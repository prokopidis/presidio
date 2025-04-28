from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import StanzaNlpEngine
from presidio_analyzer.predefined_recognizers import EmailRecognizer, PhoneRecognizer, CreditCardRecognizer, IbanRecognizer
from presidio_anonymizer import AnonymizerEngine

from presidio_anonymizer.entities import OperatorConfig
from presidio_anonymizer.operators import OperatorsFactory
from ilsp_athenarc_asep_anonymizer.custom_replace import CustomReplace
from ilsp_athenarc_asep_anonymizer.utils import match_entities

import regex as re
import argparse
import logging
import json
NL = "\n"

logging.basicConfig(level=logging.INFO, encoding='utf-8', format='%(asctime)s,%(msecs)03d %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]', datefmt='%Y-%m-%d:%H:%M:%S')


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
        self.analyzer.registry.add_recognizer(EmailRecognizer(supported_language="el"))
        self.analyzer.registry.add_recognizer(PhoneRecognizer(supported_language="el"))
        self.analyzer.registry.add_recognizer(CreditCardRecognizer(supported_language="el"))
        self.analyzer.registry.add_recognizer(IbanRecognizer(supported_language="el"))

        self.analyzer.log_decision_process = False

        self.operators={"PERSON": OperatorConfig("replace")}           
        self.anonymizer_engine = AnonymizerEngine()
        self.anonymizer_engine.add_anonymizer(CustomReplace)

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
        logging.info(f"Analyzer results: {analyzer_results}")
        # Check if the text is empty or contains only whitespace
        anonymization_results = self.anonymizer_engine.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=  {
                        "DATE_TIME": OperatorConfig("keep"),
                        "ORGANIZATION": OperatorConfig("keep"),
                        "ORG": OperatorConfig("keep"),
                        "PERSON": OperatorConfig("custom_replace"),
                        "LOCATION": OperatorConfig("custom_replace"),
                        "DEFAULT": OperatorConfig("keep"),
            },
        )
        analyzer_results = sorted(analyzer_results, key=lambda x: (x.start, x.end))
        logging.debug(f"Analyzer results: {analyzer_results}")        
        anonymization_results.items = sorted(anonymization_results.items, key=lambda x: (x.start, x.end))

        anonymization_results_dict = dict()
        anonymization_results_dict["full_text"] = text
        anonymization_results_dict["masked"] = anonymization_results.text
        anonymization_results_dict["spans"] = list()


        for span in anonymization_results.items:
            if span.operator == "keep":
                continue
            span_dict = dict()
            span_dict["entity_type"] = span.entity_type
            span_dict["entity_value"] = anonymization_results.text[span.start:span.end]
            span_dict["start"] = span.start
            span_dict["end"] = span.end
            span_dict["operator"] = span.operator
            anonymization_results_dict["spans"].append(span_dict)

        anonymization_results_dict["spans"] = match_entities(text, anonymization_results.text, anonymization_results_dict["spans"])
        for span in anonymization_results_dict["spans"]:
            #span['entity_value'] = span["orig_text"]
            #del span["orig_text"]
            del span["start"]
            del span["end"]

        
        return anonymization_results_dict

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

    parser = argparse.ArgumentParser(
        description="Anonymize PII in Greek text.",
        formatter_class=argparse.RawTextHelpFormatter, # Allows embedding newlines in help
        epilog="""Example Usage:
  # Anonymize text from a file and print to console
  python pii_anonymizer.py --input-file input.txt

  # Anonymize text provided directly and save to a file
  python pii_anonymizer.py --text "Ο Γιάννης Παπαδόπουλος μένει στην Αθήνα.\nΤηλέφωνο 6936745127.\nEmail: gp@ex.com" --output-file output.json

  # Anonymize with debug logging
  python pii_anonymizer.py --input-file input.txt --log-level DEBUG
"""
    )

    # Input group (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--text",
        metavar="\"TEXT\"",
        help="Direct text input to anonymize."
    )
    input_group.add_argument(
        "--input-file",
        metavar="FILE_PATH",
        type=argparse.FileType('r', encoding='utf-8'),
        help="Path to the input file (UTF-8 encoded)."
    )

    # Output file argument
    parser.add_argument(
        "--output-file",
        metavar="FILE_PATH",
        type=argparse.FileType('w', encoding='utf-8'),
        default=None, # Default is None, indicating stdout
        help="Path to the output file to save results (JSON format, UTF-8 encoded).\nIf not provided, results are printed to standard output."
    )

    # Entities argument
    # parser.add_argument(
    #     "--entities",
    #     metavar="ENTITY_TYPE",
    #     nargs='+', # Accepts one or more arguments
    #     default=None, # Default is None, meaning use all configured recognizers
    #     help="List of specific entity types to detect (e.g., PERSON EMAIL PHONE_NUMBER).\nIf not provided, all supported/configured entities are detected."
    # )

    # Log level argument
    parser.add_argument(
        "--log-level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help="Set the logging level (default: INFO)."
    )

    args = parser.parse_args()

    # --- Configure Logging ---
    log_level = getattr(logging, args.log_level.upper())
    # Update logging config based on parsed level
    # Keep existing format but set the level dynamically
    logging.basicConfig(
        level=log_level,
        encoding='utf-8',
        format='%(asctime)s,%(msecs)03d %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]',
        datefmt='%Y-%m-%d:%H:%M:%S',
        force=True # Override potential default config
    )
    logging.info(f"Logging level set to {args.log_level}")


    # --- Determine Input Text ---
    if args.text:
        input_text = args.text
        logging.info("Reading text from command line argument.")
    else: # args.input_file must be set because the group is required
        logging.info(f"Reading text from input file: {args.input_file.name}")
        # File is already opened by argparse.FileType
        input_text = args.input_file.read()
        args.input_file.close() # Close the file

    # --- Initialize Anonymizer ---
    logging.info("Initializing PII Anonymizer...")
    anonymizer = PiiAnonymizer()
    logging.info("Anonymizer initialized.")

    # --- Perform Anonymization ---
    logging.info("Starting anonymization process...")
    # if args.entities:
    #     logging.info(f"Anonymizing only entities: {', '.join(args.entities)}")
    # else:
    #     logging.info("Anonymizing all detected entities.")

    # anonymization_results = anonymizer.anonymize(input_text, entities=args.entities)
    anonymization_results = anonymizer.anonymize(input_text)
    logging.info("Anonymization complete.")

    # --- Prepare Output ---
    # Convert results to JSON string
    
    json_output = json.dumps(anonymization_results, indent=4, ensure_ascii=False)

    # # --- Write Output ---
    if args.output_file:
        logging.info(f"Writing results to output file: {args.output_file.name}")
        args.output_file.write(json_output + NL) # Add a newline at the end of the file
        args.output_file.close() # Close the output file
        logging.info("Results written successfully.")
    else:
        logging.info("Writing results to standard output.")
        print(json_output)

    # logging.info("Script finished.")