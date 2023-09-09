from django.contrib import admin
from reports.models import Machine, MunkiReport

class MachineAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'username')

class MunkiReportAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'timestamp', 'errors', 'warnings')

admin.site.register(Machine, MachineAdmin)
admin.site.register(MunkiReport, MunkiReportAdmin)
