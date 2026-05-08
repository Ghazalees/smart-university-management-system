from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Validate login input for the authentication API."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    """Represent an empty logout request body for API documentation and consistency."""

    pass
