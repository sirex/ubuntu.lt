import logging

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email(to, subject, message):
    from_email = settings.DEFAULT_FROM_EMAIL

    for recipient in to:
        try:
            send_mail(
                subject='ubuntu.lt: {subject}'.format(subject=subject),
                message=message,
                from_email=from_email,
                recipient_list=[recipient]
            )
        except OSError as err:
            logger.exception(err)
