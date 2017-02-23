from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

from spirit.comment.models import Comment


class LatestCommentsFeed(Feed):
    title = "ubuntu.lt naujausių komentarų srautas"
    link = "/"
    description = "64 naujausi komentarai iš visų kategorijų."

    def items(self):
        return Comment.objects.select_related('user', 'topic', 'topic__category').order_by('-date')[:64]

    def item_title(self, item):
        return item.topic.title

    def item_author_name(self, item):
        return item.user.username

    def item_pubdate(self, item):
        return item.date

    def item_description(self, item):
        return item.comment

    def item_categories(self, item):
        return [item.topic.category.title]
