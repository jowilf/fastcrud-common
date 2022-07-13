from typing import Any, Callable, Iterable

from phonenumbers import NumberParseException, is_valid_number, parse
from pydantic.validators import str_validator


class PhoneNumber(str):
    """
    Phone Number
    """

    @classmethod
    def __get_validators__(cls) -> Iterable[Callable[..., Any]]:
        yield str_validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            type="string",
            format="phone",
            example="+22990988998",
        )

    @classmethod
    def validate(cls, v: str):
        if v is None:
            return v
        try:
            if not v.startswith("+"):
                v = f"+{v}"
            n = parse(f"{v}")
            if not is_valid_number(n):
                raise ValueError("Please provide a valid mobile phone number")
        except NumberParseException as e:
            raise ValueError("Please provide a valid mobile phone number") from e
        return v  # format_number(n, PhoneNumberFormat.INTERNATIONAL)
