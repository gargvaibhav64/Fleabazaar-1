# Generated by Django 2.2.7 on 2019-12-20 14:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0004_auto_20191218_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('street_address', models.CharField(max_length=200)),
                ('apartment_address', models.CharField(max_length=200)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('state', models.CharField(max_length=50)),
                ('zip', models.CharField(max_length=6)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]