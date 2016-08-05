from spirit.core.tests import utils

from ubuntult.models import PhpBBForumRefs, PhpBBTopicRefs


def test_viewtopic(app):
    user = utils.create_user()
    category = utils.create_category()
    topic = utils.create_topic(category=category, user=user)

    PhpBBForumRefs.objects.create(category=category, phpbb_forum_id=1)
    PhpBBTopicRefs.objects.create(topic=topic, phpbb_forum_id=1, phpbb_topic_id=2)

    # Test success
    app.get('/forum/viewforum.php?f=1')
    app.get('/forum/viewtopic.php?f=1&t=2')

    # Test 404
    app.get('/forum/viewforum.php?f=2', status=404)
    app.get('/forum/viewtopic.php?f=1&t=3', status=404)

    # Test NaN's
    app.get('/forum/viewtopic.php?f=NaN', status=404)
    app.get('/forum/viewtopic.php?t=42NaN', status=404)
    app.get('/forum/viewforum.php?f=42Nan', status=404)
