import tempfile
import zipfile
from pathlib import Path


from django.contrib.gis.gdal import DataSource
from django.db import transaction


from capas.models import UploadedFeature




STORAGE_SRID = 4326




def extract_shapefile(zip_path):
   """
   Extrae temporalmente un ZIP y devuelve
   la ruta del archivo .shp.
   """


   temp_directory = tempfile.TemporaryDirectory()


   temp_path = Path(
       temp_directory.name
   )


   with zipfile.ZipFile(zip_path) as zip_file:
       zip_file.extractall(temp_path)


   shapefiles = list(
       temp_path.rglob("*.shp")
   )


   if len(shapefiles) != 1:
       temp_directory.cleanup()


       raise ValueError(
           "No se encontró exactamente un archivo SHP."
       )


   return (
       temp_directory,
       shapefiles[0],
   )




def get_datasource(layer):
   """
   Abre la fuente vectorial mediante GDAL.
   """


   if layer.file_format == "shp":


       temp_directory, path = (
           extract_shapefile(
               layer.source_file.path
           )
       )


       datasource = DataSource(
           str(path)
       )


       return datasource, temp_directory


   datasource = DataSource(
       layer.source_file.path
   )


   return datasource, None




def get_source_srid(gdal_layer):
   """
   Intenta detectar el EPSG de origen.
   """


   if not gdal_layer.srs:
       return None


   try:
       return gdal_layer.srs.srid


   except Exception:
       return None




def serialize_value(value):
   """
   Convierte atributos OGR a tipos compatibles
   con JSONField.
   """


   if value is None:
       return None


   if isinstance(
       value,
       (str, int, float, bool),
   ):
       return value


   return str(value)




def process_uploaded_layer(layer):
   """
   Procesa un UploadedLayer y crea
   UploadedFeature en PostGIS.
   """


   datasource = None
   temporary_directory = None


   try:


       datasource, temporary_directory = (
           get_datasource(layer)
       )


       if len(datasource) != 1:
           raise ValueError(
               "La fuente debe contener exactamente una capa."
           )


       gdal_layer = datasource[0]


       source_srid = get_source_srid(
           gdal_layer
       )


       # GeoJSON normalmente trabaja en WGS84.
       if (
           source_srid is None
           and layer.file_format == "geojson"
       ):
           source_srid = 4326


       if source_srid is None:
           raise ValueError(
               "No fue posible determinar el EPSG "
               "del archivo."
           )


       geometry_type = str(
           gdal_layer.geom_type
       )


       features_to_create = []


       for feature in gdal_layer:


           if feature.geom is None:
               continue


           # Convertir OGRGeometry a GEOSGeometry.
           geometry = feature.geom.geos


           if geometry.srid is None:
               geometry.srid = source_srid


           # Reproyectar a EPSG:4326.
           if geometry.srid != STORAGE_SRID:
               geometry.transform(
                   STORAGE_SRID
               )


           properties = {}


           for field_name in gdal_layer.fields:


               properties[field_name] = (
                   serialize_value(
                       feature.get(
                           field_name
                       )
                   )
               )


           features_to_create.append(
               UploadedFeature(
                   layer=layer,
                   geometry=geometry,
                   properties=properties,
               )
           )


       if not features_to_create:
           raise ValueError(
               "El archivo no contiene geometrías válidas."
           )


       with transaction.atomic():


           # Si se vuelve a procesar una capa,
           # reemplazamos sus features.
           layer.features.all().delete()


           UploadedFeature.objects.bulk_create(
               features_to_create,
               batch_size=500,
           )


           layer.source_epsg = source_srid


           layer.storage_epsg = STORAGE_SRID


           layer.geometry_type = geometry_type


           layer.feature_count = len(
               features_to_create
           )


           layer.status = "processed"


           layer.validation_message = (
               "Archivo validado y procesado correctamente."
           )


           layer.save(
               update_fields=[
                   "source_epsg",
                   "storage_epsg",
                   "geometry_type",
                   "feature_count",
                   "status",
                   "validation_message",
                   "updated_at",
               ]
           )


   except Exception as exc:


       layer.status = "error"


       layer.validation_message = str(exc)


       layer.save(
           update_fields=[
               "status",
               "validation_message",
               "updated_at",
           ]
       )


       raise


   finally:


       if temporary_directory:
           temporary_directory.cleanup()
