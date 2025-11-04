from django.contrib import admin
from django.urls import path, include

from . import views

app_name = "abac"
urlpatterns = [
    path('', views.user_list, name='users'),
    path('user/<int:pk>/', views.user, name='user'),
    path('objects/', views.object_list, name='objects'),
    path('object/<int:pk>/', views.item, name='object'),
]
