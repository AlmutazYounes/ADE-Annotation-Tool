from django.urls import path
from . import views

urlpatterns = [
    path('', views.annotation_list, name='annotation_list'),
    path('edit/<int:annotation_id>/', views.annotation_edit, name='annotation_edit'),
    path('import/', views.import_jsonl, name='import_jsonl'),
    path('export/', views.export_jsonl, name='export_jsonl'),
    path('export-entities/', views.export_entities_jsonl, name='export_entities_jsonl'),
    path('stats/', views.annotation_stats, name='annotation_stats'),
] 