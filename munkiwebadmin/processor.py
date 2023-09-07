from django.conf import settings
from django.templatetags.static import static
import base64

# get settings
try:
    STYLE = settings.STYLE
except:
    STYLE = 'default'

try:
    APPNAME = settings.APPNAME
except:
    APPNAME = "MunkiWebAdmin"

try:
    BASE_DIR = settings.BASE_DIR
except:
    BASE_DIR = ""

try:
    HOSTNAME = settings.HOSTNAME
except:
    HOSTNAME = "localhost"

def index(request):
    try:
        image = request.user.ldap_user.attrs["thumbnailPhoto"]
        imgString = "data:image/png;base64,"+base64.b64encode(image[0])
    except:
        imgString = static('img/placeholder.jpg')
        pass

    return {'style': STYLE, 'APPNAME': APPNAME, 'HOSTNAME': HOSTNAME, 'userImage': imgString }

