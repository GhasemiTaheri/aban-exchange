from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .services import user_create


class UserSignupApi(APIView):
    """
    API view for user signup.

    Allows unauthenticated users to register by providing their username, email,
    and password.
    This API creates a new user and returns a success message if the data is valid.

    Attributes:
        authentication_classes: Disables authentication for this endpoint.
        permission_classes: Allows unrestricted access to this endpoint.
    """

    authentication_classes = ()
    permission_classes = ()

    class InputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ["username", "email", "password"]
            extra_kwargs = {"email": {"required": True}}

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_create(**serializer.validated_data)
        except Exception:  # noqa: BLE001
            raise ValidationError(detail="data is not correct!")  # noqa: B904

        return Response(data="success", status=201)
