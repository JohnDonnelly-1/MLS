from django.urls import path

from . import views

app_name = 'wiki'

urlpatterns = [
    path('', views.wiki_home, name='home'),
    path('search/', views.search, name='search'),

    path('spaces/', views.space_list, name='space_list'),
    path('spaces/new/', views.space_create, name='space_create'),

    path('attachments/<int:attachment_id>/download/', views.attachment_download, name='attachment_download'),
    path('attachments/<int:attachment_id>/delete/', views.attachment_delete, name='attachment_delete'),

    path('<slug:space_key>/', views.space_detail, name='space_detail'),
    path('<slug:space_key>/new/', views.page_create, name='page_create'),
    path('<slug:space_key>/<slug:page_slug>/', views.page_detail, name='page_detail'),
    path('<slug:space_key>/<slug:page_slug>/edit/', views.page_edit, name='page_edit'),
    path('<slug:space_key>/<slug:page_slug>/delete/', views.page_delete, name='page_delete'),
    path('<slug:space_key>/<slug:page_slug>/attach/', views.attachment_upload, name='attachment_upload'),
    path('<slug:space_key>/<slug:page_slug>/history/', views.page_history, name='page_history'),
    path('<slug:space_key>/<slug:page_slug>/history/<int:version>/', views.page_revision_detail, name='page_revision_detail'),
    path('<slug:space_key>/<slug:page_slug>/compare/<int:from_version>/<int:to_version>/', views.page_diff, name='page_diff'),
    path('<slug:space_key>/<slug:page_slug>/restore/<int:version>/', views.page_restore, name='page_restore'),
]
