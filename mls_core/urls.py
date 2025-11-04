"""
URL configuration for MLS Core.
"""

from django.urls import path
from . import views

app_name = 'mls_core'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Security Profiles
    path('profiles/', views.profile_list, name='profile_list'),
    path('profiles/<int:profile_id>/', views.profile_detail, name='profile_detail'),
    path('profiles/<int:profile_id>/edit/', views.profile_edit, name='profile_edit'),
    path('profiles/<int:profile_id>/delete/', views.profile_delete, name='profile_delete'),
    path('profiles/create/select-user/', views.profile_create_select_user, name='profile_create_select_user'),
    path('profiles/create/<int:user_id>/', views.profile_create, name='profile_create'),

    # Security Labels
    path('labels/', views.label_list, name='label_list'),
    path('labels/create/', views.label_create, name='label_create'),
    path('labels/<int:label_id>/edit/', views.label_edit, name='label_edit'),
    path('labels/<int:label_id>/delete/', views.label_delete, name='label_delete'),

    # MLS Groups
    path('mls-groups/', views.mls_group_list, name='mls_group_list'),
    path('mls-groups/create/', views.mls_group_create, name='mls_group_create'),
    path('mls-groups/<int:group_id>/edit/', views.mls_group_edit, name='mls_group_edit'),
    path('mls-groups/<int:group_id>/delete/', views.mls_group_delete, name='mls_group_delete'),

    # DAC Groups
    path('dac-groups/', views.dac_group_list, name='dac_group_list'),
    path('dac-groups/create/', views.dac_group_create, name='dac_group_create'),
    path('dac-groups/<int:group_id>/edit/', views.dac_group_edit, name='dac_group_edit'),
    path('dac-groups/<int:group_id>/delete/', views.dac_group_delete, name='dac_group_delete'),

    # Security Clearances
    path('clearances/', views.clearance_list, name='clearance_list'),
    path('clearances/create/', views.clearance_create, name='clearance_create'),
    path('clearances/<int:clearance_id>/edit/', views.clearance_edit, name='clearance_edit'),
    path('clearances/<int:clearance_id>/delete/', views.clearance_delete, name='clearance_delete'),

    # Classification Helper
    path('classify/', views.classification_helper, name='classification_helper'),
]
