from django.contrib import admin


class ModelAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None, **kwargs):
        fields = super().get_readonly_fields(request, obj, **kwargs)
        fields = fields + tuple([
            field
            for field in ['created_at', 'updated_at']
            if hasattr(self.model, field)
        ])
        return fields


class UUIDModelAdmin(ModelAdmin):
    readonly_fields = ('uuid',)

    def get_fields(self, request, obj=None, **kwargs):
        fields = super().get_fields(request, obj, **kwargs)
        fields.remove('uuid')
        fields.insert(0, 'uuid')
        return fields
