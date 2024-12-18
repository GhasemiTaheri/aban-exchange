from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .services import user_create


class UserSignupApi(APIView):
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
        except Exception:
            raise ValidationError(detail="data is not correct!")

        return Response(data="success", status=201)
