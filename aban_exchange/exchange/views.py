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

    async def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        await order_receive(user_id=request.user_id, **serializer.validated_data)
        return Response(data="successful", status=201)
