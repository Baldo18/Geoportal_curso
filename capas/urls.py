from django.urls import path



from .views import( map_view, layer_geojson)

urlpatterns = [
    path("mapa/", map_view, name="mapa"),
    path("geojson/<int:layer_id>/", layer_geojson, name = "layer_geojson")
    
]

