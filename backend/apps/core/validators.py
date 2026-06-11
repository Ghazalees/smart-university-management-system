from rest_framework import serializers


def validate_non_empty_string(value, field_name="Value"):
    if not isinstance(value, str):
        raise serializers.ValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise serializers.ValidationError(f"{field_name} cannot be empty.")

    return cleaned


def validate_max_length(value, max_length, field_name="Value"):
    if isinstance(value, str) and len(value) > max_length:
        raise serializers.ValidationError(
            f"{field_name} cannot be longer than {max_length} characters."
        )

    return value


def normalize_keyword(value):
    if value is None:
        return ""

    if not isinstance(value, str):
        raise serializers.ValidationError("Search value must be a string.")

    return value.strip()