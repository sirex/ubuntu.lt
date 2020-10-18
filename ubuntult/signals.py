from textwrap import dedent

from django.urls import reverse
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from spirit.comment.flag.models import Flag

from ubuntult.email import send_email



def notify_mods(sender, instance, created, **kwargs):
    flag = instance

    if created:
        User = get_user_model()
        to = User.objects.filter(st__is_moderator=True).values_list('email', flat=True)
        context = {
            'user': flag.user.username,
            'comment': flag.body,
            'post_link': flag.comment.get_absolute_url(),
            'flag_link': reverse('spirit:admin:flag:detail', kwargs={'pk': flag.pk})
        }
        send_email(to, "Pranešimas apie netinkamą komentarą", dedent("""\
            Sveiki,

            naudotojas {user}, pažymėjo komentarą kaip netinkamą.

            Nuoroda į pranešimą: https://ubuntu.lt{flag_link}

            Pranešta apie šį komentarą: https://ubuntu.lt{post_link}

            Pranešėjo pastaba:
            {comment}


            --
            ubuntu.lt
        """).format(**context))

post_save.connect(notify_mods, sender=Flag, dispatch_uid=__name__)
