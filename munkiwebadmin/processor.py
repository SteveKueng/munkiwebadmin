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
    REPO_MANAGEMENT_ONLY = settings.REPO_MANAGEMENT_ONLY
except:
    REPO_MANAGEMENT_ONLY = False

try:
    ENTRA_ONLY = settings.ENTRA_ONLY
except:
    ENTRA_ONLY = False

try:
    TENANT_ID = settings.TENANT_ID
except:
    TENANT_ID = None

def index(request):
    imgString = static('img/placeholder.jpg')
    try:   
        image = request.user.ldap_user.attrs["thumbnailPhoto"]
        imgString = "data:image/png;base64,"+base64.b64encode(image[0])
    except:
        pass

    return {'REPO_MANAGEMENT_ONLY': REPO_MANAGEMENT_ONLY, 'ENTRA_ONLY': ENTRA_ONLY, 'TENANT_ID': TENANT_ID, 'APPNAME': APPNAME, 'userImage': imgString }

