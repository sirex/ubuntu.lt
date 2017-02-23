from lxml import etree

from spirit.core.tests import utils
from spirit.comment.flag.models import Flag, CommentFlag
from spirit.comment.flag.forms import FlagForm



def test_latest_comments_feed(app):
    user = utils.create_user(username='userx')
    category = utils.create_category()
    topic = utils.create_topic(category=category, user=user)
    comment = utils.create_comment(user=user, topic=topic)

    resp = app.get('/feeds/latest/comments/rss/')
    rss = etree.fromstring(resp.content)

    assert rss.xpath('//item/title/text()') == [topic.title]
    assert rss.xpath('//item/category/text()') == [category.title]
    assert rss.xpath('//item/link/text()') == ['http://localhost:80/comment/%s/find/' % comment.pk]
