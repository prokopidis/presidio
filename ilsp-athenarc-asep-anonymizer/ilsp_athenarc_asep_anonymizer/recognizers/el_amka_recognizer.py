from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class ElAmkaRecognizer(PatternRecognizer):
    """
    Recognizes Greek Social Security Number (Α.Μ.Κ.Α. / ΑΜΚΑ) using regex patterns.

    The patterns look for variations of "Α.Μ.Κ.Α." or "ΑΜΚΑ" followed by 11 digits.
    """

    # Variations of the prefix text
    # Handles "Α.Μ.Κ.Α." with optional dots and spaces, or "ΑΜΚΑ"
    _PREFIX_VARIATIONS = (
        r"(?:Α\.?\s*Μ\.?\s*Κ\.?\s*Α\.?|ΑΜΚΑ(?:\s*:)?)"
    )
    PATTERNS = [
        Pattern(
            "AMKA (Α.Μ.Κ.Α./ΑΜΚΑ) followed by 11 digits",
            rf"(?<=\b(?:{_PREFIX_VARIATIONS})\s+)(\d{{11}})\b",
            0.9,  # High confidence due to specific pattern and length
        ),
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "el",
        supported_entity: str = "AMKA",
    ):
        """
        Initialize ElAmkaRecognizer.

        :param patterns: List of patterns to use.
        :param context: List of context words.
        :param supported_language: Language this recognizer supports.
        :param supported_entity: Entity type this recognizer supports.
        """
        patterns = patterns if patterns else self.PATTERNS
        super().__init__(
            patterns=patterns, # Corrected order for Presidio V2.2.33+
            context=context,
            supported_language=supported_language,
            supported_entity=supported_entity,
        )