# Generated by Django 5.1.6 on 2025-03-29 20:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_eventview'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='eventregistration',
            unique_together={('event', 'user')},
        ),
    ]
