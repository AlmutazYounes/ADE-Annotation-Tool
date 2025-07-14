from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Max
from .models import TextAnnotation, AnnotationChange, DrugListEntry, ADEListEntry
import json
import re

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
        
        # Create response
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="exported_annotations_{filename_suffix}.jsonl"'
        
        for annotation in annotations:
            data = {
                'text': annotation.text,
                'drugs': annotation.drugs,
                'adverse_events': annotation.adverse_events,
                'is_validated': annotation.is_validated
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
                'entities': entities,
                'is_validated': annotation.is_validated
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


def annotation_changes(request, annotation_id=None):
    """View to display change history for annotations"""
    if annotation_id:
        # Show changes for specific annotation
        annotation = get_object_or_404(TextAnnotation, id=annotation_id)
        changes = annotation.changes.all()
        
        # Calculate text differences for this annotation
        text_with_changes = calculate_text_changes(annotation, changes)
        
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
