import logging

from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shipment, ShippingMethod
from .serializers import (
    ShippingCreateRequestSerializer,
    ShippingStatusQuerySerializer,
    ShippingMethodSerializer,
    ShippingMethodWriteSerializer,
)


logger = logging.getLogger(__name__)


class ShippingCreateView(APIView):
    def post(self, request):
        logger.info("shipping.create request")
        serializer = ShippingCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = int(serializer.validated_data["order_id"])
        address = serializer.validated_data["address"]

        shipment = Shipment.objects.create(order_id=order_id, address=address, status=Shipment.STATUS_PROCESSING)
        logger.info("shipping.create result order_id=%s status=%s", order_id, shipment.status)
        return Response({"order_id": order_id, "status": shipment.status}, status=status.HTTP_200_OK)


class ShippingStatusView(APIView):
    def get(self, request):
        logger.info("shipping.status request")
        query = ShippingStatusQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = int(query.validated_data["order_id"])
        shipment = Shipment.objects.filter(order_id=order_id).order_by("-created_at", "-id").first()
        if not shipment:
            return Response({"error": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Simple state progression (optional): Processing -> Shipping -> Delivered.
        if shipment.status == Shipment.STATUS_PROCESSING:
            shipment.status = Shipment.STATUS_SHIPPING
            shipment.save(update_fields=["status", "updated_at"])
        elif shipment.status == Shipment.STATUS_SHIPPING:
            shipment.status = Shipment.STATUS_DELIVERED
            shipment.save(update_fields=["status", "updated_at"])

        return Response({"order_id": order_id, "status": shipment.status}, status=status.HTTP_200_OK)


class ShippingMethodListCreateView(generics.ListCreateAPIView):
    queryset = ShippingMethod.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ShippingMethodWriteSerializer
        return ShippingMethodSerializer


class ShippingMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ShippingMethod.objects.all()

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return ShippingMethodWriteSerializer
        return ShippingMethodSerializer
