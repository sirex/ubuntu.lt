#Running the example application

Assuming you use virtualenv, follow these steps to download and run the
Spirit example application in this directory:


    $ git clone https://github.com/sirex/ubuntu.lt.git
    $ cd ubuntu.lt
    $ virtualenv -p /usr/bin/python3 venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ python manage.py spiritinstall
    $ python manage.py runserver

Visit http://127.0.0.1:8000/

> This will run using the *developer* settings,
> which are not suitable for production environments.


> On production, you should create a `prod_local.py`,
> import the production settings `from .prod import *`
> and overwrite settings such as `SECRET_KEY`, `DATABASES` and `ALLOWED_HOSTS`.
>
> You should run Spirit on a real web server. ie: gunicorn + Nginx.


> An email server is required, you can host your own (ie: [exim](http://www.exim.org/)),
> or hire an external service provider (ie: [Mandrill](http://mandrill.com/)).


> You will need to setup a search engine,
> Spirit is configured to work with [Woosh](https://bitbucket.org/mchaput/whoosh/wiki/Home) by default.

