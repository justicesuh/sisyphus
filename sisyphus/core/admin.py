from django.contrib import admin


class UUIDModelAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields + tuple([field for field in ['created_at', 'updated_at'] if hasattr(self.model, field)])
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        fields.remove('uuid')
        fields.insert(0, 'uuid')
        return fields
