from django.shortcuts import get_object_or_404
from django.http import HttpResponsePermanentRedirect, Http404

from ubuntult.models import PhpBBForumRefs, PhpBBTopicRefs
from ubuntult.forms import ViewForumParams, ViewTopicParams


def phpbb_viewforum(request):
    form = ViewForumParams(request.GET)
    if form.is_valid():
        params = form.cleaned_data
        ref = get_object_or_404(
            PhpBBForumRefs,
            phpbb_forum_id=params['f'],
        )
        return HttpResponsePermanentRedirect(ref.category.get_absolute_url())
    else:
        raise Http404(form.errors.as_text())


def phpbb_viewtopic(request):
    form = ViewTopicParams(request.GET)
    if form.is_valid():
        params = form.cleaned_data
        ref = get_object_or_404(
            PhpBBTopicRefs,
            phpbb_forum_id=params['f'],
            phpbb_topic_id=params['t'],
        )
        return HttpResponsePermanentRedirect(ref.topic.get_absolute_url())
    else:
        raise Http404(form.errors.as_text())
