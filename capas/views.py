from django.shortcuts import render, get_object_or_404
import json
from .models import UploadedLayer, UploadedFeature
from django.http import JsonResponse
# Create your views here.
#


def map_view(request):
    capas = UploadedLayer.objects.filter(status = "processed")
    context = {
        "capas": capas,

    }

    return render(request,"capas/mapa.html", context)

def layer_geojson(request, layer_id):
    capa = get_object_or_404(
        UploadedLayer,
        pk=layer_id,
    )

    elementos = UploadedFeature.objects.filter(
        layer=capa
    )

    features = []

    for elemento in elementos:

        if not elemento.geometry:
            continue

        feature = {
            "type": "Feature",

            "geometry": json.loads(
                elemento.geometry.geojson
            ),

            "properties": (
                elemento.properties or {}
            ),
        }

        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    return JsonResponse(geojson)
