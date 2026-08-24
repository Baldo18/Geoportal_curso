# ============================================================
# IMPORTACIONES
# ============================================================


from django.contrib import admin, messages
from django.contrib.gis.admin import GISModelAdmin

from .forms import UploadedLayerAdminForm
from .models import (
    TestGeometry,
    UploadedFeature,
    UploadedLayer,
)
from .services.importer import (
    process_uploaded_layer,
)

# ============================================================
# GEOMETRÍAS DE PRUEBA
# ============================================================


@admin.register(TestGeometry)
class TestGeometryAdmin(GISModelAdmin):
    list_display = (
        "id",
        "name",
        "created_at",
    )

    search_fields = ("name",)


# ============================================================
# CAPAS CARGADAS
# ============================================================


@admin.register(UploadedLayer)
class UploadedLayerAdmin(admin.ModelAdmin):
    form = UploadedLayerAdminForm

    list_display = (
        "id",
        "name",
        "file_format",
        "geometry_type",
        "source_epsg",
        "feature_count",
        "status",
        "created_by",
        "created_at",
    )

    list_filter = (
        "file_format",
        "geometry_type",
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "file_format",
        "source_epsg",
        "storage_epsg",
        "geometry_type",
        "feature_count",
        "file_hash",
        "status",
        "validation_message",
        "created_by",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Información",
            {
                "fields": (
                    "name",
                    "description",
                    "source_file",
                )
            },
        ),
        (
            "Información geoespacial",
            {
                "fields": (
                    "file_format",
                    "geometry_type",
                    "source_epsg",
                    "storage_epsg",
                    "feature_count",
                )
            },
        ),
        (
            "Validación",
            {
                "fields": (
                    "file_hash",
                    "status",
                    "validation_message",
                )
            },
        ),
        (
            "Registro",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        # Si viene un archivo nuevo.
        if "source_file" in form.changed_data:
            obj.file_format = form.detected_file_format

            obj.file_hash = form.detected_file_hash

            obj.status = "valid"

            obj.validation_message = "Archivo validado. Pendiente de procesamiento."

        if not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        if "source_file" in form.changed_data:
            try:
                process_uploaded_layer(obj)

                self.message_user(
                    request,
                    (f"La capa '{obj.name}' fue procesada correctamente."),
                    level=messages.SUCCESS,
                )

            except Exception as exc:
                self.message_user(
                    request,
                    (
                        "El archivo fue registrado, "
                        "pero ocurrió un error durante "
                        f"el procesamiento: {exc}"
                    ),
                    level=messages.ERROR,
                )


# ============================================================
# FEATURES GEOGRÁFICOS
# ============================================================


@admin.register(UploadedFeature)
class UploadedFeatureAdmin(GISModelAdmin):
    list_display = (
        "id",
        "layer",
        "geometry_type",
        "created_at",
    )

    list_filter = (
        "layer",
        "created_at",
    )

    search_fields = ("layer__name",)

    readonly_fields = (
        "layer",
        "properties",
        "created_at",
    )

    def geometry_type(self, obj):

        if not obj.geometry:
            return "-"

        return obj.geometry.geom_type

    geometry_type.short_description = "Tipo de geometría"
