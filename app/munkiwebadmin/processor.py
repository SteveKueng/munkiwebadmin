from django.conf import settings
from django.templatetags.static import static
import base64

# get settings
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

try:
    REPO_MANAGEMENT_ONLY = settings.REPO_MANAGEMENT_ONLY
except:
    REPO_MANAGEMENT_ONLY = False

def index(request):
    try:
        image = request.user.ldap_user.attrs["thumbnailPhoto"]
        imgString = "data:image/png;base64,"+base64.b64encode(image[0])
    except:
        imgString = static('img/placeholder.jpg')
        pass

    return {'REPO_MANAGEMENT_ONLY': REPO_MANAGEMENT_ONLY, 'APPNAME': APPNAME, 'HOSTNAME': HOSTNAME, 'userImage': imgString }

