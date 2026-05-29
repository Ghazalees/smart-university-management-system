from rest_framework import serializers


def validate_non_empty_string(value, field_name="value"):
    """Normalize and validate required user-facing string inputs."""
    if value is None:
        raise serializers.ValidationError(f"{field_name} is required.")
    cleaned = str(value).strip()
    if not cleaned:
        raise serializers.ValidationError(f"{field_name} cannot be empty.")
    return cleaned


def validate_max_length(value, max_length, field_name="value"):
    """Validate maximum length with a consistent error message."""
    if value and len(value) > max_length:
        raise serializers.ValidationError(
            f"{field_name} must be {max_length} characters or fewer."
        )
    return value


def normalize_keyword(value):
    """Normalize optional keyword/search query parameters."""
    if value is None:
        return ""
    return str(value).strip()
