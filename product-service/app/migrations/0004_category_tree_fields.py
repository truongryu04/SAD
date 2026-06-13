from django.db import migrations, models
import django.db.models.deletion


def populate_category_product_type(apps, schema_editor):
    Category = apps.get_model("app", "Category")
    Product = apps.get_model("app", "Product")

    for category in Category.objects.all().iterator():
        first_product = Product.objects.filter(category_id=category.id).order_by("id").first()
        category.product_type = first_product.product_type if first_product else "ELECTRONICS"
        category.save(update_fields=["product_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0003_tpt_product_schema"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="children",
                to="app.category",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="product_type",
            field=models.CharField(
                choices=[
                    ("BOOK", "Book"),
                    ("ELECTRONICS", "Electronics"),
                    ("FASHION", "Fashion"),
                ],
                default="ELECTRONICS",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_category_product_type, reverse_code=migrations.RunPython.noop),
    ]
