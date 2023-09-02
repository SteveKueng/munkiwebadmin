from django.contrib import admin

from vault.models import localAdmin, passwordAccess

class localAdminAdmin(admin.ModelAdmin):
    list_display = ('machine', 'expireDate')

class passwordAccessAdmin(admin.ModelAdmin):
    list_display = ('machine', 'user', 'reason', 'date')

admin.site.register(localAdmin, localAdminAdmin)
admin.site.register(passwordAccess, passwordAccessAdmin)