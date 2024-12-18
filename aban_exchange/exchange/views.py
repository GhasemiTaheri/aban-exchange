from django.conf import settings
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import order_receive

User = settings.AUTH_USER_MODEL


class OrderCreateApi(APIView):
    class InputSerializer(serializers.Serializer):
        amount = serializers.IntegerField(required=True, allow_null=False, min_value=1)
        price = serializers.IntegerField(required=True, allow_null=False, min_value=1)

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_receive(
            user_id=request.user.id,
            **serializer.validated_data,
        )
        return Response(
            data={
                "detail": "we recieve your order successfully. we notice you with email!",  # noqa: E501
            },
            status=201,
        )
