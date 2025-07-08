from django.urls import path
from . import views

urlpatterns = [
    path('', views.annotation_list, name='annotation_list'),
    path('<int:annotation_id>/', views.annotation_list, name='annotation_single'),
    path('edit/<int:annotation_id>/', views.annotation_edit, name='annotation_edit'),
    path('import/', views.import_jsonl, name='import_jsonl'),
    path('export/', views.export_jsonl, name='export_jsonl'),
    path('export-entities/', views.export_entities_jsonl, name='export_entities_jsonl'),
    path('stats/', views.annotation_stats, name='annotation_stats'),
    path('changes/', views.annotation_changes, name='annotation_changes'),
    path('changes/<int:annotation_id>/', views.annotation_changes, name='annotation_changes_specific'),
    path('upload-drugs/', views.upload_drug_list, name='upload_drug_list'),
    path('upload-ades/', views.upload_ade_list, name='upload_ade_list'),
] 