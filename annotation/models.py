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
