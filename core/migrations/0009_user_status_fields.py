from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_idea_empresa_asignada_idea_estado_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userclientes',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userempresa',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]