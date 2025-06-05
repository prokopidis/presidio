from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult, AnalysisExplanation




class ElAmRecognizer(PatternRecognizer):
    """
    Recognizes Greek Registration Number (Α.Μ. / ΑΜ) using regex patterns.

    The patterns look for variations of "Α.Μ.", "ΑΜ", or "Αριθμός μητρώου"
    followed by 8 digits.
    """

    # Variations of the prefix text
    _PREFIX_VARIATIONS = (
        r"(?:Α\.?\s*Μ\.?|ΑΜ|[Αα]ριθμός\sμητρώου(?:\sΥποψηφίου)?(?:\s*:)?)"
    )    
    PATTERNS = [
        Pattern(
            "AM (Α.Μ./ΑΜ/Αριθμός μητρώου) followed by more than 4 digits",
            rf"(?<=\b(?:{_PREFIX_VARIATIONS})\s+)(\d{{4,}})\b",
            0.8,  # Medium-high confidence
        ),
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "el",
        supported_entity: str = "AM",
    ):
        """
        Initialize ElAΜRecognizer.

        :param patterns: List of patterns to use.
        :param context: List of context words.
        :param supported_language: Language this recognizer supports.
        :param supported_entity: Entity type this recognizer supports.
        """
        patterns = patterns if patterns else self.PATTERNS
        super().__init__(
            patterns=patterns,
            context=context,
            supported_language=supported_language,
            supported_entity=supported_entity,
        )

    def _get_recognizer_result(self, match, text, region, nlp_artifacts):
        result = RecognizerResult(
            entity_type="AM",
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
            recognizer=ElAmRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation=f"Recognized as a Greek AM number, "
            f"using ElAMRecognizer.",
        )
