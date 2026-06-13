# Generated manually for initial Payment model

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.IntegerField(db_index=True)),
                ("amount", models.FloatField()),
                (
                    "status",
                    models.CharField(
                        choices=[("Pending", "Pending"), ("Success", "Success"), ("Failed", "Failed")],
                        default="Pending",
                        max_length=50,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
