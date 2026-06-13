from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Product, Category
from .serializers import CategorySerializer, ProductReadSerializer, ProductWriteSerializer


class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer


class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductListCreateView(generics.ListCreateAPIView):
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = Product.objects.select_related("category", "book", "electronics", "fashion").all().order_by("-id")
        category_id = self.request.query_params.get("category_id")
        product_type = self.request.query_params.get("product_type")
        name = self.request.query_params.get("name") or self.request.query_params.get("search")

        if category_id:
            qs = qs.filter(category_id=category_id)
        if product_type:
            qs = qs.filter(product_type=product_type.upper())
        if name:
            qs = qs.filter(name__icontains=name)
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductWriteSerializer
        return ProductReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = Product.objects.select_related("category", "book", "electronics", "fashion").get(pk=product.pk)
        return Response(ProductReadSerializer(product, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("category", "book", "electronics", "fashion")

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return ProductWriteSerializer
        return ProductReadSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = Product.objects.select_related("category", "book", "electronics", "fashion").get(pk=product.pk)
        return Response(ProductReadSerializer(product, context={"request": request}).data)


class CategoryProductsView(generics.ListAPIView):
    serializer_class = ProductReadSerializer
    pagination_class = DefaultPagination

    def _collect_category_ids(self, root_id: int):
        category_ids = [root_id]
        frontier = [root_id]

        while frontier:
            children = list(
                Category.objects.filter(parent_id__in=frontier).values_list("id", flat=True)
            )
            if not children:
                break
            category_ids.extend(children)
            frontier = children

        return category_ids

    def get_queryset(self):
        category = get_object_or_404(Category, pk=self.kwargs["pk"])
        category_ids = self._collect_category_ids(category.id)
        return Product.objects.select_related(
            "category", "book", "electronics", "fashion"
        ).filter(category_id__in=category_ids).order_by("-id")
