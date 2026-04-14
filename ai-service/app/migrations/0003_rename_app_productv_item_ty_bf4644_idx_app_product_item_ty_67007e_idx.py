from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_productvectorindex"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="productvectorindex",
            new_name="app_product_item_ty_67007e_idx",
            old_name="app_productv_item_ty_bf4644_idx",
        ),
    ]