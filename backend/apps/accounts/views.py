"""
Accounts views — authentication endpoints.
Full implementation in Phase 2.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class LogoutView(APIView):
    def post(self, request):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)
