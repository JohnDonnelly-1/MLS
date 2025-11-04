# Use
* Install virtualenv/pipenv/
* `django-admin startproject --template https://github.com/alkelaun/project_name/archive/refs/heads/master.zip $NEW_PROJECT_NAME .`

# What it does
creating a start project template

1. Changed Timezone in Settings
2. Added "main" app 
3. Included "main" app in Settings
4. Registered all models in the django admin if settings.DEBUG == True (see excerpt 1)
5. 



#################### Excerpt 1 ######################


https://docs.djangoproject.com/en/4.0/topics/settings/#using-settings-in-python-code


```
from django.contrib import admin
from django.apps import apps
from django.conf import settings

# Register your models here.


if settings.DEBUG:
    models = apps.get_models()

    '''
    ListAdminMixin causes all fields to be displayed in the admin 
    Do not need 'def str(self): pass' to be defined
    '''
    class ListAdminMixin(object):
        def __init__(self, model, admin_site):
            self.list_display = [field.name for field in model._meta.fields]
            super(ListAdminMixin, self).__init__(model, admin_site)

    '''
    Registers all models in the entire database
    '''
    for model in models:
        admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
        try:
            admin.site.register(model, admin_class)
        except admin.sites.AlreadyRegistered:
            pass
```

#################### Excerpt 1 ######################
