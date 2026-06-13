from django.db import migrations


def seed_shipping_methods(apps, schema_editor):
    ShippingMethod = apps.get_model("app", "ShippingMethod")

    if ShippingMethod.objects.exists():
        return

    ShippingMethod.objects.bulk_create(
        [
            ShippingMethod(code="STANDARD", name="Standard delivery", fee=0, is_active=True),
            ShippingMethod(code="EXPRESS", name="Express delivery", fee=30000, is_active=True),
            ShippingMethod(code="SAME_DAY", name="Same-day delivery", fee=50000, is_active=True),
        ],
        ignore_conflicts=True,
    )


def noop_reverse(apps, schema_editor):
    # Keep seeded rows (safe default).
    return


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_shippingmethod"),
    ]

    operations = [
        migrations.RunPython(seed_shipping_methods, reverse_code=noop_reverse),
    ]
