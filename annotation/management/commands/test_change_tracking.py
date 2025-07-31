from django.core.management.base import BaseCommand
from annotation.models import TextAnnotation, AnnotationChange
from django.db.models import Count


class Command(BaseCommand):
    help = 'Test change tracking functionality'

    def handle(self, *args, **options):
        self.stdout.write("Testing change tracking functionality...")
        
        # Check if we have any annotations
        total_annotations = TextAnnotation.objects.count()
        self.stdout.write(f"Total annotations: {total_annotations}")
        
        if total_annotations == 0:
            self.stdout.write("No annotations found. Please import some data first.")
            return
        
        # Check change tracking statistics
        total_changes = AnnotationChange.objects.count()
        self.stdout.write(f"Total changes tracked: {total_changes}")
        
        # Breakdown by change type
        change_types = AnnotationChange.objects.values('change_type').annotate(
            count=Count('change_type')
        ).order_by('-count')
        
        self.stdout.write("\nChange type breakdown:")
        for change_type in change_types:
            self.stdout.write(f"  {change_type['change_type']}: {change_type['count']}")
        
        # Check most active annotations
        most_active = TextAnnotation.objects.annotate(
            num_changes=Count('changes')
        ).filter(changes__isnull=False).order_by('-num_changes')[:5]
        
        if most_active:
            self.stdout.write("\nMost active annotations:")
            for ann in most_active:
                self.stdout.write(f"  Annotation #{ann.id}: {ann.num_changes} changes")
        
        # Test creating a sample change
        sample_annotation = TextAnnotation.objects.first()
        if sample_annotation:
            self.stdout.write(f"\nTesting change logging on annotation #{sample_annotation.id}...")
            
            # Log a sample drug addition
            old_drugs = sample_annotation.drugs.copy()
            new_drugs = old_drugs + ['Test Drug']
            
            change = AnnotationChange.log_drug_change(
                annotation=sample_annotation,
                change_type='drug_added',
                entity_name='Test Drug',
                old_drugs=old_drugs,
                new_drugs=new_drugs,
                session_id='test_session'
            )
            
            self.stdout.write(f"Created test change: {change}")
            
            # Verify the change was saved
            new_total = AnnotationChange.objects.count()
            self.stdout.write(f"New total changes: {new_total}")
            
            # Test change summary
            summary = sample_annotation.get_change_summary()
            self.stdout.write(f"Change summary for annotation #{sample_annotation.id}:")
            self.stdout.write(f"  Total changes: {summary['total_changes']}")
            self.stdout.write(f"  Drug additions: {summary['drug_additions']}")
            self.stdout.write(f"  Drug removals: {summary['drug_removals']}")
            self.stdout.write(f"  Event additions: {summary['event_additions']}")
            self.stdout.write(f"  Event removals: {summary['event_removals']}")
        
        self.stdout.write("\nChange tracking test completed!") 