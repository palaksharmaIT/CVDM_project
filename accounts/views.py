from django.contrib.auth import authenticate, get_user_model
from django.conf import settings as dj_settings
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView



from .serializers import RegisterSerializer, UserSerializer
from .models import EmailVerification


User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        verification = EmailVerification.objects.create(user=user)

        verify_url = request.build_absolute_uri(
            reverse("verify-email", args=[verification.token])
        )

        send_mail(
            subject="Verify your CVDM account",
            message=(
                f"Hi {user.username},\n\n"
                f"Click the link below to verify your email and "
                f"activate your CVDM account:\n\n{verify_url}\n\n"
                f"If you didn't request this, ignore this email."
            ),
            from_email=dj_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {
                "detail": (
                    "Registration successful. Check your email to "
                    "verify your account before logging in."
                ),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()

        return Response(
            {"detail": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)