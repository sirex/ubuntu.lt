from django.db import models

import ubuntult.signals  # noqa


class PhpBBForumRefs(models.Model):
    category = models.ForeignKey('spirit_category.Category', on_delete=models.CASCADE)
    phpbb_forum_id = models.IntegerField(db_index=True)


class PhpBBTopicRefs(models.Model):
    topic = models.ForeignKey('spirit_topic.Topic', on_delete=models.CASCADE)
    phpbb_forum_id = models.IntegerField(db_index=True)
    phpbb_topic_id = models.IntegerField(db_index=True)
