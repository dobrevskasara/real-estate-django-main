from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from properties.models import Property, PropertyImage


class PropertyImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        covers = 0
        for form in self.forms:
            if not getattr(form, "cleaned_data", None):
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            if form.cleaned_data.get("is_cover"):
                covers += 1

        if covers > 1:
            raise ValidationError("You can select only one cover image.")


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    formset = PropertyImageInlineFormSet

    class Media:
        js = ("admin/js/cover_radio.js",)


class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "listing_type",
        "city",
        "property_type",
        "owner",
        "status",
        "created_at",
    )
    list_filter = ("listing_type","status", "city", "property_type")
    search_fields = ("name", "description", "city", "location")
    filter_horizontal = ("features",)
    actions = ["approve_property"]
    exclude = ('owner',)
    inlines = [PropertyImageInline]

    def get_exclude(self, request, obj=None):
        excluded = list(self.exclude)

        if obj is None:
            excluded.append("status")

        return excluded

    def get_readonly_fields(self, request, obj=None):
        readonly = []

        if obj:
            if obj.owner.profile.is_admin:
                readonly.append("status")
            else:
                if not (request.user.profile.is_admin or request.user.is_superuser):
                    readonly.append("status")

        return readonly

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user

            if request.user.profile.is_admin or request.user.is_superuser:
                obj.status = "approved"
            else:
                obj.status = "pending"
        else:
            old = Property.objects.get(pk=obj.pk)
            critical_fields = ["price", "description"]

            if obj.owner.profile.is_user:
                for field in critical_fields:
                    if getattr(old, field) != getattr(obj, field):
                        obj.status = "pending"
                        break

            if old.status == "rejected" and obj.status == "rejected":
                obj.status = "pending"

        super().save_model(request, obj, form, change)

    @admin.action(description="Approve selected properties")
    def approve_property(self, request, queryset):
        queryset.update(status="approved")


class FeatureAdmin(admin.ModelAdmin):
    search_fields = ("name",)
