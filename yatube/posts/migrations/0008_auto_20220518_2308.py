# Generated by Django 2.2.6 on 2022-05-18 18:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220518_2304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(1, 'Поле текста поста не должно быть пустым.')], verbose_name='Текст поста'),
        ),
    ]