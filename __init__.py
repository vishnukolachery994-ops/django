from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Validates registration input — email + password only."""
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    # write_only=True means password will never appear in response output

    def validate_email(self, value):
        """Custom field-level validation — called automatically by is_valid()."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        if value.isdigit():
            raise serializers.ValidationError("Password cannot be entirely numeric.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Validates OTP verification input."""
    email = serializers.EmailField()
    otp   = serializers.CharField(max_length=6, min_length=6)


class LoginSerializer(serializers.Serializer):
    """Validates login credentials."""
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Serializes user data for the /api/me/ response."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name',
                  'is_verified', 'created_at']
        read_only_fields = fields  # All fields are read-only in this serializer
