from django.db import models
import json


class TextAnnotation(models.Model):
    """Model to store text entries with their annotations"""
    text = models.TextField(help_text="The medical text to be annotated")
    drugs = models.JSONField(default=list, help_text="List of drugs mentioned in the text")
    adverse_events = models.JSONField(default=list, help_text="List of adverse events mentioned in the text")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_validated = models.BooleanField(default=False, help_text="Whether this annotation has been validated")
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"Text {self.id}: {self.text[:50]}..."
    
    def get_drugs_as_string(self):
        """Return drugs as comma-separated string for easier editing"""
        return ", ".join(self.drugs) if self.drugs else ""
    
    def get_adverse_events_as_string(self):
        """Return adverse events as comma-separated string for easier editing"""
        return ", ".join(self.adverse_events) if self.adverse_events else ""
    
    def set_drugs_from_string(self, drugs_string):
        """Set drugs from comma-separated string"""
        if drugs_string.strip():
            self.drugs = [drug.strip() for drug in drugs_string.split(",") if drug.strip()]
        else:
            self.drugs = []
    
    def set_adverse_events_from_string(self, events_string):
        """Set adverse events from comma-separated string"""
        if events_string.strip():
            self.adverse_events = [event.strip() for event in events_string.split(",") if event.strip()]
        else:
            self.adverse_events = []
    
    def get_change_summary(self):
        """Get a summary of changes made to this annotation"""
        changes = self.changes.all()
        summary = {
            'total_changes': changes.count(),
            'drug_additions': changes.filter(change_type='drug_added').count(),
            'drug_removals': changes.filter(change_type='drug_removed').count(),
            'event_additions': changes.filter(change_type='event_added').count(),
            'event_removals': changes.filter(change_type='event_removed').count(),
            'last_modified': changes.order_by('-timestamp').first().timestamp if changes.exists() else None,
        }
        return summary
    
    def get_recent_changes(self, limit=10):
        """Get recent changes for this annotation"""
        return self.changes.all().order_by('-timestamp')[:limit]


class AnnotationChange(models.Model):
    """Model to track changes made to annotations"""
    CHANGE_TYPES = [
        ('drug_added', 'Drug Added'),
        ('drug_removed', 'Drug Removed'),
        ('event_added', 'Adverse Event Added'),
        ('event_removed', 'Adverse Event Removed'),
        ('bulk_update', 'Bulk Update'),
    ]
    
    annotation = models.ForeignKey(TextAnnotation, on_delete=models.CASCADE, related_name='changes')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    field_name = models.CharField(max_length=50, null=True, blank=True, help_text="Name of the field that was changed")
    old_value = models.JSONField(null=True, blank=True, help_text="Previous value")
    new_value = models.JSONField(null=True, blank=True, help_text="New value")
    entity_name = models.CharField(max_length=255, null=True, blank=True, help_text="Name of the entity that was added/removed")
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, null=True, blank=True, help_text="Browser session ID for tracking user sessions")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_change_type_display()} on Text {self.annotation.id} at {self.timestamp}"
    
    @classmethod
    def log_drug_change(cls, annotation, change_type, entity_name, old_drugs, new_drugs, session_id=None):
        """Log a drug-related change"""
        return cls.objects.create(
            annotation=annotation,
            change_type=change_type,
            field_name='drugs',
            old_value=old_drugs,
            new_value=new_drugs,
            entity_name=entity_name,
            session_id=session_id
        )
    
    @classmethod
    def log_event_change(cls, annotation, change_type, entity_name, old_events, new_events, session_id=None):
        """Log an adverse event-related change"""
        return cls.objects.create(
            annotation=annotation,
            change_type=change_type,
            field_name='adverse_events',
            old_value=old_events,
            new_value=new_events,
            entity_name=entity_name,
            session_id=session_id
        )
    
    @classmethod
    def log_bulk_update(cls, annotation, field_name, old_value, new_value, session_id=None):
        """Log a bulk update change"""
        return cls.objects.create(
            annotation=annotation,
            change_type='bulk_update',
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            entity_name=None,  # Bulk updates don't have a specific entity
            session_id=session_id
        )


class DrugListEntry(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name

class ADEListEntry(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name