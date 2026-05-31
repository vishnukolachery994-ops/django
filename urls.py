from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import RegisterSerializer, VerifyOTPSerializer, LoginSerializer, UserSerializer
from .models import OTP, AuthToken
from .utils import send_otp_email, create_auth_token, set_auth_cookie, delete_auth_cookie

User = get_user_model()


class RegisterView(APIView):
    """
    POST /api/register/
    Accepts email + password.
    Creates an unverified user and sends OTP to email.
    Permission: AllowAny — no login required to register.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Creates an unverified user and sends OTP to the provided email.",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('OTP sent to email'),
            400: openapi.Response('Validation error'),
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        # is_valid() runs all field validations and custom validate_* methods
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Create user with is_verified=False until OTP is confirmed
        user = User.objects.create_user(email=email, password=password)

        # Send OTP email (prints to terminal in development)
        send_otp_email(user)

        return Response(
            {'message': 'Registration successful. Please verify your email with the OTP sent.'},
            status=status.HTTP_201_CREATED
        )


class VerifyOTPView(APIView):
    """
    POST /api/register/verify/
    Accepts email + 6-digit OTP.
    Marks the user as verified if OTP is valid and not expired.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify OTP for registration",
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response('Email verified successfully'),
            400: openapi.Response('Invalid or expired OTP'),
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code  = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Find the latest unused OTP for this user
        try:
            otp = OTP.objects.filter(user=user, code=code, is_used=False).latest('created_at')
        except OTP.DoesNotExist:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({'error': 'OTP has expired. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as used and verify the user
        otp.is_used = True
        otp.save()
        user.is_verified = True
        user.save()

        return Response({'message': 'Email verified successfully. You can now log in.'}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    POST /api/login/
    Accepts email + password.
    On success: creates auth token and sets it as an HttpOnly cookie.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Login user",
        operation_description="Authenticates user and sets auth_token in HttpOnly cookie.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response('Login successful, cookie set'),
            400: openapi.Response('Invalid credentials'),
            403: openapi.Response('Email not verified'),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Manually look up user and check password
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_verified:
            return Response({'error': 'Please verify your email before logging in.'}, status=status.HTTP_403_FORBIDDEN)

        # Create a new auth token and set it as a cookie
        token = create_auth_token(user)

        response = Response(
            {'message': 'Login successful.', 'user': UserSerializer(user).data},
            status=status.HTTP_200_OK
        )

        # THIS is how we set the HttpOnly cookie
        set_auth_cookie(response, token.key)

        return response


class MeView(APIView):
    """
    GET /api/me/
    Returns the logged-in user's details.
    Protected: only works if auth_token cookie is valid.
    """
    permission_classes = [IsAuthenticated]  # CookieAuthentication handles this

    @swagger_auto_schema(
        operation_summary="Get current user details",
        operation_description="Returns details of the authenticated user. Requires auth_token cookie.",
        responses={
            200: UserSerializer,
            401: openapi.Response('Not authenticated'),
        }
    )
    def get(self, request):
        # request.user is set by CookieAuthentication.authenticate()
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/logout/
    Deletes the auth_token from the database and clears the cookie.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Logout user",
        operation_description="Clears auth_token cookie and invalidates the token.",
        responses={
            200: openapi.Response('Logout successful'),
        }
    )
    def post(self, request):
        # Delete token from database so it can't be reused
        AuthToken.objects.filter(user=request.user).delete()

        response = Response({'message': 'Logout successful.'}, status=status.HTTP_200_OK)

        # Clear the cookie from browser
        delete_auth_cookie(response)

        return response
