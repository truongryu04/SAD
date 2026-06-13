from django.db import migrations, models
import django.db.models.deletion


def _guess_product_type(category_name: str, product_name: str, description: str, brand: str) -> str:
    category_name = (category_name or "").lower()
    product_name = (product_name or "").lower()
    description = (description or "").lower()
    brand = (brand or "").strip()

    if brand:
        return "ELECTRONICS"

    book_keywords = ["book", "sach", "textbook", "novel", "isbn"]
    fashion_keywords = ["fashion", "clothes", "shirt", "pants", "shoes", "ao", "quan", "giay"]

    haystack = f"{category_name} {product_name} {description}"
    if any(k in haystack for k in book_keywords):
        return "BOOK"
    if any(k in haystack for k in fashion_keywords):
        return "FASHION"

    return "ELECTRONICS"


def copy_legacy_data(apps, schema_editor):
    LegacyProduct = apps.get_model("app", "LegacyProduct")
    LegacyCategory = apps.get_model("app", "LegacyCategory")

    Category = apps.get_model("app", "Category")
    Product = apps.get_model("app", "Product")
    Book = apps.get_model("app", "Book")
    Electronics = apps.get_model("app", "Electronics")
    Fashion = apps.get_model("app", "Fashion")

    legacy_categories = list(LegacyCategory.objects.all())
    legacy_category_by_id = {c.id: c for c in legacy_categories}

    category_id_map = {}
    for legacy_category in legacy_categories:
        new_category = Category.objects.create(name=legacy_category.name)
        category_id_map[legacy_category.id] = new_category.id

    uncategorized = None

    for legacy_product in LegacyProduct.objects.all().iterator():
        legacy_category = legacy_category_by_id.get(getattr(legacy_product, "category_id", None))
        legacy_category_name = getattr(legacy_category, "name", "") if legacy_category else ""

        mapped_category_id = category_id_map.get(getattr(legacy_product, "category_id", None))
        if mapped_category_id is None:
            if uncategorized is None:
                uncategorized = Category.objects.create(name="Uncategorized")
            mapped_category_id = uncategorized.id

        product_type = _guess_product_type(
            legacy_category_name,
            getattr(legacy_product, "name", ""),
            getattr(legacy_product, "description", ""),
            getattr(legacy_product, "brand", ""),
        )

        base_price = getattr(legacy_product, "base_price", 0) or 0
        try:
            price = float(base_price)
        except (TypeError, ValueError):
            price = 0.0

        new_product = Product.objects.create(
            name=getattr(legacy_product, "name", ""),
            price=price,
            stock=0,
            category_id=mapped_category_id,
            product_type=product_type,
        )

        if product_type == "BOOK":
            Book.objects.create(
                product_id=new_product.id,
                author="Unknown",
                publisher="Unknown",
                isbn=f"UNKNOWN-{legacy_product.id}",
            )
        elif product_type == "FASHION":
            Fashion.objects.create(
                product_id=new_product.id,
                size="M",
                color="Black",
            )
        else:
            brand = (getattr(legacy_product, "brand", "") or "").strip() or "Unknown"
            Electronics.objects.create(
                product_id=new_product.id,
                brand=brand,
                warranty=12,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_merge_product_domain"),
    ]

    operations = [
        # 1) Rename legacy models to keep data around during transformation.
        migrations.RenameModel(old_name="Product", new_name="LegacyProduct"),
        migrations.RenameModel(old_name="Category", new_name="LegacyCategory"),

        # 2) Create the new schema (Table-per-Type via composition).
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("price", models.FloatField()),
                ("stock", models.IntegerField()),
                (
                    "product_type",
                    models.CharField(
                        choices=[
                            ("BOOK", "Book"),
                            ("ELECTRONICS", "Electronics"),
                            ("FASHION", "Fashion"),
                        ],
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="app.category",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author", models.CharField(max_length=255)),
                ("publisher", models.CharField(max_length=255)),
                ("isbn", models.CharField(max_length=20)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="book",
                        to="app.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Electronics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("brand", models.CharField(max_length=100)),
                ("warranty", models.IntegerField()),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="electronics",
                        to="app.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Fashion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("size", models.CharField(max_length=10)),
                ("color", models.CharField(max_length=50)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fashion",
                        to="app.product",
                    ),
                ),
            ],
        ),

        # 3) Copy legacy data into the new schema.
        migrations.RunPython(copy_legacy_data, reverse_code=migrations.RunPython.noop),

        # 4) Drop legacy tables (old data is removed after seeding the new schema).
        migrations.DeleteModel(name="ProductVariant"),
        migrations.DeleteModel(name="Attribute"),
        migrations.DeleteModel(name="CategoryAttribute"),
        migrations.DeleteModel(name="Inventory"),
        migrations.DeleteModel(name="ProductAttributeValue"),
        migrations.DeleteModel(name="StockTransaction"),
        migrations.DeleteModel(name="LegacyProduct"),
        migrations.DeleteModel(name="LegacyCategory"),
    ]
