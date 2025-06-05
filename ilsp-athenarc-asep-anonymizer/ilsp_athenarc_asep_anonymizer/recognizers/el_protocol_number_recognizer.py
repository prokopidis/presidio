from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class ElProtocolNumberRecognizer(PatternRecognizer):
    """
    Recognizes Greek Protocol Number (Αριθμός Πρωτοκόλλου / Α.Π. / ΑΠ) using regex patterns.
    
    The patterns look for variations of "Αριθμός Πρωτοκόλλου", "αριθμό πρωτοκόλλου", "Α.Π.", "ΑΠ", 
    "υπ αρίθμου", or "υπ' αριθμ." followed by numbers separated by slashes.
    Examples: 123/456, 123/456/2025, 20400/21.03.2025, 41447-18/11/2024.
    """

    # Variations of the prefix text
    # Handles "Αριθμός Πρωτοκόλλου", "Α.Π." (with optional dots and spaces), or "ΑΠ"
    _PREFIX_VARIATIONS = (
        r"(?:[Αα]ριθμός\sΠρωτοκόλλου|Α\.?\s*Π\.?|ΑΠ|υπ\sαρίθμου|υπ'\s*αριθμ\.?)"
    )

    # Pattern for the number sequence (e.g., 84/1190 or 84/1190/2025)
    # It matches one or more digits, followed by a slash and more digits,
    # and optionally another slash followed by more digits (often the year).
    _NUMBER_PATTERN = r"[\d.-]+/[\d.-]+(?:/[\d.-]+)?"

    PATTERNS = [
        Pattern(
            "PROTOCOL_NUMBER (Αριθμός Πρωτοκόλλου/Α.Π./ΑΠ) followed by number/number(/number)",
            rf"(?<=\b(?:{_PREFIX_VARIATIONS})\s+)({_NUMBER_PATTERN})\b",
            0.8,  # Medium-high confidence; specific prefix helps
        )
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "el",
        supported_entity: str = "PROTOCOL_NUMBER",
    ):
        """
        Initialize ElProtocolNumberRecognizer.

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