from rest_framework import serializers

from .models import Book, Category, Electronics, Fashion, Product


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "product_type", "parent", "children"]

    def get_children(self, obj):
        return [
            {
                "id": child.id,
                "name": child.name,
                "product_type": child.product_type,
            }
            for child in obj.children.all().order_by("id")
        ]

    def validate(self, attrs):
        product_type = attrs.get("product_type", getattr(self.instance, "product_type", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))

        if parent and product_type and parent.product_type != product_type:
            raise serializers.ValidationError({"parent": "Parent category must have the same product_type."})

        if self.instance and parent and parent.id == self.instance.id:
            raise serializers.ValidationError({"parent": "Category cannot be parent of itself."})

        return attrs


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["author", "publisher", "isbn", "publication_date", "language"]


class ElectronicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electronics
        fields = ["model_name", "brand", "warranty", "weight", "dimensions", "color"]


class FashionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fashion
        fields = ["brand", "size", "color", "material", "season", "gender"]


class ProductReadSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source="category.id", read_only=True)
    imageUrl = serializers.URLField(source="image_url", read_only=True)
    book = BookSerializer(read_only=True)
    electronics = ElectronicsSerializer(read_only=True)
    fashion = FashionSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "image_url",
            "imageUrl",
            "price",
            "stock",
            "category_id",
            "product_type",
            "book",
            "electronics",
            "fashion",
            "created_at",
            "updated_at",
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    image_url = serializers.URLField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        # Backward/forward compatibility with clients using camelCase.
        # (Staff UI and some clients send imageUrl instead of image_url.)
        if isinstance(data, dict):
            if "imageUrl" in data and "image_url" not in data:
                data = data.copy()
                data["image_url"] = data.get("imageUrl")
        return super().to_internal_value(data)

    # Book fields
    author = serializers.CharField(required=False, allow_blank=True)
    publisher = serializers.CharField(required=False, allow_blank=True)
    isbn = serializers.CharField(required=False, allow_blank=True)
    publication_date = serializers.DateField(required=False, allow_null=True)
    language = serializers.CharField(required=False, allow_blank=True)

    # Electronics fields
    model_name = serializers.CharField(required=False, allow_blank=True)
    brand = serializers.CharField(required=False, allow_blank=True)
    warranty = serializers.IntegerField(required=False)
    weight = serializers.FloatField(required=False)
    dimensions = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, allow_blank=True)

    # Fashion fields
    size = serializers.CharField(required=False, allow_blank=True)
    material = serializers.CharField(required=False, allow_blank=True)
    season = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "image_url",
            "price",
            "stock",
            "category_id",
            "product_type",
            # book
            "author",
            "publisher",
            "isbn",
            "publication_date",
            "language",
            # electronics
            "model_name",
            "brand",
            "warranty",
            "weight",
            "dimensions",
            "color",
            # fashion
            "size",
            "material",
            "season",
            "gender",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        request_method = getattr(self.context.get("request"), "method", "").upper()

        product_type = attrs.get("product_type")
        if request_method in {"PUT", "PATCH"} and self.instance is not None:
            # For updates, allow product_type to be changed if explicitly provided
            # Otherwise use existing product_type
            if product_type is None:
                product_type = self.instance.product_type

        if not product_type:
            raise serializers.ValidationError({"product_type": "product_type is required."})

        # Keep creation requirements aligned with the staff UI payloads.
        # Other fields are optional and will be defaulted by model definitions / create_with_subtype.
        required_by_type = {
            Product.PRODUCT_TYPE_BOOK: ["author", "publisher", "isbn"],
            Product.PRODUCT_TYPE_ELECTRONICS: ["brand"],
            Product.PRODUCT_TYPE_FASHION: ["size", "color"],
        }
        required_fields = required_by_type.get(product_type)
        if required_fields is None:
            raise serializers.ValidationError({"product_type": "Invalid product_type."})

        category_obj = None
        if "category_id" in attrs:
            category_id = attrs.get("category_id")
            try:
                category_obj = Category.objects.get(id=category_id)
            except Category.DoesNotExist as exc:
                raise serializers.ValidationError({"category_id": "category_id does not exist."}) from exc
        elif self.instance is not None:
            category_obj = self.instance.category

        if category_obj and category_obj.product_type != product_type:
            raise serializers.ValidationError({
                "category_id": "Category product_type must match product_type."
            })

        if request_method == "POST":
            missing = [f for f in required_fields if attrs.get(f) in (None, "")]
            if missing:
                raise serializers.ValidationError({"subtype": f"Missing subtype fields: {', '.join(missing)}"})

        return attrs

    def create(self, validated_data):
        category_id = validated_data.pop("category_id")

        subtype_fields = {
            # book
            "author": validated_data.pop("author", None),
            "publisher": validated_data.pop("publisher", None),
            "isbn": validated_data.pop("isbn", None),
            "publication_date": validated_data.pop("publication_date", None),
            "language": validated_data.pop("language", None),
            # electronics
            "model_name": validated_data.pop("model_name", None),
            "brand": validated_data.pop("brand", None),
            "warranty": validated_data.pop("warranty", None),
            "weight": validated_data.pop("weight", None),
            "dimensions": validated_data.pop("dimensions", None),
            "color": validated_data.pop("color", None),
            # fashion
            "size": validated_data.pop("size", None),
            "material": validated_data.pop("material", None),
            "season": validated_data.pop("season", None),
            "gender": validated_data.pop("gender", None),
        }
        subtype_fields = {k: v for k, v in subtype_fields.items() if v is not None}

        category = Category.objects.get(id=category_id)

        return Product.create_with_subtype(category=category, **validated_data, **subtype_fields)

    def update(self, instance, validated_data):
        old_product_type = instance.product_type
        
        if "category_id" in validated_data:
            category_id = validated_data.pop("category_id")
            instance.category = Category.objects.get(id=category_id)

        subtype_fields = {
            # book
            "author": validated_data.pop("author", None),
            "publisher": validated_data.pop("publisher", None),
            "isbn": validated_data.pop("isbn", None),
            "publication_date": validated_data.pop("publication_date", None),
            "language": validated_data.pop("language", None),
            # electronics
            "model_name": validated_data.pop("model_name", None),
            "brand": validated_data.pop("brand", None),
            "warranty": validated_data.pop("warranty", None),
            "weight": validated_data.pop("weight", None),
            "dimensions": validated_data.pop("dimensions", None),
            "color": validated_data.pop("color", None),
            # fashion
            "size": validated_data.pop("size", None),
            "material": validated_data.pop("material", None),
            "season": validated_data.pop("season", None),
            "gender": validated_data.pop("gender", None),
        }
        subtype_fields = {k: v for k, v in subtype_fields.items() if v is not None}

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        # If product_type changed, delete old subtype
        if instance.product_type != old_product_type:
            if old_product_type == Product.PRODUCT_TYPE_BOOK:
                Book.objects.filter(product=instance).delete()
            elif old_product_type == Product.PRODUCT_TYPE_ELECTRONICS:
                Electronics.objects.filter(product=instance).delete()
            elif old_product_type == Product.PRODUCT_TYPE_FASHION:
                Fashion.objects.filter(product=instance).delete()

        if subtype_fields:
            if instance.product_type == Product.PRODUCT_TYPE_BOOK:
                Book.objects.update_or_create(product=instance, defaults={k: subtype_fields.get(k) for k in ("author", "publisher", "isbn", "publication_date", "language") if k in subtype_fields})
            elif instance.product_type == Product.PRODUCT_TYPE_ELECTRONICS:
                Electronics.objects.update_or_create(product=instance, defaults={k: subtype_fields.get(k) for k in ("model_name", "brand", "warranty", "weight", "dimensions", "color") if k in subtype_fields})
            elif instance.product_type == Product.PRODUCT_TYPE_FASHION:
                Fashion.objects.update_or_create(product=instance, defaults={k: subtype_fields.get(k) for k in ("brand", "size", "color", "material", "season", "gender") if k in subtype_fields})

        return instance
