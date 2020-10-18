# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spirit_category', '0003_category_is_global'),
        ('ubuntult', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhpBBForumRefs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('phpbb_forum_id', models.IntegerField(db_index=True)),
                ('category', models.ForeignKey(to='spirit_category.Category', on_delete=models.CASCADE)),
            ],
        ),
    ]
