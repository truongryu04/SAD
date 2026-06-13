from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('data_type', models.CharField(max_length=50)),
                ('unit', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('parent_id', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='CategoryAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_id', models.IntegerField()),
                ('attribute_id', models.IntegerField()),
                ('is_required', models.BooleanField(default=False)),
                ('display_order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['display_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_id', models.IntegerField()),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('reserved_quantity', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.IntegerField()),
                ('attribute_id', models.IntegerField()),
                ('value', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='StockTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_id', models.IntegerField()),
                ('change_quantity', models.IntegerField()),
                ('type', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='attribute',
            constraint=models.UniqueConstraint(fields=('name',), name='uniq_attribute_name'),
        ),
        migrations.AddConstraint(
            model_name='categoryattribute',
            constraint=models.UniqueConstraint(fields=('category_id', 'attribute_id'), name='uniq_category_attribute'),
        ),
        migrations.AddConstraint(
            model_name='productattributevalue',
            constraint=models.UniqueConstraint(fields=('product_id', 'attribute_id'), name='uniq_product_attribute_value'),
        ),
    ]
