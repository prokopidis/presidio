from typing import List, Optional

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

from presidio_analyzer import (
    AnalysisExplanation,
    EntityRecognizer,
    LocalRecognizer,
    RecognizerResult,
)
from presidio_analyzer.nlp_engine import NlpArtifacts
from ilsp_athenarc_asep_anonymizer.utils import find_longest_pattern_matches
import regex as re

# Assume your compiled regex patterns are defined as provided:
#PHONE1_REGEX = re.compile(r"((\+\d{1,2}[\s-])?(?!0+\s+,?$)\d{10})")
PHONE2_REGEX = re.compile(r"((\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})")
# PHONE3_REGEX has a leading '\s' and a capturing group around the number itself
PHONE3_REGEX = re.compile(r"(\+\d{1,2}\s\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})")
PHONE_REGEX_WORD_BOUNDARY = re.compile(r"\b(?!0+\s*$)(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")

# Define a list of patterns and whether to use span(0) [whole match] or span(1) [group 1]
# based on the pattern definition and desired output span.
# PHONE3_REGEX explicitly captures the number *without* the leading space in group 1.
patterns_config = [
#    (PHONE1_REGEX, False), # False indicates use match.span() (span(0))
    #(PHONE2_REGEX, False),
    (PHONE_REGEX_WORD_BOUNDARY, False),  # False indicates use match.span(0)
    #(PHONE3_REGEX, True)  # True indicates use match.span(1) (the first group)
]

# # Example Usage with Greek text:
# text = "Παρακαλώ καλέστε στο +30 2101234567 για πληροφορίες. Έχουν επίσης αριθμό 6901234567 και 210-9876543."
# matches = find_longest_pattern_matches(text, patterns_config)
# print("Longest phone matches found:")   
# print(matches)  # Output: [(start, end), ...]
# # Example output: [(0, 15), (16, 30), (31, 45)] 

class ElPhoneRecognizer(LocalRecognizer):
    """Recognize multi-regional phone numbers.

     Using python-phonenumbers, along with fixed and regional context words.
    :param context: Base context words for enhancing the assurance scores.
    :param supported_language: Language this recognizer supports
    :param supported_regions: The regions for phone number matching and validation
    :param leniency: The strictness level of phone number formats.
    Accepts values from 0 to 3, where 0 is the lenient and 3 is the most strictest.
    """

    SCORE = 0.8
    CONTEXT = ["phone", "number", "telephone", "cell", "cellphone", "mobile", "call", 
               "τηλέφωνο", "κινητό", "τηλ", "κιν", "τηλ:", "κιν:"]
    DEFAULT_SUPPORTED_REGIONS = ("US", "UK", "DE", "FE", "IL", "IN", "CA", "BR")

    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "el",
        # For all regions, use phonenumbers.SUPPORTED_REGIONS
        supported_regions=DEFAULT_SUPPORTED_REGIONS,
        leniency: Optional[int] = 1,
    ):
        context = context if context else self.CONTEXT
        self.supported_regions = supported_regions
        self.leniency = leniency
        super().__init__(
            supported_entities=self.get_supported_entities(),
            supported_language=supported_language,
            context=context,
        )

    def load(self) -> None:  # noqa D102
        pass

    def get_supported_entities(self):  # noqa D102
        return ["PHONE_NUMBER"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """Analyzes text to detect phone numbers using python-phonenumbers.

        Iterates over entities, fetching regions, then matching regional
        phone numbers patterns against the text.
        :param text: Text to be analyzed
        :param entities: Entities this recognizer can detect
        :param nlp_artifacts: Additional metadata from the NLP engine
        :return: List of phone numbers RecognizerResults
        """
        results = []
        for region in self.supported_regions:
            continue
            for match in phonenumbers.PhoneNumberMatcher(
                text, region, leniency=self.leniency
            ):
                try:
                    parsed_number = phonenumbers.parse(text[match.start:match.end])
                    region = phonenumbers.region_code_for_number(parsed_number)
                    results += [
                    self._get_recognizer_result(match, text, region, nlp_artifacts)
                ]
                except NumberParseException:
                    results += [
                        self._get_recognizer_result(match, text, region, nlp_artifacts)
                    ]

        matches = find_longest_pattern_matches(text, patterns_config)    
        for match in matches:
            start, end = match
            # Adjust the end index to include the last character of the match
            end += 1 if patterns_config[0][1] else 0
            results.append(
                RecognizerResult(
                    entity_type="PHONE_NUMBER",
                    start=start,
                    end=end,
                    score=1.0,
                    analysis_explanation=self._get_analysis_explanation("GR"),
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                    },
                )
            )
        return EntityRecognizer.remove_duplicates(results)

    def _get_recognizer_result(self, match, text, region, nlp_artifacts):
        result = RecognizerResult(
            entity_type="PHONE_NUMBER",
            start=match.start,
            end=match.end,
            score=self.SCORE,
            analysis_explanation=self._get_analysis_explanation(region),
            recognition_metadata={
                RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
            },
        )

        return result

    def _get_analysis_explanation(self, region):
        return AnalysisExplanation(
            recognizer=ElPhoneRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation=f"Recognized as {region} region phone number, "
            f"using ElPhoneRecognizer",
        )
