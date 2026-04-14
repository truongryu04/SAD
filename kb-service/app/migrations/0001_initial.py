from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="KBCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.IntegerField(unique=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("raw_payload", models.JSONField(default=dict)),
                ("synced_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="KBInventory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.IntegerField(unique=True)),
                ("variant_id", models.IntegerField()),
                ("quantity", models.IntegerField(default=0)),
                ("reserved_quantity", models.IntegerField(default=0)),
                ("raw_payload", models.JSONField(default=dict)),
                ("synced_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="KBProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.IntegerField(unique=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("brand", models.CharField(blank=True, max_length=120)),
                ("category_external_id", models.IntegerField(blank=True, null=True)),
                ("category_name", models.CharField(blank=True, max_length=200)),
                ("base_price", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("status", models.CharField(blank=True, max_length=50)),
                ("normalized_text", models.TextField(blank=True)),
                ("raw_payload", models.JSONField(default=dict)),
                ("synced_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="KBSyncCheckpoint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_name", models.CharField(max_length=50, unique=True)),
                ("records_synced", models.IntegerField(default=0)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
