from django import forms
from django.core.exceptions import ValidationError


from .models import UploadedLayer
from .validators import (
   calculate_sha256,
   validate_geospatial_file,
)




class UploadedLayerAdminForm(forms.ModelForm):


   class Meta:
       model = UploadedLayer


       fields = (
           "name",
           "description",
           "source_file",
       )


   def clean_source_file(self):


       uploaded_file = self.cleaned_data[
           "source_file"
       ]


       # Validar estructura.
       file_format = validate_geospatial_file(
           uploaded_file
       )


       # Calcular SHA-256.
       file_hash = calculate_sha256(
           uploaded_file
       )


       queryset = UploadedLayer.objects.filter(
           file_hash=file_hash
       )


       if self.instance.pk:
           queryset = queryset.exclude(
               pk=self.instance.pk
           )


       if queryset.exists():
           raise ValidationError(
               "Este archivo ya fue cargado anteriormente."
           )


       # Guardamos temporalmente estos valores
       # para utilizarlos desde save_model().
       self.detected_file_format = file_format
       self.detected_file_hash = file_hash


       return uploaded_file
