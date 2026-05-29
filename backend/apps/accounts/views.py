from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import BearerTokenAuthentication
from apps.accounts.serializers import LoginSerializer
from apps.accounts.services import AuthFacade, RoleDashboardStrategy
from apps.core.responses import api_error, api_success


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
            return api_error(
                message=result["message"],
                errors={"detail": result["message"]},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return api_success(message="Login successful.", data=result["data"])


class LogoutView(APIView):
    """Handle POST /api/v1/auth/logout for the token-based authentication flow."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """Return a successful logout response for the current API client."""
        result = AuthFacade.logout()
        return api_success(message=result["message"])


class CurrentUserView(APIView):
    """Handle GET /api/v1/auth/me for authenticated users."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the current user data and role-based dashboard selected by Strategy Pattern."""
        return api_success(
            message="Current user retrieved successfully.",
            data={
                "user": AuthFacade.user_payload(request.user),
                "role": request.user.primary_role(),
                "dashboard": RoleDashboardStrategy.build_dashboard(request.user),
            },
        )
