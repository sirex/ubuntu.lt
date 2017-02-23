Development environment
=======================

Assuming you use virtualenv, follow these steps to download and run the Spirit
example application in this directory::


    $ git clone https://github.com/sirex/ubuntu.lt.git
    $ cd ubuntu.lt
    $ virtualenv -p /usr/bin/python3 venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ createdb ubuntult
    $ ./manage.py spiritinstall
    $ ./manage.py createsuperuser
    $ ./manage.py runserver

Visit http://127.0.0.1:8000/


Translations
============

While Lithuanian translations are still not included in Spirit [1]_, all
translation messages have to be merged into one using following command::

    msgcat --use-first ubuntult/transifex/*.po > ubuntult/locale/lt/LC_MESSAGES/django.po

After that, you need to compile messages::

    (cd ubuntult && django-admin compilemessages -l lt)

Once you update transaltion messages, you have to repeat this precedure all
over again.

.. [1] https://github.com/nitely/Spirit/issues/167
