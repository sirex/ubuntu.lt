from django.urls import re_path
from django.views.generic.base import RedirectView

from ubuntult import views, feeds


urlpatterns = [
    re_path(r'^forum/$', RedirectView.as_view(url='/', permanent=True)),
    re_path(r'^forum/viewforum\.php$', views.phpbb_viewforum),
    re_path(r'^forum/viewtopic\.php$', views.phpbb_viewtopic),
    re_path(r'^feeds/latest/comments/rss/$', feeds.LatestCommentsFeed()),
    re_path(r'^user/register/$', views.register, name='register'),
]
