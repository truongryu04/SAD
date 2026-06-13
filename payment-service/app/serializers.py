from rest_framework import serializers

from .models import PaymentMethod


class PaymentPayRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    amount = serializers.FloatField()

    def validate_amount(self, value: float):
        if value is None:
            raise serializers.ValidationError("amount is required.")
        if value <= 0:
            raise serializers.ValidationError("amount must be > 0.")
        return float(value)


class PaymentStatusQuerySerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "code", "name", "is_active", "created_at", "updated_at"]


class PaymentMethodWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["code", "name", "is_active"]

    def validate_code(self, value: str):
        value = (value or "").strip().upper()
        if not value:
            raise serializers.ValidationError("code is required.")

        qs = PaymentMethod.objects.filter(code=value)
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
