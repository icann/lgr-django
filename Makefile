#MKMSG_OPTIONS=--no-wrap
MKMSG_OPTIONS=
MAKEMESSAGES=PYTHONPATH=../.. ../../manage.py makemessages 
COMPILEMESSAGES=PYTHONPATH=../.. ../../manage.py compilemessages

LANGUAGES= \
	   -l ar \
	   -l en \
	   -l fr \


MO_FILES= \
	  src/lgr_web/locale/ar/LC_MESSAGES/django.mo \
	  src/lgr_web/locale/en/LC_MESSAGES/django.mo \
	  src/lgr_web/locale/fr/LC_MESSAGES/django.mo \
	  src/lgr_editor/locale/ar/LC_MESSAGES/django.mo \
	  src/lgr_editor/locale/en/LC_MESSAGES/django.mo \
	  src/lgr_editor/locale/fr/LC_MESSAGES/django.mo \
	  src/lgr_validator/locale/ar/LC_MESSAGES/django.mo \
	  src/lgr_validator/locale/en/LC_MESSAGES/django.mo \
	  src/lgr_validator/locale/fr/LC_MESSAGES/django.mo \
	  src/lgr_tools/locale/ar/LC_MESSAGES/django.mo \
	  src/lgr_tools/locale/en/LC_MESSAGES/django.mo \
	  src/lgr_tools/locale/fr/LC_MESSAGES/django.mo \

PO_FILES= \
	  src/lgr_web/locale/ar/LC_MESSAGES/django.po \
	  src/lgr_web/locale/en/LC_MESSAGES/django.po \
	  src/lgr_web/locale/fr/LC_MESSAGES/django.po \
	  src/lgr_editor/locale/ar/LC_MESSAGES/django.po \
	  src/lgr_editor/locale/en/LC_MESSAGES/django.po \
	  src/lgr_editor/locale/fr/LC_MESSAGES/django.po \
	  src/lgr_validator/locale/ar/LC_MESSAGES/django.po \
	  src/lgr_validator/locale/en/LC_MESSAGES/django.po \
	  src/lgr_validator/locale/fr/LC_MESSAGES/django.po \
	  src/lgr_tools/locale/ar/LC_MESSAGES/django.po \
	  src/lgr_tools/locale/en/LC_MESSAGES/django.po \
	  src/lgr_tools/locale/fr/LC_MESSAGES/django.po \

all: messages

messages: $(MO_FILES)

update: update-lgrweb update-lgreditor update-lgrvalidator update-lgrtools

update-lgrweb:
	cd src/lgr_web && $(MAKEMESSAGES) $(LANGUAGES) $(MKMSG_OPTIONS)

update-lgreditor:
	cd src/lgr_editor && $(MAKEMESSAGES) $(LANGUAGES) $(MKMSG_OPTIONS)

update-lgrvalidator:
	cd src/lgr_validator && $(MAKEMESSAGES) $(LANGUAGES) $(MKMSG_OPTIONS)

update-lgrtools:
	cd src/lgr_tools && $(MAKEMESSAGES) $(LANGUAGES) $(MKMSG_OPTIONS)

src/lgr_web/locale/%/LC_MESSAGES/django.po:
	cd `echo "$@" | sed -e 's#\/locale/.*##'` && django-admin.py makemessages $(LANGUAGES) $(MKMSG_OPTIONS)

src/lgr_editor/locale/%/LC_MESSAGES/django.po:
	cd `echo "$@" | sed -e 's#\/locale/.*##'` && django-admin.py makemessages $(LANGUAGES) $(MKMSG_OPTIONS)

src/lgr_validator/locale/%/LC_MESSAGES/django.po:
	cd `echo "$@" | sed -e 's#\/locale/.*##'` && django-admin.py makemessages $(LANGUAGES) $(MKMSG_OPTIONS)

src/lgr_tools/locale/%/LC_MESSAGES/django.po:
	cd `echo "$@" | sed -e 's#\/locale/.*##'` && django-admin.py makemessages $(LANGUAGES) $(MKMSG_OPTIONS)

$(MO_FILES): $(PO_FILES)
	cd `echo "$@" | sed -e 's#\/locale/.*##'` && $(COMPILEMESSAGES)
