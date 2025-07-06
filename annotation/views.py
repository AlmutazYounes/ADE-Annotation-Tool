from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from .models import TextAnnotation
import json


def annotation_list(request):
    """View to display list of all annotations with pagination"""
    annotations = TextAnnotation.objects.all()
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        annotations = annotations.filter(text__icontains=search_query)
    
    # Add filtering by validation status
    status_filter = request.GET.get('status', '')
    if status_filter == 'validated':
        annotations = annotations.filter(is_validated=True)
    elif status_filter == 'unvalidated':
        annotations = annotations.filter(is_validated=False)
    
    # Pagination
    paginator = Paginator(annotations, 10)  # Show 10 annotations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_count': annotations.count(),
        'validated_count': TextAnnotation.objects.filter(is_validated=True).count(),
        'unvalidated_count': TextAnnotation.objects.filter(is_validated=False).count(),
    }
    
    return render(request, 'annotation/list.html', context)


def annotation_edit(request, annotation_id):
    """View to edit a specific annotation"""
    annotation = get_object_or_404(TextAnnotation, id=annotation_id)
    
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.POST.get('ajax') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Update the annotation
        if 'text' in request.POST:
            annotation.text = request.POST.get('text', '')
        
        # Handle drugs
        if 'drugs' in request.POST:
            drugs_string = request.POST.get('drugs', '')
            annotation.set_drugs_from_string(drugs_string)
        
        # Handle adverse events
        if 'adverse_events' in request.POST:
            events_string = request.POST.get('adverse_events', '')
            annotation.set_adverse_events_from_string(events_string)
        
        # Handle validation status
        annotation.is_validated = request.POST.get('is_validated') == 'on'
        
        try:
            annotation.save()
            
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Annotation updated successfully!'})
            
            messages.success(request, 'Annotation updated successfully!')
            
            # Check if user wants to go to next annotation
            if 'save_and_next' in request.POST:
                next_annotation = TextAnnotation.objects.filter(id__gt=annotation.id).first()
                if next_annotation:
                    return redirect('annotation_edit', annotation_id=next_annotation.id)
                else:
                    messages.info(request, 'No more annotations to edit.')
                    return redirect('annotation_list')
            
            return redirect('annotation_edit', annotation_id=annotation.id)
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'message': f'Error saving annotation: {str(e)}'})
            messages.error(request, f'Error saving annotation: {str(e)}')
    
    # Get navigation info
    prev_annotation = TextAnnotation.objects.filter(id__lt=annotation.id).last()
    next_annotation = TextAnnotation.objects.filter(id__gt=annotation.id).first()
    
    context = {
        'annotation': annotation,
        'prev_annotation': prev_annotation,
        'next_annotation': next_annotation,
    }
    
    return render(request, 'annotation/edit.html', context)


def import_jsonl(request):
    """View to import data from JSONL file"""
    if request.method == 'POST':
        try:
            file_path = request.POST.get('file_path', 'extracted_data.jsonl')
            
            with transaction.atomic():
                # Clear existing data if requested
                if request.POST.get('clear_existing'):
                    TextAnnotation.objects.all().delete()
                
                imported_count = 0
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line_num, line in enumerate(file, 1):
                        try:
                            line = line.strip()
                            if line:
                                data = json.loads(line)
                                annotation = TextAnnotation(
                                    text=data.get('text', ''),
                                    drugs=data.get('drugs', []),
                                    adverse_events=data.get('adverse_events', [])
                                )
                                annotation.save()
                                imported_count += 1
                        except json.JSONDecodeError as e:
                            messages.warning(request, f'Skipped invalid JSON on line {line_num}: {str(e)}')
                        except Exception as e:
                            messages.warning(request, f'Error importing line {line_num}: {str(e)}')
                
                messages.success(request, f'Successfully imported {imported_count} annotations!')
                return redirect('annotation_list')
                
        except FileNotFoundError:
            messages.error(request, f'File not found: {file_path}')
        except Exception as e:
            messages.error(request, f'Error importing file: {str(e)}')
    
    context = {
        'current_count': TextAnnotation.objects.count(),
    }
    return render(request, 'annotation/import.html', context)


def export_jsonl(request):
    """View to export data to JSONL format"""
    try:
        annotations = TextAnnotation.objects.all()
        
        # Create response
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="exported_annotations.jsonl"'
        
        for annotation in annotations:
            data = {
                'text': annotation.text,
                'drugs': annotation.drugs,
                'adverse_events': annotation.adverse_events
            }
            response.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        messages.success(request, f'Successfully exported {annotations.count()} annotations!')
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('annotation_list')


def export_entities_jsonl(request):
    """View to export data to JSONL format with entities (character positions)"""
    def find_entity_positions(text, entity_name):
        """Find all positions of an entity in text"""
        positions = []
        start = 0
        while True:
            pos = text.lower().find(entity_name.lower(), start)
            if pos == -1:
                break
            positions.append((pos, pos + len(entity_name)))
            start = pos + 1
        return positions
    
    try:
        annotations = TextAnnotation.objects.all()
        
        # Create response
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="exported_annotations_entities.jsonl"'
        
        for annotation in annotations:
            entities = []
            
            # Add drug entities
            for drug in annotation.drugs:
                positions = find_entity_positions(annotation.text, drug)
                for start, end in positions:
                    entities.append({
                        "start": start,
                        "end": end,
                        "label": "DRUG"
                    })
            
            # Add adverse event entities
            for event in annotation.adverse_events:
                positions = find_entity_positions(annotation.text, event)
                for start, end in positions:
                    entities.append({
                        "start": start,
                        "end": end,
                        "label": "ADE"
                    })
            
            # Sort entities by start position
            entities.sort(key=lambda x: x['start'])
            
            data = {
                'text': annotation.text,
                'entities': entities
            }
            response.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        messages.success(request, f'Successfully exported {annotations.count()} annotations in entities format!')
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('annotation_list')


def annotation_stats(request):
    """View to show annotation statistics"""
    total_annotations = TextAnnotation.objects.count()
    validated_annotations = TextAnnotation.objects.filter(is_validated=True).count()
    
    # Statistics about entities
    drug_stats = {}
    event_stats = {}
    
    for annotation in TextAnnotation.objects.all():
        for drug in annotation.drugs:
            drug_stats[drug] = drug_stats.get(drug, 0) + 1
        for event in annotation.adverse_events:
            event_stats[event] = event_stats.get(event, 0) + 1
    
    # Sort by frequency
    top_drugs = sorted(drug_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    top_events = sorted(event_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    
    context = {
        'total_annotations': total_annotations,
        'validated_annotations': validated_annotations,
        'validation_percentage': (validated_annotations / total_annotations * 100) if total_annotations > 0 else 0,
        'top_drugs': top_drugs,
        'top_events': top_events,
        'total_unique_drugs': len(drug_stats),
        'total_unique_events': len(event_stats),
    }
    
    return render(request, 'annotation/stats.html', context)
