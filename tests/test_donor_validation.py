import pytest
from pydantic import ValidationError

from backend.schemas import (
    AGE_ERROR,
    DonorLoginRequest,
    DonorRegisterRequest,
    MOBILE_ERROR,
    NAME_ERROR,
    validate_donor_age,
    validate_indian_mobile,
    validate_person_name,
)


VALID_DONOR = {
    "name": "Ajay Raj",
    "age": 25,
    "blood_group": "O+",
    "phone": "9876543210",
    "password": "Test@123",
    "city": "Chennai",
}


def test_valid_names():
    for name in ["Ajay", "Ajay Raj", "Rahul Kumar", "Arun"]:
        assert validate_person_name(name) == name
        assert validate_person_name("  " + name + "  ") == name


def test_invalid_names():
    for name in ["Ajay123", "Ajay@123", "Ajay_raj", "12345", "@Ajay", "Ajay!", "A123", "😀Ajay", "   ", "Ajay@Raj"]:
        with pytest.raises(ValueError, match=NAME_ERROR):
            validate_person_name(name)


def test_valid_mobiles():
    for phone in ["9876543210", "9123456789", "8123456789", "7012345678"]:
        assert validate_indian_mobile(phone) == phone


def test_invalid_mobiles():
    for phone in [
        "987654321",
        "98765432101",
        "1234567890",
        "5123456789",
        "98765abc10",
        "98765 43210",
        "+919876543210",
        "00919876543210",
        "98765-43210",
    ]:
        with pytest.raises(ValueError, match=MOBILE_ERROR):
            validate_indian_mobile(phone)


def test_valid_ages():
    for age in [18, 25, 35, 50, 60, "18", "60"]:
        assert validate_donor_age(age) in (18, 25, 35, 50, 60)


def test_invalid_ages():
    for age in [17, 61, 100, 0, -5, -1, 18.5, "abc", "", None]:
        with pytest.raises(ValueError, match=AGE_ERROR):
            validate_donor_age(age)


def test_register_model_accepts_valid_payload():
    payload = DonorRegisterRequest.model_validate(VALID_DONOR)
    assert payload.phone == "9876543210"
    assert payload.age == 25
    assert payload.name == "Ajay Raj"


def test_register_model_rejects_invalid_fields():
    with pytest.raises(ValidationError):
        DonorRegisterRequest.model_validate({**VALID_DONOR, "phone": "+919876543210"})

    with pytest.raises(ValidationError):
        DonorRegisterRequest.model_validate({**VALID_DONOR, "name": "Ajay123"})

    with pytest.raises(ValidationError):
        DonorRegisterRequest.model_validate({**VALID_DONOR, "age": 17})


def test_login_model_validates_mobile():
    payload = DonorLoginRequest.model_validate({
        "phone": "9876543210",
        "password": "secret",
    })
    assert payload.phone == "9876543210"

    with pytest.raises(ValidationError):
        DonorLoginRequest.model_validate({
            "phone": "1234567890",
            "password": "secret",
        })
