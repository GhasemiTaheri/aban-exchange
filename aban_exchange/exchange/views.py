from django.conf import settings
from rest_framework import serializers
from rest_framework.views import APIView

User = settings.AUTH_USER_MODEL


class OrderCreateApi(APIView):
    class InputSerializer(serializers.Serializer):
        user =  serializers.IntegerField(required=True, allow_null=False, min_value=1)
        amount = serializers.IntegerField(required=True, allow_null=False, min_value=1)
        price = serializers.IntegerField(required=True, allow_null=False, min_value=1)

    class OutputSerializer(serializers.Serializer):
        pass

    async def post(self, request):
        pass
