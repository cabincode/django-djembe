from django.contrib import admin

from djembe.models import Identity


class IdentityAdmin(admin.ModelAdmin):
    model = Identity
    list_display = ['address', 'fingerprint']
    search_fields = ['address']
admin.site.register(Identity, IdentityAdmin)
