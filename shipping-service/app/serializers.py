from rest_framework import serializers

from .models import ShippingMethod


class ShippingCreateRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    address = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def validate_address(self, value: str):
        if not (value or "").strip():
            raise serializers.ValidationError("address is required.")
        return value.strip()


class ShippingStatusQuerySerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ["id", "code", "name", "fee", "is_active", "created_at", "updated_at"]


class ShippingMethodWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ["code", "name", "fee", "is_active"]

    def validate_code(self, value: str):
        value = (value or "").strip().upper()
        if not value:
            raise serializers.ValidationError("code is required.")

        qs = ShippingMethod.objects.filter(code=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("code already exists.")
        return value

    def validate_name(self, value: str):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("name is required.")
        return value

    def validate_fee(self, value: float):
        try:
            fee = float(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("fee must be a number.")
        if fee < 0:
            raise serializers.ValidationError("fee must be >= 0.")
        return fee
