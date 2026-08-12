from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_app', '0006_xmldocument_title_manually_edited'),
    ]

    operations = [
        migrations.AddField(
            model_name='xmldocument',
            name='eadid',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='xmldocument',
            name='public_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='xmldocument',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
