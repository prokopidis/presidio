from re import M
from typing import List, Optional
from flair.data import Sentence, Token
from flair.models import SequenceTagger
from huggingface_hub import hf_hub_download

from presidio_analyzer import (
    AnalysisExplanation,
    EntityRecognizer,
    LocalRecognizer,
    RecognizerResult,
)
from presidio_analyzer.nlp_engine import NlpArtifacts
from ilsp_athenarc_asep_anonymizer.utils import find_longest_pattern_matches
import logging



class ElAddressRecognizer(LocalRecognizer):

    SCORE = 0.8
    CONTEXT = ["οδός", "λεωφόρος", "πλατεία", "οδ", "πλ", "οδός", "λεωφόρος", "πλατεία",    
                "οδ.", "λεωφ.", "πλ.", "οδ:", "λεωφ:", "πλ:", "οδ", "λεωφ", "πλ",
                "street", "avenue", "square", "st", "ave", "sq", "str", "av", "sq",
                # Add more context words as needed
                ]

    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "el",
    ):
        context = context if context else self.CONTEXT

        REPO_ID = "ilsp/justice"
        MODEL_PATH = "decisions-ner-model.pt"

        model_path = hf_hub_download(repo_id=REPO_ID, filename=MODEL_PATH)       
        self.model = SequenceTagger.load(model_path)        
        super().__init__(
            supported_entities=self.get_supported_entities(),
            supported_language=supported_language,
            context=context,
        )
        logging.info(f"Loaded address model from {REPO_ID} {MODEL_PATH}") 

    def load(self) -> None:  # noqa D102
        pass

    def get_supported_entities(self):  # noqa D102
        return ["ADDRESS"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        results = []
        sentence = Sentence([Token(t) for t in text.split()]) # or use a sentence splitter
        self.model.predict(sentence)
        for span in sentence.get_spans("ner"):
            if span.tag == "FAC":
                start = span.start_position
                end = span.end_position
                results.append(
                    RecognizerResult(
                        entity_type="ADDRESS",
                        start=start,
                        end=end,
                        score=self.SCORE,
                        analysis_explanation=self._get_analysis_explanation(),
                        recognition_metadata={
                            RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                            RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        },
                    )
                )
        return EntityRecognizer.remove_duplicates(results)

    def _get_recognizer_result(self, match, text, region, nlp_artifacts):
        result = RecognizerResult(
            entity_type="ADDRESS",
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

    def _get_analysis_explanation(self):
        return AnalysisExplanation(
            recognizer=ElAddressRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation=f"Recognized as a Greek address, "
            f"using ElAddressRecognizer.",
        )
