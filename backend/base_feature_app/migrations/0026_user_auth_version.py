from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_feature_app', '0025_positive_money_amounts'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='auth_version',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
    ]
