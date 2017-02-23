from django.conf.urls import url
from django.views.generic.base import RedirectView

from ubuntult import views, feeds


urlpatterns = [
    url(r'^forum/$', RedirectView.as_view(url='/', permanent=True)),
    url(r'^forum/viewforum\.php$', views.phpbb_viewforum),
    url(r'^forum/viewtopic\.php$', views.phpbb_viewtopic),
    url(r'^feeds/latest/comments/rss/$', feeds.LatestCommentsFeed()),
]
