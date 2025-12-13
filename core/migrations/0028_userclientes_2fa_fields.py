# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_userempresa_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='userclientes',
            name='two_factor_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userclientes',
            name='two_factor_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
