import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_userprofile_default_resume'),
        ('searches', '0007_backfill_search_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='search',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='searches', to='accounts.userprofile'),
        ),
    ]
