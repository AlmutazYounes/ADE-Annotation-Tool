from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Max
from .models import TextAnnotation, AnnotationChange, DrugListEntry, ADEListEntry
import json
import re
import requests
from datetime import datetime

# Global sets for uploaded drugs/ADEs, initialized from data
UPLOADED_DRUGS = set(d for ann in TextAnnotation.objects.all() for d in ann.drugs)
UPLOADED_ADES = set(a for ann in TextAnnotation.objects.all() for a in ann.adverse_events)

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
            # Get session ID for tracking
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            
            # Store old values for change tracking
            old_drugs = annotation.drugs.copy()
            old_events = annotation.adverse_events.copy()
            old_validated = annotation.is_validated
            
            # Handle drugs
            if 'drugs' in request.POST:
                drugs_string = request.POST.get('drugs', '')
                annotation.set_drugs_from_string(drugs_string)
                
                # Log drug changes
                if old_drugs != annotation.drugs:
                    # Find added drugs
                    added_drugs = [drug for drug in annotation.drugs if drug not in old_drugs]
                    for drug in added_drugs:
                        AnnotationChange.log_drug_change(
                            annotation, 'drug_added', drug, old_drugs, annotation.drugs, session_id
                        )
                    
                    # Find removed drugs
                    removed_drugs = [drug for drug in old_drugs if drug not in annotation.drugs]
                    for drug in removed_drugs:
                        AnnotationChange.log_drug_change(
                            annotation, 'drug_removed', drug, old_drugs, annotation.drugs, session_id
                        )
            
            # Handle adverse events
            if 'adverse_events' in request.POST:
                events_string = request.POST.get('adverse_events', '')
                annotation.set_adverse_events_from_string(events_string)
                
                # Log event changes
                if old_events != annotation.adverse_events:
                    # Find added events
                    added_events = [event for event in annotation.adverse_events if event not in old_events]
                    for event in added_events:
                        AnnotationChange.log_event_change(
                            annotation, 'event_added', event, old_events, annotation.adverse_events, session_id
                        )
                    
                    # Find removed events
                    removed_events = [event for event in old_events if event not in annotation.adverse_events]
                    for event in removed_events:
                        AnnotationChange.log_event_change(
                            annotation, 'event_removed', event, old_events, annotation.adverse_events, session_id
                        )
            
            # Handle validation status (not tracked)
            new_validated = request.POST.get('is_validated') == 'on'
            if old_validated != new_validated:
                annotation.is_validated = new_validated
            
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
    
    # Get all annotation IDs for slider navigation
    all_annotation_ids = list(TextAnnotation.objects.order_by('id').values_list('id', flat=True))
    
    # Get all unique drugs and ADEs from DB and data
    all_drugs_set = set(d for ann in TextAnnotation.objects.all() for d in ann.drugs)
    all_ades_set = set(a for ann in TextAnnotation.objects.all() for a in ann.adverse_events)
    all_drugs_set.update(d.name for d in DrugListEntry.objects.all())
    all_ades_set.update(a.name for a in ADEListEntry.objects.all())
    all_drugs = sorted(list(all_drugs_set), key=str.lower)
    all_ades = sorted(list(all_ades_set), key=str.lower)

    # Quick add suggestions (Python logic)
    text = annotation.text if annotation else ''
    words = re.findall(r"\b\w[\w\-']*\b", text.lower())
    annotated_drugs = set(d.lower() for d in annotation.drugs)
    annotated_ades = set(a.lower() for a in annotation.adverse_events)
    all_annotated = annotated_drugs | annotated_ades
    def is_not_in_any_entity(word, entities):
        return all(word not in entity for entity in entities)
    quick_drug_suggestions = [w for w in words if w in (d.lower() for d in all_drugs)
                             and w not in annotated_drugs
                             and is_not_in_any_entity(w, all_annotated)]
    quick_ade_suggestions = [w for w in words if w in (a.lower() for a in all_ades)
                            and w not in annotated_ades
                            and is_not_in_any_entity(w, all_annotated)]

    context = {
        'annotation': annotation,
        'prev_annotation': prev_annotation,
        'next_annotation': next_annotation,
        'total_count': total_count,
        'validated_count': validated_count,
        'unvalidated_count': unvalidated_count,
        'current_position': current_position,
        'all_annotation_ids': json.dumps(all_annotation_ids),
        'progress_percentage': int((current_position / total_count) * 100) if total_count > 0 else 0,
        'validation_percentage': int((validated_count / total_count) * 100) if total_count > 0 else 0,
        'all_drugs': all_drugs,
        'all_ades': all_ades,
        'quick_drug_suggestions': quick_drug_suggestions,
        'quick_ade_suggestions': quick_ade_suggestions,
    }
    
    return render(request, 'annotation/list.html', context)


def annotation_edit(request, annotation_id):
    """Redirect to main annotation interface"""
    return redirect('annotation_single', annotation_id=annotation_id)


def import_jsonl(request):
    """View to import data from JSONL file"""
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('jsonl_file')
            
            if not uploaded_file:
                messages.error(request, 'Please select a file to upload.')
                return render(request, 'annotation/import.html', {'current_count': TextAnnotation.objects.count()})
            
            # Validate file extension
            if not uploaded_file.name.lower().endswith(('.jsonl', '.json')):
                messages.error(request, 'Please upload a .jsonl or .json file.')
                return render(request, 'annotation/import.html', {'current_count': TextAnnotation.objects.count()})
            
            with transaction.atomic():
                # Clear existing data if requested
                if request.POST.get('clear_existing'):
                    TextAnnotation.objects.all().delete()
                
                imported_count = 0
                skipped_count = 0
                
                # Read file content
                file_content = uploaded_file.read().decode('utf-8')
                lines = file_content.strip().split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    try:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            annotation = TextAnnotation(
                                text=data.get('text', ''),
                                drugs=data.get('drugs', []),
                                adverse_events=data.get('adverse_events', []),
                                is_validated=data.get('is_validated', False)
                            )
                            annotation.save()
                            imported_count += 1
                    except json.JSONDecodeError as e:
                        skipped_count += 1
                        messages.warning(request, f'Skipped invalid JSON on line {line_num}: {str(e)}')
                    except Exception as e:
                        skipped_count += 1
                        messages.warning(request, f'Error importing line {line_num}: {str(e)}')
                
                # Success message
                success_msg = f'Successfully imported {imported_count} annotations!'
                if skipped_count > 0:
                    success_msg += f' ({skipped_count} lines skipped due to errors)'
                
                messages.success(request, success_msg)
                return redirect('annotation_list')
                
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
    
    context = {
        'current_count': TextAnnotation.objects.count(),
    }
    return render(request, 'annotation/import.html', context)


def export_jsonl(request):
    """View to export data to JSONL format"""
    try:
        # Get filter type from query parameters
        filter_type = request.GET.get('filter', 'all')
        include_changes = request.GET.get('include_changes', 'false').lower() == 'true'
        
        # Start with all annotations
        annotations = TextAnnotation.objects.all()
        
        # Apply filters based on the filter_type
        if filter_type == 'annotated':
            # Only export texts that have drugs or adverse events
            annotations = annotations.exclude(Q(drugs=[]) & Q(adverse_events=[]))
        elif filter_type == 'validated':
            # Only export validated annotations
            annotations = annotations.filter(is_validated=True)
        elif filter_type == 'annotated_validated':
            # Only export texts that are both annotated and validated
            annotations = annotations.exclude(Q(drugs=[]) & Q(adverse_events=[])).filter(is_validated=True)
        elif filter_type == 'modified':
            # Only export texts that have been modified (have changes tracked)
            annotations = annotations.filter(changes__isnull=False).distinct()
        # 'all' or any other value exports everything (default behavior)
        
        # Determine filename based on filter
        filter_names = {
            'annotated': 'annotated_only',
            'validated': 'validated_only', 
            'annotated_validated': 'annotated_validated',
            'modified': 'modified_only',
            'all': 'all'
        }
        filename_suffix = filter_names.get(filter_type, 'all')
        
        # Add changes suffix if including changes
        if include_changes:
            filename_suffix += '_with_changes'
        
        # Create response
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="exported_annotations_{filename_suffix}.jsonl"'
        
        for annotation in annotations:
            data = {
                'text': annotation.text,
                'drugs': annotation.drugs,
                'adverse_events': annotation.adverse_events,
                'is_validated': annotation.is_validated,
                'created_at': annotation.created_at.isoformat() if annotation.created_at else None,
                'updated_at': annotation.updated_at.isoformat() if annotation.updated_at else None,
            }
            
            # Include change tracking data if requested
            if include_changes:
                # Get change summary for this annotation
                change_summary = annotation.get_change_summary()
                # Create JSON-serializable version of change summary
                serializable_change_summary = {
                    'total_changes': change_summary['total_changes'],
                    'drug_additions': change_summary['drug_additions'],
                    'drug_removals': change_summary['drug_removals'],
                    'event_additions': change_summary['event_additions'],
                    'event_removals': change_summary['event_removals'],
                    'last_modified': change_summary['last_modified'].isoformat() if change_summary['last_modified'] else None,
                }
                data['change_summary'] = serializable_change_summary
                
                # Get detailed changes
                changes = []
                for change in annotation.changes.all():
                    changes.append({
                        'change_type': change.change_type,
                        'change_type_display': change.get_change_type_display(),
                        'field_name': change.field_name,
                        'entity_name': change.entity_name,
                        'old_value': change.old_value,
                        'new_value': change.new_value,
                        'timestamp': change.timestamp.isoformat() if change.timestamp else None,
                        'session_id': change.session_id,
                    })
                data['changes'] = changes
                
                # Add aggregated change statistics
                data['change_statistics'] = {
                    'total_changes': change_summary['total_changes'],
                    'drug_additions': change_summary['drug_additions'],
                    'drug_removals': change_summary['drug_removals'],
                    'event_additions': change_summary['event_additions'],
                    'event_removals': change_summary['event_removals'],
                    'total_additions': change_summary['drug_additions'] + change_summary['event_additions'],
                    'total_removals': change_summary['drug_removals'] + change_summary['event_removals'],
                    'last_modified': change_summary['last_modified'].isoformat() if change_summary['last_modified'] else None,
                }
            
            response.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        total_count = TextAnnotation.objects.count()
        exported_count = annotations.count()
        
        if filter_type == 'all':
            messages.success(request, f'Successfully exported all {exported_count} annotations!')
        else:
            messages.success(request, f'Successfully exported {exported_count} {filter_type} annotations out of {total_count} total!')
        
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
        include_changes = request.GET.get('include_changes', 'false').lower() == 'true'
        annotations = TextAnnotation.objects.all()
        
        # Create response
        response = HttpResponse(content_type='application/json')
        filename = 'exported_annotations_entities'
        if include_changes:
            filename += '_with_changes'
        response['Content-Disposition'] = f'attachment; filename="{filename}.jsonl"'
        
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
                'entities': entities,
                'is_validated': annotation.is_validated,
                'created_at': annotation.created_at.isoformat() if annotation.created_at else None,
                'updated_at': annotation.updated_at.isoformat() if annotation.updated_at else None,
            }
            
            # Include change tracking data if requested
            if include_changes:
                # Get change summary for this annotation
                change_summary = annotation.get_change_summary()
                # Create JSON-serializable version of change summary
                serializable_change_summary = {
                    'total_changes': change_summary['total_changes'],
                    'drug_additions': change_summary['drug_additions'],
                    'drug_removals': change_summary['drug_removals'],
                    'event_additions': change_summary['event_additions'],
                    'event_removals': change_summary['event_removals'],
                    'last_modified': change_summary['last_modified'].isoformat() if change_summary['last_modified'] else None,
                }
                data['change_summary'] = serializable_change_summary
                
                # Get detailed changes
                changes = []
                for change in annotation.changes.all():
                    changes.append({
                        'change_type': change.change_type,
                        'change_type_display': change.get_change_type_display(),
                        'field_name': change.field_name,
                        'entity_name': change.entity_name,
                        'old_value': change.old_value,
                        'new_value': change.new_value,
                        'timestamp': change.timestamp.isoformat() if change.timestamp else None,
                        'session_id': change.session_id,
                    })
                data['changes'] = changes
                
                # Add aggregated change statistics
                data['change_statistics'] = {
                    'total_changes': change_summary['total_changes'],
                    'drug_additions': change_summary['drug_additions'],
                    'drug_removals': change_summary['drug_removals'],
                    'event_additions': change_summary['event_additions'],
                    'event_removals': change_summary['event_removals'],
                    'total_additions': change_summary['drug_additions'] + change_summary['event_additions'],
                    'total_removals': change_summary['drug_removals'] + change_summary['event_removals'],
                    'last_modified': change_summary['last_modified'].isoformat() if change_summary['last_modified'] else None,
                }
            
            response.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        messages.success(request, f'Successfully exported {annotations.count()} annotations with entity positions!')
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('annotation_list')


def annotation_stats(request):
    """View to display annotation statistics"""
    total_count = TextAnnotation.objects.count()
    validated_count = TextAnnotation.objects.filter(is_validated=True).count()
    unvalidated_count = total_count - validated_count
    
    # Get drug statistics and single tag type statistics
    all_drugs = []
    only_drug_count = 0
    only_adverse_event_count = 0
    mixed_count = 0

    for annotation in TextAnnotation.objects.all():
        all_drugs.extend(annotation.drugs)

        # Count single tag type annotations
        has_drugs = len(annotation.drugs) > 0
        has_adverse_events = len(annotation.adverse_events) > 0

        if has_drugs and not has_adverse_events:
            only_drug_count += 1
        elif has_adverse_events and not has_drugs:
            only_adverse_event_count += 1
        elif has_drugs and has_adverse_events:
            mixed_count += 1

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
    
    # --- Change statistics ---
    from django.db.models import Count
    change_qs = AnnotationChange.objects.all()
    total_changes = change_qs.count()
    drug_additions = change_qs.filter(change_type='drug_added').count()
    drug_removals = change_qs.filter(change_type='drug_removed').count()
    event_additions = change_qs.filter(change_type='event_added').count()
    event_removals = change_qs.filter(change_type='event_removed').count()
    bulk_updates = change_qs.filter(change_type='bulk_update').count()

    # Most active annotations (by number of changes)
    most_active_annotations = (
        TextAnnotation.objects.annotate(num_changes=Count('changes'))
        .order_by('-num_changes')[:5]
    )

    # Recent changes
    recent_changes = AnnotationChange.objects.select_related('annotation').order_by('-timestamp')[:10]

    context = {
        'total_annotations': total_count,
        'validated_annotations': validated_count,
        'unvalidated_annotations': unvalidated_count,
        'validation_percentage': (validated_count / total_count * 100) if total_count > 0 else 0,
        'top_drugs': sorted(drug_stats.items(), key=lambda x: x[1], reverse=True)[:10],
        'top_events': sorted(event_stats.items(), key=lambda x: x[1], reverse=True)[:10],
        'total_unique_drugs': len(drug_stats),
        'total_unique_events': len(event_stats),
        'total_drugs': len(all_drugs),
        'total_events': len(all_events),
        # Single tag type stats
        'only_drug_count': only_drug_count,
        'only_adverse_event_count': only_adverse_event_count,
        'mixed_count': mixed_count,
        # Change stats
        'total_changes': total_changes,
        'drug_additions': drug_additions,
        'drug_removals': drug_removals,
        'event_additions': event_additions,
        'event_removals': event_removals,
        'bulk_updates': bulk_updates,
        'most_active_annotations': most_active_annotations,
        'recent_changes': recent_changes,
    }
    
    return render(request, 'annotation/stats.html', context)


def entity_examples(request):
    """AJAX endpoint to get examples of a specific entity"""
    entity_name = request.GET.get('entity')
    entity_type = request.GET.get('type')  # 'drug' or 'adverse_event'

    if not entity_name or not entity_type:
        return JsonResponse({'error': 'Missing entity name or type'}, status=400)

    # Filter annotations based on entity type
    # Note: Using Python filtering instead of database filtering for SQLite compatibility
    all_annotations = TextAnnotation.objects.all()
    annotations = []

    for annotation in all_annotations:
        if entity_type == 'drug' and entity_name in annotation.drugs:
            annotations.append(annotation)
        elif entity_type == 'adverse_event' and entity_name in annotation.adverse_events:
            annotations.append(annotation)

    if not annotations:
        return JsonResponse({
            'entity_name': entity_name,
            'entity_type': entity_type,
            'total_count': 0,
            'examples': []
        })

    # Prepare response data
    examples = []
    for annotation in annotations[:20]:  # Limit to 20 examples for performance
        # Highlight the entity in the text
        highlighted_text = highlight_entity_in_text(annotation.text, entity_name)

        examples.append({
            'id': annotation.id,
            'text': annotation.text,
            'highlighted_text': highlighted_text,
            'is_validated': annotation.is_validated,
            'created_at': annotation.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({
        'entity_name': entity_name,
        'entity_type': entity_type,
        'total_count': len(annotations),
        'examples': examples
    })


def highlight_entity_in_text(text, entity_name):
    """Highlight entity occurrences in text with HTML spans"""
    import re

    # Escape special regex characters in entity name
    escaped_entity = re.escape(entity_name)

    # Create pattern for case-insensitive matching with word boundaries
    pattern = r'\b' + escaped_entity + r'\b'

    # Replace with highlighted version
    highlighted = re.sub(
        pattern,
        f'<span class="entity-highlight">{entity_name}</span>',
        text,
        flags=re.IGNORECASE
    )

    return highlighted


def entity_examples_page(request):
    """Dedicated page for displaying entity examples"""
    from django.core.paginator import Paginator

    entity_name = request.GET.get('entity')
    entity_type = request.GET.get('type')
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    page_number = request.GET.get('page', 1)

    # Handle both specific entity examples and single tag type examples
    if not entity_type:
        return redirect('annotation_stats')

    # Filter annotations based on entity type
    all_annotations = TextAnnotation.objects.all()
    matching_annotations = []

    if entity_type in ['only_drug', 'only_adverse_event', 'mixed']:
        # Handle single tag type filtering
        for annotation in all_annotations:
            has_drugs = len(annotation.drugs) > 0
            has_adverse_events = len(annotation.adverse_events) > 0

            if entity_type == 'only_drug' and has_drugs and not has_adverse_events:
                matching_annotations.append(annotation)
            elif entity_type == 'only_adverse_event' and has_adverse_events and not has_drugs:
                matching_annotations.append(annotation)
            elif entity_type == 'mixed' and has_drugs and has_adverse_events:
                matching_annotations.append(annotation)
    else:
        # Handle specific entity filtering (existing functionality)
        if not entity_name:
            return redirect('annotation_stats')

        for annotation in all_annotations:
            if entity_type == 'drug' and entity_name in annotation.drugs:
                matching_annotations.append(annotation)
            elif entity_type == 'adverse_event' and entity_name in annotation.adverse_events:
                matching_annotations.append(annotation)

    # Apply search filter if provided
    if search_query:
        filtered_annotations = []
        for annotation in matching_annotations:
            if search_query.lower() in annotation.text.lower():
                filtered_annotations.append(annotation)
        matching_annotations = filtered_annotations

    # Apply status filter
    if status_filter == 'validated':
        matching_annotations = [a for a in matching_annotations if a.is_validated]
    elif status_filter == 'unvalidated':
        matching_annotations = [a for a in matching_annotations if not a.is_validated]

    # Sort by creation date (newest first)
    matching_annotations.sort(key=lambda x: x.created_at, reverse=True)

    # Pagination
    paginator = Paginator(matching_annotations, 20)  # 20 examples per page
    page_obj = paginator.get_page(page_number)

    # Prepare examples with highlighted text
    examples = []
    for annotation in page_obj:
        if entity_type in ['only_drug', 'only_adverse_event', 'mixed']:
            # For single tag types, highlight all entities of the relevant type(s)
            highlighted_text = annotation.text
            if entity_type == 'only_drug':
                # Highlight all drugs in the sentence
                for drug in annotation.drugs:
                    highlighted_text = highlight_entity_in_text(highlighted_text, drug)
            elif entity_type == 'only_adverse_event':
                # Highlight all adverse events in the sentence
                for event in annotation.adverse_events:
                    highlighted_text = highlight_entity_in_text(highlighted_text, event)
            elif entity_type == 'mixed':
                # Highlight both drugs and adverse events
                for drug in annotation.drugs:
                    highlighted_text = highlight_entity_in_text(highlighted_text, drug)
                for event in annotation.adverse_events:
                    highlighted_text = highlight_entity_in_text(highlighted_text, event)
        else:
            # For specific entity examples, highlight the specific entity
            highlighted_text = highlight_entity_in_text(annotation.text, entity_name)

        examples.append({
            'id': annotation.id,
            'text': annotation.text,
            'highlighted_text': highlighted_text,
            'is_validated': annotation.is_validated,
            'created_at': annotation.created_at,
        })

    # Calculate statistics
    total_count = len(matching_annotations)
    validated_count = sum(1 for a in matching_annotations if a.is_validated)
    unvalidated_count = total_count - validated_count

    # Determine display names and entity name for context
    if entity_type == 'only_drug':
        entity_name_display = 'Only Drug Tags'
        entity_type_display = 'Single Tag Type'
        breadcrumb_name = 'Only Drug Examples'
    elif entity_type == 'only_adverse_event':
        entity_name_display = 'Only Adverse Event Tags'
        entity_type_display = 'Single Tag Type'
        breadcrumb_name = 'Only Adverse Event Examples'
    elif entity_type == 'mixed':
        entity_name_display = 'Mixed Tags'
        entity_type_display = 'Single Tag Type'
        breadcrumb_name = 'Mixed Tag Examples'
    else:
        entity_name_display = entity_name
        entity_type_display = 'Drug' if entity_type == 'drug' else 'Adverse Event'
        breadcrumb_name = f'{entity_type_display} Examples'

    context = {
        'entity_name': entity_name_display,
        'entity_type': entity_type,
        'entity_type_display': entity_type_display,
        'breadcrumb_name': breadcrumb_name,
        'examples': examples,
        'page_obj': page_obj,
        'total_count': total_count,
        'validated_count': validated_count,
        'unvalidated_count': unvalidated_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'has_search': bool(search_query),
        'has_filter': status_filter != 'all',
        'is_single_tag_type': entity_type in ['only_drug', 'only_adverse_event', 'mixed'],
    }

    return render(request, 'annotation/entity_examples.html', context)


def annotation_changes(request, annotation_id=None):
    """View to display change history for annotations"""
    if annotation_id:
        # Show changes for specific annotation
        annotation = get_object_or_404(TextAnnotation, id=annotation_id)
        changes = annotation.changes.all()
        
        # Calculate text differences for this annotation
        text_with_changes = calculate_text_changes(annotation, changes)
        
        # Check if JSON format is requested
        if request.GET.get('format') == 'json':
            # Get change summary
            change_summary = annotation.get_change_summary()
            
            # Prepare changes data for JSON
            changes_data = []
            for change in changes.order_by('-timestamp')[:10]:  # Limit to 10 most recent
                changes_data.append({
                    'change_type': change.change_type,
                    'change_type_display': change.get_change_type_display(),
                    'entity_name': change.entity_name,
                    'field_name': change.field_name,
                    'timestamp': change.timestamp.isoformat() if change.timestamp else None,
                    'session_id': change.session_id,
                })
            
            # Return JSON response
            return JsonResponse({
                'success': True,
                'annotation': {
                    'id': annotation.id,
                    'text': annotation.text,
                    'drugs': annotation.drugs,
                    'adverse_events': annotation.adverse_events,
                    'is_validated': annotation.is_validated,
                },
                'summary': {
                    'total_changes': change_summary['total_changes'],
                    'drug_additions': change_summary['drug_additions'],
                    'drug_removals': change_summary['drug_removals'],
                    'event_additions': change_summary['event_additions'],
                    'event_removals': change_summary['event_removals'],
                    'total_additions': change_summary['drug_additions'] + change_summary['event_additions'],
                    'total_removals': change_summary['drug_removals'] + change_summary['event_removals'],
                    'bulk_updates': changes.filter(change_type='bulk_update').count(),
                },
                'changes': changes_data,
            })
        
        context = {
            'annotation': annotation,
            'changes': changes,
            'text_with_changes': text_with_changes,
            'show_specific': True
        }
    else:
        # Show grouped changes across all annotations
        from django.db.models import Count, Max
        
        # Get filter parameters
        change_type = request.GET.get('change_type')
        
        # Group changes by annotation
        annotations_with_changes = TextAnnotation.objects.filter(
            changes__isnull=False
        ).annotate(
            total_changes=Count('changes'),
            last_change=Max('changes__timestamp')
        ).order_by('-last_change')
        
        # Apply change type filter if specified
        if change_type:
            annotations_with_changes = annotations_with_changes.filter(
                changes__change_type=change_type
            ).distinct()
        
        # Get detailed changes for each annotation
        annotation_summaries = []
        for annotation in annotations_with_changes:
            changes = annotation.changes.all().order_by('-timestamp')
            if change_type:
                changes = changes.filter(change_type=change_type)
            
            # Calculate text differences
            text_with_changes = calculate_text_changes(annotation, changes)
            
            # Group changes by type
            change_summary = {
                'drug_additions': changes.filter(change_type='drug_added').count(),
                'drug_removals': changes.filter(change_type='drug_removed').count(),
                'event_additions': changes.filter(change_type='event_added').count(),
                'event_removals': changes.filter(change_type='event_removed').count(),
                'total_changes': changes.count(),
                'last_change': changes.first().timestamp if changes.exists() else None,
            }
            
            annotation_summaries.append({
                'annotation': annotation,
                'changes': changes,
                'summary': change_summary,
                'text_with_changes': text_with_changes
            })
        
        # Pagination
        paginator = Paginator(annotation_summaries, 20)  # Show 20 annotations per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'annotation_summaries': page_obj,
            'show_specific': False,
            'change_types': AnnotationChange.CHANGE_TYPES,
            'selected_change_type': change_type
        }
    
    return render(request, 'annotation/changes.html', context)


def calculate_text_changes(annotation, changes):
    """Calculate text differences showing added and removed entities"""
    original_text = annotation.text

    # Track all entities that were ever added or removed, and their type
    added_drugs = set()
    added_ades = set()
    removed_drugs = set()
    removed_ades = set()

    for change in changes:
        if change.change_type == 'drug_added' and change.entity_name:
            added_drugs.add(change.entity_name)
        elif change.change_type == 'drug_removed' and change.entity_name:
            removed_drugs.add(change.entity_name)
        elif change.change_type == 'event_added' and change.entity_name:
            added_ades.add(change.entity_name)
        elif change.change_type == 'event_removed' and change.entity_name:
            removed_ades.add(change.entity_name)

    # Convert to sorted lists (longest first)
    removed_drugs = sorted(removed_drugs, key=len, reverse=True)
    removed_ades = sorted(removed_ades, key=len, reverse=True)
    added_drugs = sorted(added_drugs, key=len, reverse=True)
    added_ades = sorted(added_ades, key=len, reverse=True)

    highlighted_text = original_text

    # Highlight removed drugs (crossed out, green)
    for entity in removed_drugs:
        escaped_entity = re.escape(entity)
        pattern = re.compile(escaped_entity, re.IGNORECASE)
        highlighted_text = pattern.sub(f'<span class="removed-drug">{entity}</span>', highlighted_text)
    # Highlight removed ADEs (crossed out, red)
    for entity in removed_ades:
        escaped_entity = re.escape(entity)
        pattern = re.compile(escaped_entity, re.IGNORECASE)
        highlighted_text = pattern.sub(f'<span class="removed-ade">{entity}</span>', highlighted_text)
    # Highlight added drugs (green)
    for entity in added_drugs:
        escaped_entity = re.escape(entity)
        pattern = re.compile(escaped_entity, re.IGNORECASE)
        highlighted_text = pattern.sub(f'<span class="added-drug">{entity}</span>', highlighted_text)
    # Highlight added ADEs (red/pink)
    for entity in added_ades:
        escaped_entity = re.escape(entity)
        pattern = re.compile(escaped_entity, re.IGNORECASE)
        highlighted_text = pattern.sub(f'<span class="added-ade">{entity}</span>', highlighted_text)

    return highlighted_text


def upload_drug_list(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    if request.method == 'POST' and request.FILES.get('drug_file'):
        file = request.FILES['drug_file']
        content = file.read().decode('utf-8')
        added = 0
        for line in content.splitlines():
            drug = line.strip()
            if drug:
                obj, created = DrugListEntry.objects.get_or_create(name=drug)
                if created:
                    added += 1
        messages.success(request, f'Drug list uploaded! {added} new drugs added.')
        return redirect('annotation_list')
    return render(request, 'annotation/upload_drugs.html')

def upload_ade_list(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    if request.method == 'POST' and request.FILES.get('ade_file'):
        file = request.FILES['ade_file']
        content = file.read().decode('utf-8')
        added = 0
        for line in content.splitlines():
            ade = line.strip()
            if ade:
                obj, created = ADEListEntry.objects.get_or_create(name=ade)
                if created:
                    added += 1
        messages.success(request, f'ADE list uploaded! {added} new ADEs added.')
        return redirect('annotation_list')
    return render(request, 'annotation/upload_ades.html')

def export_change_statistics(request):
    """View to export change tracking statistics"""
    try:
        from django.db.models import Count, Q
        
        # Get overall change statistics
        change_qs = AnnotationChange.objects.all()
        total_changes = change_qs.count()
        drug_additions = change_qs.filter(change_type='drug_added').count()
        drug_removals = change_qs.filter(change_type='drug_removed').count()
        event_additions = change_qs.filter(change_type='event_added').count()
        event_removals = change_qs.filter(change_type='event_removed').count()
        bulk_updates = change_qs.filter(change_type='bulk_update').count()
        
        # Get most active annotations
        most_active_annotations = (
            TextAnnotation.objects.annotate(num_changes=Count('changes'))
            .filter(changes__isnull=False)
            .order_by('-num_changes')[:20]
        )
        
        # Get recent changes
        recent_changes = AnnotationChange.objects.select_related('annotation').order_by('-timestamp')[:50]
        
        # Get change statistics by date
        from django.utils import timezone
        from datetime import timedelta
        
        # Last 30 days of changes
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_changes_30d = change_qs.filter(timestamp__gte=thirty_days_ago)
        
        # Last 7 days of changes
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_changes_7d = change_qs.filter(timestamp__gte=seven_days_ago)
        
        # Create statistics data
        statistics_data = {
            'export_timestamp': timezone.now().isoformat(),
            'overall_statistics': {
                'total_changes': total_changes,
                'drug_additions': drug_additions,
                'drug_removals': drug_removals,
                'event_additions': event_additions,
                'event_removals': event_removals,
                'bulk_updates': bulk_updates,
                'total_additions': drug_additions + event_additions,
                'total_removals': drug_removals + event_removals,
            },
            'recent_activity': {
                'changes_last_7_days': recent_changes_7d.count(),
                'changes_last_30_days': recent_changes_30d.count(),
            },
            'most_active_annotations': [
                {
                    'annotation_id': ann.id,
                    'text_preview': ann.text[:100] + '...' if len(ann.text) > 100 else ann.text,
                    'total_changes': ann.num_changes,
                    'drug_additions': ann.changes.filter(change_type='drug_added').count(),
                    'drug_removals': ann.changes.filter(change_type='drug_removed').count(),
                    'event_additions': ann.changes.filter(change_type='event_added').count(),
                    'event_removals': ann.changes.filter(change_type='event_removed').count(),
                    'last_modified': ann.changes.order_by('-timestamp').first().timestamp.isoformat() if ann.changes.exists() else None,
                }
                for ann in most_active_annotations
            ],
            'recent_changes': [
                {
                    'annotation_id': change.annotation.id,
                    'change_type': change.change_type,
                    'change_type_display': change.get_change_type_display(),
                    'entity_name': change.entity_name,
                    'field_name': change.field_name,
                    'timestamp': change.timestamp.isoformat(),
                    'session_id': change.session_id,
                }
                for change in recent_changes
            ],
            'change_type_breakdown': {
                'drug_added': drug_additions,
                'drug_removed': drug_removals,
                'event_added': event_additions,
                'event_removed': event_removals,
                'bulk_update': bulk_updates,
            }
        }
        
        # Create response
        response = HttpResponse(
            json.dumps(statistics_data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="change_tracking_statistics.json"'
        
        messages.success(request, f'Successfully exported change tracking statistics!')
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting change statistics: {str(e)}')
        return redirect('annotation_stats')


def upload_to_huggingface(request):
    """View to upload dataset to Hugging Face Hub"""
    if request.method == 'POST':
        try:
            # Get form data
            hf_token = request.POST.get('hf_token')
            dataset_name = request.POST.get('dataset_name')
            dataset_description = request.POST.get('dataset_description', '')
            is_private = request.POST.get('is_private') == 'on'
            filter_type = request.POST.get('filter_type', 'all')
            
            if not hf_token:
                messages.error(request, 'Hugging Face token is required!')
                return redirect('annotation_stats')
            
            if not dataset_name:
                messages.error(request, 'Dataset name is required!')
                return redirect('annotation_stats')
            
            # Validate dataset name format
            if not re.match(r'^[a-zA-Z0-9_-]+$', dataset_name):
                messages.error(request, 'Dataset name can only contain letters, numbers, underscores, and hyphens!')
                return redirect('annotation_stats')
            
            # Get annotations based on filter
            if filter_type == 'annotated':
                annotations = TextAnnotation.objects.filter(drugs__isnull=False, adverse_events__isnull=False).exclude(drugs=[], adverse_events=[])
            elif filter_type == 'validated':
                annotations = TextAnnotation.objects.filter(is_validated=True)
            else:  # all
                annotations = TextAnnotation.objects.all()
            
            # Prepare dataset data
            dataset_data = []
            for annotation in annotations:
                data = {
                    'id': annotation.id,
                    'text': annotation.text,
                    'drugs': annotation.drugs,
                    'adverse_events': annotation.adverse_events,
                    'is_validated': annotation.is_validated,
                    'created_at': annotation.created_at.isoformat() if annotation.created_at else None,
                    'updated_at': annotation.updated_at.isoformat() if annotation.updated_at else None,
                }
                dataset_data.append(data)
            
            # Create dataset info
            dataset_info = {
                'dataset_name': dataset_name,
                'description': dataset_description or f'Medical text annotation dataset with {len(dataset_data)} examples',
                'upload_timestamp': datetime.now().isoformat(),
                'total_examples': len(dataset_data),
                'filter_type': filter_type,
                'is_private': is_private,
                'validated_count': sum(1 for item in dataset_data if item['is_validated']),
                'unvalidated_count': sum(1 for item in dataset_data if not item['is_validated']),
            }
            
            # Prepare files for upload
            files = {
                'data.jsonl': ('data.jsonl', '\n'.join(json.dumps(item, ensure_ascii=False) for item in dataset_data), 'application/jsonl'),
                'dataset_info.json': ('dataset_info.json', json.dumps(dataset_info, ensure_ascii=False, indent=2), 'application/json'),
                'README.md': ('README.md', f'''# {dataset_name}

{dataset_description or f'Medical text annotation dataset with {len(dataset_data)} examples'}

## Dataset Information
- **Total Examples**: {len(dataset_data)}
- **Validated Examples**: {dataset_info['validated_count']}
- **Unvalidated Examples**: {dataset_info['unvalidated_count']}
- **Filter Type**: {filter_type}
- **Privacy**: {'Private' if is_private else 'Public'}
- **Upload Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Format
Each example contains:
- `id`: Annotation ID
- `text`: Medical text content
- `drugs`: List of identified drugs
- `adverse_events`: List of identified adverse events
- `is_validated`: Validation status
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Usage
This dataset can be used for training medical text annotation models or for research in pharmacovigilance and medical text analysis.
''', 'text/markdown')
            }
            
            # First, try to get user info to validate token
            try:
                # Debug: Log the token (first few characters only)
                token_preview = hf_token[:8] + "..." if len(hf_token) > 8 else hf_token
                print(f"Attempting to validate token: {token_preview}")
                
                user_info_response = requests.get(
                    'https://huggingface.co/api/whoami',
                    headers={'Authorization': f'Bearer {hf_token}'},
                    timeout=10
                )
                
                print(f"Token validation response status: {user_info_response.status_code}")
                print(f"Token validation response: {user_info_response.text[:200]}...")
                
                if user_info_response.status_code != 200:
                    error_detail = user_info_response.text
                    if '401' in str(user_info_response.status_code):
                        messages.error(request, 'Invalid Hugging Face token. Please check your token and try again.')
                    else:
                        messages.error(request, f'Error validating token: {error_detail}')
                    return redirect('annotation_stats')
                
                user_info = user_info_response.json()
                username = user_info.get('name', '')
                
                print(f"Retrieved username: {username}")
                
                if not username:
                    messages.error(request, 'Could not retrieve username from token. Please check your token.')
                    return redirect('annotation_stats')
                    
            except requests.exceptions.RequestException as e:
                print(f"Network error during token validation: {str(e)}")
                messages.error(request, f'Network error while validating token: {str(e)}')
                return redirect('annotation_stats')
            
            # Create dataset repository using the correct API endpoint
            create_url = f'https://huggingface.co/api/repos/create'
            create_data = {
                'name': dataset_name,
                'type': 'dataset',
                'description': dataset_info['description'],
                'private': is_private
            }
            
            create_response = requests.post(
                create_url, 
                headers={'Authorization': f'Bearer {hf_token}'}, 
                json=create_data
            )
            
            if create_response.status_code not in [200, 201, 409]:  # 409 means already exists
                error_msg = create_response.text
                if 'already exists' in error_msg.lower():
                    messages.error(request, f'Dataset "{dataset_name}" already exists. Please choose a different name.')
                else:
                    messages.error(request, f'Failed to create dataset repository: {error_msg}')
                return redirect('annotation_stats')
            
            # Upload files using the datasets API
            upload_url = f'https://huggingface.co/api/datasets/{username}/{dataset_name}/upload'
            
            # Prepare multipart form data
            import io
            from urllib.parse import urlencode
            
            # Create a custom multipart encoder
            boundary = '----WebKitFormBoundary' + ''.join([str(ord(c)) for c in 'abcdefghijklmnop'])
            
            body = []
            for field_name, (filename, content, content_type) in files.items():
                body.append(f'--{boundary}'.encode())
                body.append(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode())
                body.append(f'Content-Type: {content_type}'.encode())
                body.append(b''.encode())
                body.append(content.encode('utf-8'))
                body.append(b'')
            
            body.append(f'--{boundary}--'.encode())
            body.append(b'')
            
            upload_headers = {
                'Authorization': f'Bearer {hf_token}',
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            
            upload_response = requests.post(
                upload_url,
                headers=upload_headers,
                data=b'\r\n'.join(body)
            )
            
            if upload_response.status_code in [200, 201]:
                dataset_url = f'https://huggingface.co/datasets/{username}/{dataset_name}'
                privacy_status = 'private' if is_private else 'public'
                messages.success(request, f'Successfully uploaded {privacy_status} dataset to Hugging Face! View it at: {dataset_url}')
            else:
                messages.error(request, f'Failed to upload dataset: {upload_response.text}')
            
        except Exception as e:
            messages.error(request, f'Error uploading to Hugging Face: {str(e)}')
        
        return redirect('annotation_stats')
    
    # GET request - show upload form
    return render(request, 'annotation/upload_hf.html')


def test_hf_token(request):
    """Test endpoint to validate Hugging Face token"""
    if request.method == 'POST':
        hf_token = request.POST.get('hf_token')
        if not hf_token:
            return JsonResponse({'success': False, 'error': 'No token provided'})
        
        try:
            # Test the token
            response = requests.get(
                'https://huggingface.co/api/whoami',
                headers={'Authorization': f'Bearer {hf_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                username = user_info.get('name', '')
                return JsonResponse({
                    'success': True, 
                    'username': username,
                    'message': f'Token is valid for user: {username}'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Token validation failed: {response.status_code} - {response.text}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error testing token: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'POST method required'})
