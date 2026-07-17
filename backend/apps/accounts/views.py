"""
Accounts views — JWT authentication endpoints.

Endpoints:
  POST /api/auth/register/  → creates user, returns tokens + user data
  POST /api/auth/login/     → validates credentials, returns tokens + user data
  POST /api/auth/refresh/   → handled by simplejwt TokenRefreshView (see urls.py)
  POST /api/auth/logout/    → blacklists refresh token
"""
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


def _token_pair(user) -> dict:
    """Return a dict with access/refresh tokens for a given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class RegisterView(APIView):
    """
    Register a new user and immediately return JWT tokens.
    No prior authentication required.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Envia e-mail de boas-vindas
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        username = user.username
        email = user.email

        subject = "Bem-vindo ao Projeto Orizon!"
        message = (
            f"Bem-vindo {first_name} {last_name}!\n\n"
            f"O seu usuário é: {username}\n\n"
            f"Seja bem-vindo ao nosso aplicativo Projeto Orizon.\n\n"
            "Seja muito bem-vindo. Qualquer dúvida, pode entrar em contato com: techcarlosandre@gmail.com"
        )
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        except Exception:
            # Falha silenciosamente para não travar o cadastro caso o SMTP esteja offline
            pass

        return Response(
            {
                "user": UserSerializer(user).data,
                **_token_pair(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Authenticate with username + password, return JWT tokens.
    Uses Django's authenticate() to respect is_active checks.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        from django.contrib.auth import authenticate

        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response(
                {"detail": "Informe username e password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Credenciais inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "user": UserSerializer(user).data,
                **_token_pair(user),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Blacklist the provided refresh token.
    Requires authentication (access token must be valid).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Informe o refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (TokenError, InvalidToken) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Logout realizado com sucesso."}, status=status.HTTP_200_OK)
