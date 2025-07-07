from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from .models import TextAnnotation
import json


def annotation_list(request, annotation_id=None):
    """Main annotation interface - shows one annotation at a time"""
    
    # Get the specific annotation or find the first unvalidated one
    if annotation_id:
        annotation = get_object_or_404(TextAnnotation, id=annotation_id)
    else:
        # Get first unvalidated annotation, or first annotation if all are validated
        annotation = TextAnnotation.objects.filter(is_validated=False).first()
        if not annotation:
            annotation = TextAnnotation.objects.first()
        
        if annotation:
            return redirect('annotation_single', annotation_id=annotation.id)
    
    # Handle form submission (AJAX and regular)
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
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
            
            annotation.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': 'Annotation updated successfully!',
                    'drugs': annotation.drugs,
                    'adverse_events': annotation.adverse_events,
                    'is_validated': annotation.is_validated
                })
            
            messages.success(request, 'Annotation updated successfully!')
            
            # Check if user wants to go to next annotation
            if 'save_and_next' in request.POST:
                next_annotation = TextAnnotation.objects.filter(id__gt=annotation.id).first()
                if next_annotation:
                    return redirect('annotation_single', annotation_id=next_annotation.id)
                else:
                    messages.info(request, 'No more annotations to edit.')
                    return redirect('annotation_single', annotation_id=annotation.id)
            
            return redirect('annotation_single', annotation_id=annotation.id)
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'message': f'Error saving annotation: {str(e)}'})
            messages.error(request, f'Error saving annotation: {str(e)}')
    
    # If no annotations exist, show empty state
    if not annotation:
        context = {
            'no_annotations': True,
            'total_count': 0,
            'validated_count': 0,
            'unvalidated_count': 0,
        }
        return render(request, 'annotation/list.html', context)
    
    # Get navigation info
    prev_annotation = TextAnnotation.objects.filter(id__lt=annotation.id).last()
    next_annotation = TextAnnotation.objects.filter(id__gt=annotation.id).first()
    
    # Get statistics
    total_count = TextAnnotation.objects.count()
    validated_count = TextAnnotation.objects.filter(is_validated=True).count()
    unvalidated_count = total_count - validated_count
    
    # Get current position
    current_position = TextAnnotation.objects.filter(id__lte=annotation.id).count()
    
    context = {
        'annotation': annotation,
        'prev_annotation': prev_annotation,
        'next_annotation': next_annotation,
        'total_count': total_count,
        'validated_count': validated_count,
        'unvalidated_count': unvalidated_count,
        'current_position': current_position,
        'progress_percentage': int((current_position / total_count) * 100) if total_count > 0 else 0,
        'validation_percentage': int((validated_count / total_count) * 100) if total_count > 0 else 0,
    }
    
    return render(request, 'annotation/list.html', context)


def annotation_edit(request, annotation_id):
    """Redirect to main annotation interface"""
    return redirect('annotation_single', annotation_id=annotation_id)


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
                        "label": "DRUG",
                        "text": drug
                    })
            
            # Add adverse event entities
            for event in annotation.adverse_events:
                positions = find_entity_positions(annotation.text, event)
                for start, end in positions:
                    entities.append({
                        "start": start,
                        "end": end,
                        "label": "ADVERSE_EVENT", 
                        "text": event
                    })
            
            data = {
                'text': annotation.text,
                'entities': entities
            }
            response.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting entities: {str(e)}')
        return redirect('annotation_list')


def annotation_stats(request):
    """View to display annotation statistics"""
    total_count = TextAnnotation.objects.count()
    validated_count = TextAnnotation.objects.filter(is_validated=True).count()
    unvalidated_count = total_count - validated_count
    
    # Get drug statistics
    all_drugs = []
    for annotation in TextAnnotation.objects.all():
        all_drugs.extend(annotation.drugs)
    
    drug_stats = {}
    for drug in all_drugs:
        drug_stats[drug] = drug_stats.get(drug, 0) + 1
    
    # Get adverse event statistics
    all_events = []
    for annotation in TextAnnotation.objects.all():
        all_events.extend(annotation.adverse_events)
    
    event_stats = {}
    for event in all_events:
        event_stats[event] = event_stats.get(event, 0) + 1
    
    context = {
        'total_count': total_count,
        'validated_count': validated_count,
        'unvalidated_count': unvalidated_count,
        'validation_percentage': int((validated_count / total_count) * 100) if total_count > 0 else 0,
        'drug_stats': sorted(drug_stats.items(), key=lambda x: x[1], reverse=True)[:10],
        'event_stats': sorted(event_stats.items(), key=lambda x: x[1], reverse=True)[:10],
        'unique_drugs': len(drug_stats),
        'unique_events': len(event_stats),
        'total_drugs': len(all_drugs),
        'total_events': len(all_events),
    }
    
    return render(request, 'annotation/stats.html', context)
