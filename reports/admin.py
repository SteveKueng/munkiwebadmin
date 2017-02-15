from django.contrib import admin
from reports.models import Machine, MunkiReport, BusinessUnit, ImagrReport

class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('hash', 'name')

class MachineAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'username')

class MunkiReportAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'timestamp', 'errors', 'warnings')

class ImagrReportAdmin(admin.ModelAdmin):
    list_display = ('machine', 'status', 'message', 'date_added')

admin.site.register(BusinessUnit, BusinessUnitAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(MunkiReport, MunkiReportAdmin)
admin.site.register(ImagrReport, ImagrReportAdmin)
