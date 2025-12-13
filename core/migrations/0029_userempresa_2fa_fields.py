# Generated manually for 2FA empresa fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_userclientes_2fa_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='userempresa',
            name='two_factor_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userempresa',
            name='two_factor_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
