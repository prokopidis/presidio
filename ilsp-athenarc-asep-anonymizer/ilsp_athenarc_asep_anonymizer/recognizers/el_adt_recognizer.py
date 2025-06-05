from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class ElAdtRecognizer(PatternRecognizer):
    """
    Recognizes Greek Police ID (Α.Δ.Τ. / ΑΔΤ) using regex patterns.

    The patterns look for variations of "Α.Δ.Τ.", "ΑΔΤ", or "Αρ. Δελ. Ταυτ."
    followed by two Greek or Latin letters and 6 digits.
    """

    # Greek and English letters for the ID prefix
    _LETTER_PREFIX = r"[Α-ΩA-Z]"

    # Variations of the prefix text
    # _PREFIX_VARIATIONS = r"(?:Α\.?\s*Δ\.?\s*Τ\.?|ΑΔΤ|Αρ\.?\s*Δελ\.?\s*Ταυτ\.?)"
    _PREFIX_VARIATIONS = (
        r"(?:Α\.?\s*Δ\.?\s*Τ\.?|ΑΔΤ|"
        r"Αρ(?:ισμός?|\.)\s*Δελ(?:τίου|\.)\s*Ταυτ(?:ότητας|\.)|"
        r"Δελτίο\s*Ταυτότητας|"
        r"(?:(?:Παλιός|Σωστός)\s)?[Αα]ριθμός?\sΤαυτότητας(?:\s*:)?"
        r")"
    )

    PATTERNS = [
            Pattern(
                "ADT (Α.Δ.Τ./ΑΔΤ/Αρ. Δελ. Ταυτ.) followed by letter and 6 digits",
                rf"(?<=\b(?:{_PREFIX_VARIATIONS})\s+)({_LETTER_PREFIX}{{2}}\s*\d{{6}})\b",
                0.9,  # High confidence due to specific pattern
            ),
        ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "el",
        supported_entity: str = "ADT",
    ):
        """
        Initialize ElAdtRecognizer.

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
