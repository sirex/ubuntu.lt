test: env/done
	env/bin/py.test -vv --tb=short ubuntult/tests

env/done: env/bin/pip requirements-dev.txt requirements.txt
	env/bin/pip install -r requirements-dev.txt
	touch env/done

env/bin/pip:
	python3 -m venv env

requirements-dev.txt: env/bin/pip-compile requirements.in requirements-dev.in
	env/bin/pip-compile requirements.in requirements-dev.in -o requirements-dev.txt

requirements.txt: env/bin/pip-compile requirements.in
	env/bin/pip-compile requirements.in -o requirements.txt

env/bin/pip-compile: env/bin/pip
	env/bin/pip install pip-tools

upgrade: env/done
	env/bin/pip-compile --upgrade requirements.in requirements-dev.in -o requirements-dev.txt
	env/bin/pip-compile --upgrade requirements.in -o requirements.txt

.PHONY: test upgrade
