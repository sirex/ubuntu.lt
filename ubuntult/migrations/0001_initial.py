# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spirit_topic', '0002_auto_20150828_2003'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhpBBTopicRefs',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('phpbb_forum_id', models.IntegerField(db_index=True)),
                ('phpbb_topic_id', models.IntegerField(db_index=True)),
                ('topic', models.ForeignKey(to='spirit_topic.Topic', on_delete=models.CASCADE)),
            ],
        ),
    ]
