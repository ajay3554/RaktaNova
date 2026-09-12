import re
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator, ValidationError


PERSON_NAME_PATTERN = re.compile(r"^[A-Za-z]+(?: [A-Za-z]+)*$")
INDIAN_MOBILE_PATTERN = re.compile(r"^[6-9]\d{9}$")
LANDLINE_FORMAT_PATTERN = re.compile(r"^\+?[0-9][0-9 ()-]*[0-9]$")
PLAIN_TEXT_PATTERN = re.compile(r"[<>]")

VALID_BLOOD_GROUPS = {
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
}

NAME_ERROR = "Name can contain letters and spaces only."
MOBILE_ERROR = "Enter a valid 10-digit Indian mobile number."
HOSPITAL_NAME_ERROR = "Hospital name must be text only."
LANDLINE_ERROR = "Enter a valid landline number."
BLOOD_GROUPS_ERROR = "Enter valid blood groups separated by commas."
AGE_ERROR = "Age must be between 18 and 60."
DUPLICATE_MOBILE_ERROR = "This mobile number is already registered."


def first_validation_message(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid input"

    message = errors[0].get("msg", "Invalid input")
    if message.startswith("Value error, "):
        return message[len("Value error, "):]
    return message


def validate_person_name(value: Any) -> str:
    if value is None:
        raise ValueError(NAME_ERROR)

    name = str(value).strip()
    if not PERSON_NAME_PATTERN.fullmatch(name):
        raise ValueError(NAME_ERROR)

    return name


def validate_indian_mobile(value: Any) -> str:
    if value is None:
        raise ValueError(MOBILE_ERROR)

    phone = str(value).strip()
    if not INDIAN_MOBILE_PATTERN.fullmatch(phone):
        raise ValueError(MOBILE_ERROR)

    return phone


def validate_hospital_name(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(HOSPITAL_NAME_ERROR)

    name = value.strip()
    if (
        not name
        or not re.search(r"[A-Za-z]", name)
        or PLAIN_TEXT_PATTERN.search(name)
    ):
        raise ValueError(HOSPITAL_NAME_ERROR)

    return name


def validate_landline_phone(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(LANDLINE_ERROR)

    phone = value.strip()
    digits = re.sub(r"\D", "", phone)
    is_indian_mobile = (
        len(digits) == 10
        and digits[0] in "6789"
    ) or (
        len(digits) == 12
        and digits.startswith("91")
        and digits[2] in "6789"
    )
    if (
        not LANDLINE_FORMAT_PATTERN.fullmatch(phone)
        or not 7 <= len(digits) <= 15
        or is_indian_mobile
    ):
        raise ValueError(LANDLINE_ERROR)

    return phone


def validate_optional_personal_phone(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None

    return validate_indian_mobile(value)


def validate_blood_groups(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(BLOOD_GROUPS_ERROR)

    groups = [group.strip().upper() for group in value.split(",")]
    if (
        not groups
        or any(group not in VALID_BLOOD_GROUPS for group in groups)
        or len(set(groups)) != len(groups)
    ):
        raise ValueError(BLOOD_GROUPS_ERROR)

    return ", ".join(groups)


def validate_donor_age(value: Any) -> int:
    if value is None or value == "":
        raise ValueError(AGE_ERROR)

    if isinstance(value, bool):
        raise ValueError(AGE_ERROR)

    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(AGE_ERROR)
        value = int(value)

    if isinstance(value, str):
        text = value.strip()
        if not re.fullmatch(r"[0-9]+", text):
            raise ValueError(AGE_ERROR)
        value = int(text)

    if isinstance(value, int):
        if value < 18 or value > 60:
            raise ValueError(AGE_ERROR)
        return value

    raise ValueError(AGE_ERROR)


def sanitize_plain_text(value: Any, required_message: str) -> str:
    if value is None:
        raise ValueError(required_message)

    text = str(value).strip()
    if not text:
        raise ValueError(required_message)

    if PLAIN_TEXT_PATTERN.search(text):
        raise ValueError(required_message)

    return text


class DonorRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    age: int
    blood_group: str
    phone: str
    password: str
    city: str
    available: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("name", mode="before")
    @classmethod
    def check_name(cls, value: Any) -> str:
        return validate_person_name(value)

    @field_validator("age", mode="before")
    @classmethod
    def check_age(cls, value: Any) -> int:
        return validate_donor_age(value)

    @field_validator("phone", mode="before")
    @classmethod
    def check_phone(cls, value: Any) -> str:
        return validate_indian_mobile(value)

    @field_validator("blood_group", mode="before")
    @classmethod
    def check_blood_group(cls, value: Any) -> str:
        group = sanitize_plain_text(value, "Blood group is required")
        if group not in VALID_BLOOD_GROUPS:
            raise ValueError("Invalid blood group")
        return group

    @field_validator("password", mode="before")
    @classmethod
    def check_password(cls, value: Any) -> str:
        if value is None or str(value) == "":
            raise ValueError("Password is required")
        return str(value)

    @field_validator("city", mode="before")
    @classmethod
    def check_city(cls, value: Any) -> str:
        return sanitize_plain_text(value, "City is required")

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def check_optional_coordinate(cls, value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        return float(value)


class DonorLoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    phone: str
    password: str

    @field_validator("phone", mode="before")
    @classmethod
    def check_phone(cls, value: Any) -> str:
        return validate_indian_mobile(value)

    @field_validator("password", mode="before")
    @classmethod
    def check_password(cls, value: Any) -> str:
        if value is None or str(value) == "":
            raise ValueError("Phone and password are required")
        return str(value)
