# Compatibility migration placeholder for previously introduced order tables.
# Order domain has been moved to dedicated order-service.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_useractivity'),
    ]

    operations = []
