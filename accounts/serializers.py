from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "roles",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return list(
            obj.groups.values_list("name", flat=True)
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    role = serializers.ChoiceField(
        choices=settings.CVDM_SELF_ASSIGNABLE_ROLES,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "role",
        ]


    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def create(self, validated_data):
        role = validated_data.pop("role")
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()

        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        return user