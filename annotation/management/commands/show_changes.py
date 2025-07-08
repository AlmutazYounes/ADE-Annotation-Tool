from django.core.management.base import BaseCommand
from annotation.models import AnnotationChange, TextAnnotation
from django.db.models import Count
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Display annotation changes and statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--annotation-id',
            type=int,
            help='Show changes for a specific annotation ID',
        )
        parser.add_argument(
            '--recent',
            type=int,
            default=24,
            help='Show changes from the last N hours (default: 24)',
        )
        parser.add_argument(
            '--type',
            type=str,
            help='Filter by change type (drug_added, drug_removed, event_added, event_removed)',
        )

    def handle(self, *args, **options):
        annotation_id = options.get('annotation_id')
        recent_hours = options.get('recent')
        change_type = options.get('type')

        self.stdout.write(
            self.style.SUCCESS('=== Annotation Change Tracking Report ===\n')
        )

        # Get changes based on filters
        changes = AnnotationChange.objects.select_related('annotation')

        if annotation_id:
            changes = changes.filter(annotation_id=annotation_id)
            self.stdout.write(f'Showing changes for Annotation #{annotation_id}\n')
        
        if change_type:
            changes = changes.filter(change_type=change_type)
            self.stdout.write(f'Filtering by change type: {change_type}\n')

        if recent_hours:
            cutoff_time = datetime.now() - timedelta(hours=recent_hours)
            changes = changes.filter(timestamp__gte=cutoff_time)
            self.stdout.write(f'Showing changes from the last {recent_hours} hours\n')

        # Get statistics
        total_changes = changes.count()
        change_types = changes.values('change_type').annotate(count=Count('change_type')).order_by('-count')
        
        self.stdout.write(f'Total changes: {total_changes}\n')
        
        if change_types:
            self.stdout.write('Changes by type:')
            for ct in change_types:
                self.stdout.write(f'  {ct["change_type"]}: {ct["count"]}')
            self.stdout.write('')

        # Show recent changes
        recent_changes = changes.order_by('-timestamp')[:10]
        
        if recent_changes:
            self.stdout.write('Recent changes:')
            self.stdout.write('-' * 80)
            for change in recent_changes:
                timestamp = change.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                entity_info = f"'{change.entity_name}'" if change.entity_name else 'N/A'
                
                self.stdout.write(
                    f'{timestamp} | Annotation #{change.annotation.id} | '
                    f'{change.get_change_type_display()} | {entity_info} | '
                    f'Field: {change.field_name}'
                )
        else:
            self.stdout.write('No changes found matching the criteria.')

        # Show session statistics
        if not annotation_id:
            session_stats = changes.values('session_id').annotate(count=Count('session_id')).order_by('-count')[:5]
            if session_stats:
                self.stdout.write('\nTop sessions by activity:')
                for session in session_stats:
                    if session['session_id']:
                        self.stdout.write(f'  Session {session["session_id"][:20]}...: {session["count"]} changes') 