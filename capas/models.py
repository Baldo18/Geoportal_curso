from django.contrib.gis.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class TestGeometry(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Nombre"
    )

    geometry= models.GeometryField(
        srid=4326,
        verbose_name="Geometria"
    )

    created_at= models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creacion"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name= "Geometria de prueba"
        verbose_name_plural = "Geometrias de prueba"

class UploadedLayer(models.Model):
    FORMAT_CHOICES = (
        ("shp", "Shapefile ZIP"),
        ("geojson", "GeoJSON"),
    )

    STATUS_CHOICES = (
        ("pending", "Pendiente"),
        ("valid", "Válido"),
        ("processed", "Procesado"),
        ("error", "Error"),
    )

    name = models.CharField(
        max_length=200,
        verbose_name="Nombre de la capa",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descripción",
    )

    source_file = models.FileField(
        upload_to="layers/%Y/%m/",
        verbose_name="Archivo geoespacial",
    )

    file_format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        blank=True,
        editable=False,
        verbose_name="Formato",
    )

    source_epsg = models.IntegerField(
        null=True,
        blank=True,
        editable=False,
        verbose_name="EPSG original",
    )

    storage_epsg = models.IntegerField(
        default=4326,
        editable=False,
        verbose_name="EPSG de almacenamiento",
    )

    geometry_type = models.CharField(
        max_length=50,
        blank=True,
        editable=False,
        verbose_name="Tipo de geometría",
    )

    feature_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Número de elementos",
    )

    file_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name="SHA-256",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        editable=False,
        verbose_name="Estado",
    )

    validation_message = models.TextField(
        blank=True,
        editable=False,
        verbose_name="Resultado de validación",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="uploaded_layers",
        verbose_name="Usuario que realizó la carga",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de carga",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Capa cargada"
        verbose_name_plural = "Capas cargadas"
        ordering = ("-created_at",)


class UploadedFeature(models.Model):

    layer = models.ForeignKey(
        UploadedLayer,
        on_delete=models.CASCADE,
        related_name="features",
        verbose_name="Capa",
    )

    geometry = models.GeometryField(
        srid=4326,
        spatial_index=True,
        verbose_name="Geometría",
    )

    properties = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Atributos",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    def __str__(self):
        return f"{self.layer.name} - {self.pk}"

    class Meta:
        verbose_name = "Elemento geográfico"
        verbose_name_plural = "Elementos geográficos"
