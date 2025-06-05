from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class ElAfmRecognizer(PatternRecognizer):
    """
    Recognizes Greek Tax Registration Number (Α.Φ.Μ. / ΑΦΜ) using regex patterns.

    The patterns look for variations of "Α.Φ.Μ.", "ΑΦΜ", or "Αριθμός Φορολογικού Μητρώου"
    followed by 9 digits.
    """

    # Variations of the prefix text
    # Handles "Α.Φ.Μ." with optional dots and spaces, "ΑΦΜ", or "Αριθμός Φορολογικού Μητρώου"
    _PREFIX_VARIATIONS = (
        r"(?:[Αα]ριθμός?\sΦορολογικού\sΜητρώου|Α\.?\s*Φ\.?\s*Μ\.?|ΑΦΜ(?:\s*:)?)"
    )
    PATTERNS = [
        Pattern(
            "AFM (Α.Φ.Μ./ΑΦΜ/Αριθμός Φορολογικού Μητρώου) followed by 9 digits",
            rf"(?<=\b(?:{_PREFIX_VARIATIONS})\s+)(\d{{9}})\b",
            0.9,  # High confidence due to specific pattern and length
        ),
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "el",
        supported_entity: str = "AFM",
    ):
        """
        Initialize ElAfmRecognizer.

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