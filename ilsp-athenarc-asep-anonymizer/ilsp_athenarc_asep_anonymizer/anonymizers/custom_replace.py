"""Replaces the PII text entity with a new string. Returns spans including the replacement the entities and their offsets in the original string."""

from typing import Dict

from presidio_anonymizer.operators import Operator, OperatorType
from presidio_anonymizer.services.validators import validate_type


class CustomReplace(Operator):
    """Receives new text to replace old PII text entity with."""

    NEW_VALUE = "new_value"
    PRE_STRING ="{{"
    POST_STRING = "}}"
    def operate(self, text: str = None, params: Dict = None) -> str:
        """:return: new_value."""
        new_val = params.get(self.NEW_VALUE)
        if not new_val:
            return self.PRE_STRING + f"{params.get('entity_type')}" + self.POST_STRING
        return new_val

    def validate(self, params: Dict = None) -> None:
        """Validate the new value is string."""
        validate_type(params.get(self.NEW_VALUE), self.NEW_VALUE, str)
        pass

    def operator_name(self) -> str:
        """Return operator name."""
        return "custom_replace"

    def operator_type(self) -> OperatorType:
        """Return operator type."""
        return OperatorType.Anonymize
