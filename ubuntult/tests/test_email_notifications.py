from textwrap import dedent

from django.core import mail
from django.urls import reverse

from spirit.core.tests import utils
from spirit.comment.flag.models import Flag, CommentFlag
from spirit.comment.flag.forms import FlagForm



def test_flag_create(app):
    moderator = utils.create_user(username='moderator')
    moderator.st.is_moderator = True
    moderator.st.save()

    user = utils.create_user(username='userx')
    category = utils.create_category()
    topic = utils.create_topic(category=category, user=user)
    comment = utils.create_comment(user=user, topic=topic)

    url = reverse('spirit:comment:flag:create', kwargs={'comment_id': comment.pk})
    form = app.get(url, user=user.username).forms[1]
    form['reason'] = "0"
    resp = form.submit().follow()

    assert len(Flag.objects.all()) == 1
    assert len(CommentFlag.objects.all()) == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "ubuntu.lt: Pranešimas apie netinkamą komentarą"
    assert mail.outbox[0].body == dedent("""\
        Sveiki,

        naudotojas userx, pažymėjo komentarą kaip netinkamą.

        Nuoroda į pranešimą: https://ubuntu.lt/st/admin/comment/flag/{flag.pk}/

        Pranešta apie šį komentarą: https://ubuntu.lt/comment/{flag.comment.pk}/find/

        Pranešėjo pastaba:



        --
        ubuntu.lt
    """.format(flag=Flag.objects.get()))
