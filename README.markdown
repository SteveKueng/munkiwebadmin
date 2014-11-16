MunkiWebAdmin
--------------

This is an updatet version of MunkiWebAdmin form Greg Neagle.
See http://code.google.com/p/munki/wiki/MunkiWebAdmin



Install on OS X:
----------------
  
Install virtualenv:

    sudo easy_install virtualenv

Create a new virtual environment:

    cd /Users/Shared

    virtualenv munkiwebadmin_env

Go in to the created virtual enviroment:

    cd munkiwebadmin_env

    source bin/activate
  
Install django and tools for django

    pip install django==1.5.1

    pip install django-wsgiserver==0.8.0beta

    pip install django-ajax-search
	
	pip install simplejson
  
 
Clone MunkiWebAdmin

    git clone https://github.com/SteveKueng/munkiwebadmin.git
    
    cd munkiwebadmin
    cp settings_template.py settings.py
    
Edit settings.py:

* Set ADMINS to an administrative name and email
* Set TIME_ZONE to the appropriate timezone
* Under INSTALLED_APPS uncomment django_wsgiserver
* Set MUNKI_REPO_DIR to the local filesystem path to your munki repo. (In this case, /Users/Shared/munki_repo)
* Make other edits as you feel comfortable  

---

    python manage.py syncdb
    python manage.py runwsgiserver port=8000 host=0.0.0.0