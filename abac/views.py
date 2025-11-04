from django.shortcuts import HttpResponse, get_object_or_404, HttpResponseRedirect
from django.template.response import TemplateResponse
from .models import FakeUser, Object
# TemplateResponse is recommended over render
### REFERENCES ###
# https://spookylukey.github.io/django-views-the-right-way/the-pattern.html
### ###
def index(request):
    return TemplateResponse(request, template="abac/base.html", context=None)

def user(request, pk):
    user = FakeUser.objects.get(pk=pk)
    return TemplateResponse(request, template="abac/user.html", context={'user':user})

def user_list(request):
    users = FakeUser.objects.all().prefetch_related('accesses__securities')
    return TemplateResponse(request, template="abac/users.html", context={'users':users})

def object_list(request):
    objs = Object.objects.all()
    return TemplateResponse(
            request, 
            template="abac/objects.html", 
            context={'objs':objs})

def item(request, pk):
    obj = get_object_or_404(Object, pk=pk)
    return TemplateResponse(request, template="abac/object.html", context={'obj':obj})