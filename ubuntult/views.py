from django.shortcuts import get_object_or_404
from django.http import HttpResponsePermanentRedirect

from ubuntult.models import PhpBBForumRefs, PhpBBTopicRefs


def phpbb_viewforum(request):
    ref = get_object_or_404(
        PhpBBForumRefs,
        phpbb_forum_id=request.GET.get('f'),
    )
    return HttpResponsePermanentRedirect(ref.category.get_absolute_url())


def phpbb_viewtopic(request):
    ref = get_object_or_404(
        PhpBBTopicRefs,
        phpbb_forum_id=request.GET.get('f'),
        phpbb_topic_id=request.GET.get('t'),
    )
    return HttpResponsePermanentRedirect(ref.topic.get_absolute_url())
