from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
                migrations.RunSQL(
                        sql="""
                                DELETE FROM app_categoryattribute a
                                USING app_categoryattribute b
                                WHERE a.id > b.id
                                    AND a.category_id = b.category_id
                                    AND a.attribute_id = b.attribute_id;

                                DELETE FROM app_productattributevalue a
                                USING app_productattributevalue b
                                WHERE a.id > b.id
                                    AND a.product_id = b.product_id
                                    AND a.attribute_id = b.attribute_id;

                                DELETE FROM app_attribute a
                                USING app_attribute b
                                WHERE a.id > b.id
                                    AND a.name = b.name;
                        """,
                        reverse_sql=migrations.RunSQL.noop,
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
