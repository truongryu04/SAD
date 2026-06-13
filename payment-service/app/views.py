import logging
import random

from django.conf import settings
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, PaymentMethod
from .serializers import (
    PaymentPayRequestSerializer,
    PaymentStatusQuerySerializer,
    PaymentMethodSerializer,
    PaymentMethodWriteSerializer,
)


logger = logging.getLogger(__name__)


class PaymentPayView(APIView):
    def post(self, request):
        logger.info("payment.pay request")
        serializer = PaymentPayRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = int(serializer.validated_data["order_id"])
        amount = float(serializer.validated_data["amount"])

        payment = Payment.objects.create(order_id=order_id, amount=amount, status=Payment.STATUS_PENDING)

        succeeded = random.random() < float(getattr(settings, "PAYMENT_SUCCESS_RATE", 0.9))
        payment.status = Payment.STATUS_SUCCESS if succeeded else Payment.STATUS_FAILED
        payment.save(update_fields=["status"])

        logger.info("payment.pay result order_id=%s status=%s", order_id, payment.status)
        return Response({"order_id": order_id, "status": payment.status}, status=status.HTTP_200_OK)


class PaymentStatusView(APIView):
    def get(self, request):
        logger.info("payment.status request")
        query = PaymentStatusQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = int(query.validated_data["order_id"])
        payment = Payment.objects.filter(order_id=order_id).order_by("-created_at", "-id").first()
        if not payment:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"order_id": order_id, "status": payment.status}, status=status.HTTP_200_OK)


class PaymentMethodListCreateView(generics.ListCreateAPIView):
    queryset = PaymentMethod.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PaymentMethodWriteSerializer
        return PaymentMethodSerializer


class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PaymentMethod.objects.all()

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return PaymentMethodWriteSerializer
        return PaymentMethodSerializer
