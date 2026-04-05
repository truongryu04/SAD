from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        pgvector.django.VectorExtension(),
        migrations.CreateModel(
            name="ProductVectorIndex",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_type", models.CharField(max_length=20)),
                ("item_id", models.PositiveIntegerField()),
                ("name", models.CharField(max_length=255)),
                ("brand", models.CharField(blank=True, max_length=255)),
                ("price", models.CharField(blank=True, max_length=80)),
                ("stock", models.IntegerField(default=0)),
                ("description", models.TextField(blank=True)),
                ("content_text", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("embedding", pgvector.django.VectorField(dimensions=256)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [models.Index(fields=["item_type", "item_id"], name="app_productv_item_ty_bf4644_idx")],
                "constraints": [models.UniqueConstraint(fields=("item_type", "item_id"), name="uniq_product_vector_item")],
            },
        ),
    ]
