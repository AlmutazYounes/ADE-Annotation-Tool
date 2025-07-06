from django.contrib import admin
from .models import TextAnnotation


@admin.register(TextAnnotation)
class TextAnnotationAdmin(admin.ModelAdmin):
    """Admin interface for TextAnnotation model"""
    
    list_display = ['id', 'text_preview', 'drugs_count', 'adverse_events_count', 'is_validated', 'updated_at']
    list_filter = ['is_validated', 'created_at', 'updated_at']
    search_fields = ['text', 'drugs', 'adverse_events']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Text Content', {
            'fields': ('text',)
        }),
        ('Entities', {
            'fields': ('drugs', 'adverse_events'),
            'description': 'Enter entities as JSON arrays, e.g., ["drug1", "drug2"]'
        }),
        ('Status', {
            'fields': ('is_validated',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Show a preview of the text content"""
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = "Text Preview"
    
    def drugs_count(self, obj):
        """Show the number of drugs"""
        return len(obj.drugs) if obj.drugs else 0
    drugs_count.short_description = "Drugs Count"
    
    def adverse_events_count(self, obj):
        """Show the number of adverse events"""
        return len(obj.adverse_events) if obj.adverse_events else 0
    adverse_events_count.short_description = "Adverse Events Count"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view"""
        return super().get_queryset(request).select_related()
    
    actions = ['mark_as_validated', 'mark_as_unvalidated']
    
    def mark_as_validated(self, request, queryset):
        """Mark selected annotations as validated"""
        updated = queryset.update(is_validated=True)
        self.message_user(request, f'{updated} annotations marked as validated.')
    mark_as_validated.short_description = "Mark selected annotations as validated"
    
    def mark_as_unvalidated(self, request, queryset):
        """Mark selected annotations as unvalidated"""
        updated = queryset.update(is_validated=False)
        self.message_user(request, f'{updated} annotations marked as unvalidated.')
    mark_as_unvalidated.short_description = "Mark selected annotations as unvalidated"
