import argparse
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import StanzaNlpEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PiiAnonymizer:
    SUPPORTED_LANG = ["el"]

    def __init__(self):
        """This function initializes the PiiAnonymizer class. It sets up the NLP engine and the anonymizer engine.
        It also sets up the recognizer registry and adds the phone recognizer to it. The phone recognizer is used to recognize phone numbers in the text.
        The NLP engine is used to analyze the text and extract PII entities. The anonymizer engine is used to anonymize the text by replacing the PII entities with fake data.
        """
        models = [{"lang_code": "el", "model_name": "el"}]
        logger.info("Initializing Stanza NLP engine for Greek language.")
        stanza_el_engine = StanzaNlpEngine(models = models, 
                                           download_if_missing=False # Remove this once we have a model for el in the main stanza repo
                                           )
        self.analyzer = AnalyzerEngine(nlp_engine = stanza_el_engine)       
        self.operators={"PERSON": OperatorConfig("replace")}           
        self.anonymizer_engine = AnonymizerEngine()


    def analyze(self, text, language="el", entities=None, return_decision_process=True):
        return self.analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
            return_decision_process=return_decision_process,
        )


    def anonymize(self, text, entities=None, analyzer_results=None, operators=None):
        """This function anonymizes the text using the analyzer engine and the anonymizer engine. 

        Args:
            text (_type_): _description_
            analyzer_results (_type_, optional): _description_. Defaults to None.
            operators (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        if not operators:
            operators = self.operators
       
        if analyzer_results is None:
            analyzer_results = self.analyze(text, entities=entities)
        anonymized_text = self.anonymizer_engine.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operators
        )
        
        
        return anonymized_text




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anonymize PII in text.")
    text = "Πειράματα διεξάγουν Έλληνες ερευνητές. Ο Μπαράκ Ομπάμα γεννήθηκε στη Χαβάη.  Εκλέχθηκε πρόεδρος το 2008."
    anonymizer = PiiAnonymizer()
    anonymizer_results = anonymizer.anonymize(text)
    logger.info(type(anonymizer_results))
