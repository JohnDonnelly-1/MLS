from django.contrib import admin
from django.apps import apps
from django.conf import settings

# Register your models here.


if settings.DEBUG == True:
    models = apps.get_models()

   #ListAdminMixin causes all fields to be displayed in the admin 
    class ListAdminMixin(object):
        def __init__(self, model, admin_site):
            self.list_display = [field.name for field in model._meta.fields]
            super(ListAdminMixin, self).__init__(model, admin_site)

    #Registers all models in the entire database
    for model in models:
        admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
        try:
            admin.site.register(model, admin_class)
        except admin.sites.AlreadyRegistered:
            pass