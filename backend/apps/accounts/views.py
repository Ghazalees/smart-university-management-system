from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.serializers import LoginSerializer
from apps.accounts.services import AuthFacade


class LoginView(APIView):
    """Handle POST /api/v1/auth/login using AuthFacade."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """Validate credentials and return a signed token when authentication succeeds."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthFacade.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not result["success"]:
            return Response(result, status=status.HTTP_401_UNAUTHORIZED)
        return Response(result, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Handle POST /api/v1/auth/logout for the token-based authentication flow."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """Return a successful logout response for the current API client."""
        return Response(AuthFacade.logout(), status=status.HTTP_200_OK)
