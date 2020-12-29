from django.contrib import messages
from django.http import Http404
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from spirit.core.conf import settings
from spirit.core.utils.ratelimit.decorators import ratelimit
from spirit.core.utils.views import is_post
from spirit.core.utils.views import post_data
from spirit.user.utils.email import send_activation_email

from ubuntult.forms import RegistrationForm
from ubuntult.forms import ViewForumParams
from ubuntult.forms import ViewTopicParams
from ubuntult.models import PhpBBForumRefs
from ubuntult.models import PhpBBTopicRefs


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


@ratelimit(rate='2/10s')
def register(request, registration_form=RegistrationForm):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', reverse('spirit:user:update')))

    form = registration_form(data=post_data(request))

    if (
        is_post(request) and
        not request.is_limited() and
        form.is_valid()
    ):
        user = form.save()
        send_activation_email(request, user)
        messages.info(request, _(
            "We have sent you an email to %(email)s "
            "so you can activate your account!"
        ) % {'email': form.get_email()})
        return redirect(reverse(settings.LOGIN_URL))

    return render(
        request=request,
        template_name='spirit/user/auth/register.html',
        context={'form': form}
    )
