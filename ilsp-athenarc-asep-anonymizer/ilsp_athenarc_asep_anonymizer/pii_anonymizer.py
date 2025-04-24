from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import StanzaNlpEngine
from presidio_anonymizer import AnonymizerEngine, DeanonymizeEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_anonymizer.operators import Operator, OperatorType

import argparse
import logging
import regex as re
import json
from typing import Dict

NL = "\n"

logging.basicConfig(level=logging.INFO,encoding='utf-8', format='%(asctime)s,%(msecs)03d %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]' ,    datefmt='%Y-%m-%d:%H:%M:%S')


def remove_indices_from_labels(text):
    """
    Removes indices in labels like {{LABEL_INDEX}} with {{LABEL}} using regex.

    Args:
        text: The input string containing labels with indices.

    Returns:
        The string with indices removed from the labels.
    """
    return re.sub(r"\{\{([A-Z_]+)_\d+\}\}", r"{{\1}}", text)

def merge_results(anonymization_results, deanonymization_results):
    """
    Merges the results of anonymization and deanonymization.

    Args:
        anonymization_results: The results of anonymization.
        deanonymization_results: The results of deanonymization.

    Returns:
        A dictionary containing the merged results.
    """

    merged_results = dict()
    merged_results["text"] = deanonymization_results.text
    merged_results["masked"] = remove_indices_from_labels(anonymization_results.text)
    merged_results["spans"] = list()
    for span_tuple in zip(anonymization_results.items, deanonymization_results.items):
        span = span_tuple[0]
        deanon_span = span_tuple[1]
        span_dict = dict()
        span_dict["entity_type"] = span.entity_type
        span_dict["entity_value"] = deanon_span.text
        span_dict["masked_entity_value"] = remove_indices_from_labels(span.text)
        span_dict["start_position"] = span.start
        span_dict["end_position"] = span.end
        merged_results["spans"].append(span_dict)
    return merged_results

class InstanceCounterAnonymizer(Operator):
    """
    Anonymizer which replaces the entity value
    with an instance counter per entity.
    """

    REPLACING_FORMAT = "<{entity_type}_{index}>"
    REPLACING_FORMAT = "{{{{{entity_type}_{index}}}}}"


    def operate(self, text: str, params: Dict = None) -> str:
        """Anonymize the input text."""

        entity_type: str = params["entity_type"]

        # entity_mapping is a dict of dicts containing mappings per entity type
        entity_mapping: Dict[Dict:str] = params["entity_mapping"]

        entity_mapping_for_type = entity_mapping.get(entity_type)
        if not entity_mapping_for_type:
            new_text = self.REPLACING_FORMAT.format(
                entity_type=entity_type, index=0
            )
            entity_mapping[entity_type] = {}

        else:
            if text in entity_mapping_for_type:
                return entity_mapping_for_type[text]

            previous_index = self._get_last_index(entity_mapping_for_type)
            new_text = self.REPLACING_FORMAT.format(
                entity_type=entity_type, index=previous_index + 1
            )

        entity_mapping[entity_type][text] = new_text
        return new_text

    @staticmethod
    def _get_last_index(entity_mapping_for_type: Dict) -> int:
        """Get the last index for a given entity type."""

        def get_index(value: str) -> int:
            return int(value.split("_")[-1][:-1])

        indices = [get_index(v) for v in entity_mapping_for_type.values()]
        return max(indices)

    def validate(self, params: Dict = None) -> None:
        """Validate operator parameters."""

        if "entity_mapping" not in params:
            raise ValueError("An input Dict called `entity_mapping` is required.")
        if "entity_type" not in params:
            raise ValueError("An entity_type param is required.")

    def operator_name(self) -> str:
        return "entity_counter"

    def operator_type(self) -> OperatorType:
        return OperatorType.Anonymize

class InstanceCounterDeanonymizer(Operator):
    """
    Deanonymizer which replaces the unique identifier 
    with the original text.
    """

    def operate(self, text: str, params: Dict = None) -> str:
        """Anonymize the input text."""

        entity_type: str = params["entity_type"]

        # entity_mapping is a dict of dicts containing mappings per entity type
        entity_mapping: Dict[Dict:str] = params["entity_mapping"]

        if entity_type not in entity_mapping:
            raise ValueError(f"Entity type {entity_type} not found in entity mapping!")
        if text not in entity_mapping[entity_type].values():
            raise ValueError(f"Text {text} not found in entity mapping for entity type {entity_type}!")

        return self._find_key_by_value(entity_mapping[entity_type], text)

    @staticmethod
    def _find_key_by_value(entity_mapping, value):
        for key, val in entity_mapping.items():
            if val == value:
                return key
        return None
    
    def validate(self, params: Dict = None) -> None:
        """Validate operator parameters."""

        if "entity_mapping" not in params:
            raise ValueError("An input Dict called `entity_mapping` is required.")
        if "entity_type" not in params:
            raise ValueError("An entity_type param is required.")

    def operator_name(self) -> str:
        return "entity_counter_deanonymizer"

    def operator_type(self) -> OperatorType:
        return OperatorType.Deanonymize


class PiiAnonymizer:
    SUPPORTED_LANG = ["el"]

    def __init__(self):
        """This function initializes the PiiAnonymizer class. It sets up the NLP engine and the anonymizer engine.
        It also sets up the recognizer registry and adds the phone recognizer to it. The phone recognizer is used to recognize phone numbers in the text.
        The NLP engine is used to analyze the text and extract PII entities. The anonymizer engine is used to anonymize the text by replacing the PII entities with fake data.
        """
        models = [{"lang_code": "el", "model_name": "el"}]
        logging.info("Initializing Stanza NLP engine for Greek language.")
        stanza_el_engine = StanzaNlpEngine(models = models, 
                                           download_if_missing=False # Remove this once we have a model for el in the main stanza repo
                                           )
        self.analyzer = AnalyzerEngine(nlp_engine = stanza_el_engine)       
        self.operators={"PERSON": OperatorConfig("replace")}           
        self.anonymizer_engine = AnonymizerEngine()
        self.anonymizer_engine.add_anonymizer(InstanceCounterAnonymizer)
        self.deanonymizer_engine = DeanonymizeEngine()
        self.deanonymizer_engine.add_deanonymizer(InstanceCounterDeanonymizer)        


    def analyze(self, text, language="el", entities=None, return_decision_process=True):
        return self.analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
            return_decision_process=return_decision_process,
        )


    def anonymize_paragraph(self, text, entities=None, analyzer_results=None, operators=None):
        """
        Anonymize a paragraph of text.

        Args:
            text (str): The paragraph of text to anonymize.            
        """

        if not operators:
            operators = self.operators
       
        if analyzer_results is None:
            analyzer_results = self.analyze(text, entities=entities)
        # Create a mapping between entity types and counters
        entity_mapping = dict()            
        anonymization_results = self.anonymizer_engine.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=  {
                        "DEFAULT": OperatorConfig(
                                        "entity_counter", {"entity_mapping": entity_mapping}
                            ),
            }

        )

        deanonymization_results = self.deanonymizer_engine.deanonymize(
            anonymization_results.text, 
            anonymization_results.items, 
            {"DEFAULT": OperatorConfig("entity_counter_deanonymizer", 
                                    params={"entity_mapping": entity_mapping})}
        )

        merged_results = merge_results(anonymization_results=anonymization_results, deanonymization_results=deanonymization_results) # FIXME, there must be an easier way to do this

        return merged_results 



    def anonymize(self, text):
        """
        Anonymize the input text.
        Args:
            text (str): The input text to anonymize.
        Returns:
            list: A list of dictionaries containing the anonymization results for each paragraph.
        """        

        results = list()
        for paragraph in text.split(NL):
            if paragraph.strip():
                paragraph_results = self.anonymize_paragraph(paragraph)
                results.append(paragraph_results)

        return results 



if __name__ == "__main__":
    text = """Καλησπέρα σας,
   
Ονομάζομαι Γιάννης Παπαδόπουλος και είμαι προγραμματιστής. 
Πώς μπορώ να αποδείξω τις γνώσεις μου στους υπολογιστές;
Είμαι 35 ετών και μένω στην Αθήνα. 

Με εκτίμηση,
Γιάννης Παπαδόπουλος
Τηλέφωνο: 2101234567
Email: gpapadopoulos@example.com
"""

    parser = argparse.ArgumentParser(description="Anonymize PII in text.")
    # text = text + NL + "Ο Μπαράκ Ομπάμα γεννήθηκε στη Χαβάη.  Εκλέχθηκε πρόεδρος το 2008."
    anonymizer = PiiAnonymizer()    
    anonymization_results = anonymizer.anonymize(text) # FIXME, there must be an easier way to do this
    print(json.dumps(anonymization_results, indent=4, ensure_ascii=False))
