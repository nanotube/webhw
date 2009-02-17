from django.conf import settings
from django.http import HttpResponseRedirect
import re

MAINTENANCE_MODE = getattr(settings, 'MAINTENANCE_MODE', False)
MAINTENANCE_PATH = getattr(settings, 'MAINTENANCE_PATH', '/maintenance/')
class MaintenanceMiddleware(object):
    def process_request(self, request):
        
        if not MAINTENANCE_MODE:
            return None
        
        # Allow acess if the user doing the request is logged in and a
        # staff member.
        if hasattr(request, 'user') and request.user.is_staff:
            return None
        
        # Allow staff members to log in to the admin
        # assuming all admin stuff is under /admin
        if hasattr(request, 'path') and (re.match(r'/admin', request.path) or re.match(r'^'+MAINTENANCE_PATH+'$', request.path)):
            return None
        
        return HttpResponseRedirect(MAINTENANCE_PATH)
        