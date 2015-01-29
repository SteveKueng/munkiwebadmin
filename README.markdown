MunkiWebAdmin
--------------

This is an updatet version of MunkiWebAdmin form Greg Neagle.
See https://github.com/munki/munkiwebadmin



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

    pip install django==1.6.9  (Python2.6)
    pip install django==1.7.2  (Python2.7)
 
Clone MunkiWebAdmin

    git clone https://github.com/SteveKueng/munkiwebadmin.git
    
    cd munkiwebadmin/munkiwebadmin
    cp settings_template.py settings.py
    
Edit settings.py:

* Set ADMINS to an administrative name and email
* Set TIME_ZONE to the appropriate timezone
* Under INSTALLED_APPS uncomment django_wsgiserver
* Set MUNKI_REPO_DIR to the local filesystem path to your munki repo. (In this case, /Users/Shared/munki_repo)
* Make other edits as you feel comfortable  

---
    cd ..
    python manage.py syncdb
    python manage.py collectstatic
    python manage.py runserver 0.0.0.0:8000