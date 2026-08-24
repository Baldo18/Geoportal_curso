import hashlib
import json
import zipfile
from pathlib import Path

from django.core.exceptions import ValidationError

MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_UNCOMPRESSED_SIZE = 200 * 1024 * 1024


ALLOWED_EXTENSIONS = {
    ".zip",
    ".geojson",
    ".json",
}


def calculate_sha256(uploaded_file):
    """
    Calcula el SHA-256 del archivo.
    """

    sha256 = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        sha256.update(chunk)

    uploaded_file.seek(0)

    return sha256.hexdigest()


def validate_file_size(uploaded_file):
    """
    Impide archivos superiores a 50 MB.
    """

    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError("El archivo supera el tamaño máximo permitido de 50 MB.")


def validate_extension(uploaded_file):
    """
    Solamente acepta ZIP, GEOJSON y JSON.
    """

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            "Formato no permitido. Utilice Shapefile comprimido en ZIP o GeoJSON."
        )

    return extension


def validate_shapefile_zip(uploaded_file):
    """
    Comprueba que un ZIP contenga un Shapefile completo.
    """

    try:
        with zipfile.ZipFile(uploaded_file) as zip_file:
            if zip_file.testzip() is not None:
                raise ValidationError("El archivo ZIP está dañado.")

            members = zip_file.infolist()

            total_size = sum(member.file_size for member in members)

            if total_size > MAX_UNCOMPRESSED_SIZE:
                raise ValidationError(
                    "El contenido descomprimido supera el límite permitido."
                )

            # Evitar rutas inseguras dentro del ZIP.
            for member in members:
                path = Path(member.filename)

                if path.is_absolute() or ".." in path.parts:
                    raise ValidationError("El ZIP contiene rutas no permitidas.")

            filenames = [
                Path(member.filename).name.lower()
                for member in members
                if not member.is_dir()
            ]

            shp_files = [name for name in filenames if name.endswith(".shp")]

            if len(shp_files) == 0:
                raise ValidationError("El ZIP no contiene ningún archivo .shp.")

            if len(shp_files) > 1:
                raise ValidationError("El ZIP debe contener solamente un Shapefile.")

            shapefile_stem = Path(shp_files[0]).stem

            required_extensions = {
                ".shp",
                ".shx",
                ".dbf",
                ".prj",
            }

            existing_extensions = set()

            for filename in filenames:
                file_path = Path(filename)

                if file_path.stem == shapefile_stem:
                    existing_extensions.add(file_path.suffix)

            missing = required_extensions - existing_extensions

            if missing:
                raise ValidationError(
                    "El Shapefile está incompleto. "
                    "Faltan los archivos: " + ", ".join(sorted(missing))
                )

    except zipfile.BadZipFile:
        raise ValidationError("El archivo proporcionado no es un ZIP válido.")

    finally:
        uploaded_file.seek(0)


def validate_geojson(uploaded_file):
    """
    Comprueba estructura básica de GeoJSON.
    """

    try:
        data = json.load(uploaded_file)

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        raise ValidationError("El archivo no contiene JSON válido.")

    finally:
        uploaded_file.seek(0)

    if not isinstance(data, dict):
        raise ValidationError("El GeoJSON debe contener un objeto JSON.")

    if data.get("type") != "FeatureCollection":
        raise ValidationError(
            "El archivo debe ser un GeoJSON de tipo FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValidationError("El GeoJSON no contiene una lista válida de features.")

    if not features:
        raise ValidationError("El GeoJSON no contiene entidades geográficas.")


def validate_geospatial_file(uploaded_file):
    """
    Ejecuta todas las validaciones iniciales.
    """

    validate_file_size(uploaded_file)

    extension = validate_extension(uploaded_file)

    if extension == ".zip":
        validate_shapefile_zip(uploaded_file)

        return "shp"

    validate_geojson(uploaded_file)

    return "geojson"
