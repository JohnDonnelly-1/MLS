from django.shortcuts import render, HttpResponse, get_object_or_404, HttpResponseRedirect
from django.template.response import TemplateResponse

def index(request):
    return TemplateResponse(request, template="main/base.html", context=None)