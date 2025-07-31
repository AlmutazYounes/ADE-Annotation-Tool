from django.urls import path
from . import views

urlpatterns = [
    path('', views.annotation_list, name='annotation_list'),
    path('<int:annotation_id>/', views.annotation_list, name='annotation_single'),
    path('edit/<int:annotation_id>/', views.annotation_edit, name='annotation_edit'),
    path('import/', views.import_jsonl, name='import_jsonl'),
    path('export/', views.export_jsonl, name='export_jsonl'),
    path('export-entities/', views.export_entities_jsonl, name='export_entities_jsonl'),
    path('upload-hf/', views.upload_to_huggingface, name='upload_to_huggingface'),
    path('test-hf-token/', views.test_hf_token, name='test_hf_token'),
    path('stats/', views.annotation_stats, name='annotation_stats'),
    path('entity-examples/', views.entity_examples, name='entity_examples'),
    path('entity-examples-page/', views.entity_examples_page, name='entity_examples_page'),
    path('upload-drugs/', views.upload_drug_list, name='upload_drug_list'),
    path('upload-ades/', views.upload_ade_list, name='upload_ade_list'),
]