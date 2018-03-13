"""
WSGI config for munkiwebadmin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

cert = os.path.join('/usr/local/share/ca-certificates','ca-certificates.crt')
if os.path.exists(cert):
    os.environ['REQUESTS_CA_BUNDLE'] = cert

os.environ['http_proxy'] = os.getenv('PROXY_ADDRESS')
os.environ['https_proxy'] = os.getenv('PROXY_ADDRESS')
os.environ['no_proxy'] = os.getenv('NO_PROXY')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "munkiwebadmin.settings")

application = get_wsgi_application()
