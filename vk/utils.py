from typing import Any, Optional, TypeVar

_T = TypeVar("_T")


def int_to_bool_optional(value: Optional[int]) -> Optional[bool]:
    if value is None:
        return value

    return int_to_bool(value)


def int_to_bool(value: int) -> bool:
    if value not in [0, 1]:
        raise ValueError(f"Value {value} can't be converted to bool")

    return bool(value)


def validate_type(to_validate: _T, desired_type: Any) -> _T:
    if not isinstance(to_validate, desired_type):
        raise ValueError(
            f"Incorrect type {type(to_validate)}, should be {desired_type}"
        )

    return to_validate


def validate_type_optional(to_validate: _T, desired_type: Any) -> _T:
    if to_validate is None:
        return to_validate

    return validate_type(to_validate, desired_type)
