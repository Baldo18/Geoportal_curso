document.addEventListener("DOMContentLoaded", function () {
    // ==========================================
    // 1. DEFINICIÓN DE MAPAS BASE
    // ==========================================
    const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
    });

    const satelite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    });

    const cartoDark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '&copy; CartoDB'
    });

    // ==========================================
    // 2. CREACIÓN DEL MAPA
    // ==========================================
    const map = L.map("map", {
        center: [23.6345, -102.5528], // Centrado en México
        zoom: 5,
        layers: [osm] // Mapa base por defecto
    });

    // Control para cambiar entre mapas base
    const baseMaps = {
        "Calles (OSM)": osm,
        "Satélite (Esri)": satelite,
        "Modo Oscuro": cartoDark
    };
    L.control.layers(baseMaps, null, { position: 'topright' }).addTo(map);

    // ==========================================
    // 3. FUNCIÓN PARA CREAR POPUPS ELEGANTES
    // ==========================================
    function createPopupHtml(properties) {
        if (!properties || Object.keys(properties).length === 0) return "Sin datos";
        
        let html = '<div class="table-responsive"><table class="table table-sm table-striped popup-table"><tbody>';
        for (const [key, value] of Object.entries(properties)) {
            // Ignoramos campos vacíos o nulos para no ensuciar el popup
            if (value !== null && value !== '') {
                html += `<tr><th>${key}</th><td>${value}</td></tr>`;
            }
        }
        html += '</tbody></table></div>';
        return html;
    }

    // ==========================================
    // 4. LÓGICA DE CAPAS (Cargar/Descargar)
    // ==========================================
    const loadedLayers = {};
    const checkboxes = document.querySelectorAll(".layer-checkbox");

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener("change", function () {
            const layerId = this.value;
            const spinner = document.getElementById(`spinner-${layerId}`);

            if (this.checked) {
                // Mostrar indicador de carga y deshabilitar checkbox
                if (spinner) spinner.classList.remove('d-none');
                this.disabled = true; 

                fetch(`/geojson/${layerId}/`)
                    .then(response => {
                        if (!response.ok) throw new Error("Error HTTP: " + response.status);
                        return response.json();
                    })
                    .then(data => {
                        // Asignar colores aleatorios atractivos a cada capa
                        const randomColor = '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');

                        const layer = L.geoJSON(data, {
                            style: function (feature) {
                                return { color: randomColor, weight: 2, fillOpacity: 0.4 };
                            },
                            onEachFeature: function (feature, leafletLayer) {
                                if (feature.properties) {
                                    leafletLayer.bindPopup(createPopupHtml(feature.properties), {
                                        className: 'custom-popup',
                                        maxWidth: 300
                                    });
                                }
                            },
                        });

                        layer.addTo(map);
                        loadedLayers[layerId] = layer;

                        // Ajustar vista a la capa
                        const bounds = layer.getBounds();
                        if (bounds.isValid()) {
                            map.flyToBounds(bounds, { padding: [50, 50], duration: 1.5 }); 
                        }
                    })
                    .catch(error => {
                        console.error("Error al cargar la capa:", error);
                        alert("Hubo un error al cargar la capa geográfica.");
                        this.checked = false; // Desmarcar si hubo error
                    })
                    .finally(() => {
                        // Ocultar indicador de carga y habilitar checkbox
                        if (spinner) spinner.classList.add('d-none');
                        this.disabled = false;
                    });
            } 
            else {
                // Desactivar capa
                if (loadedLayers[layerId]) {
                    map.removeLayer(loadedLayers[layerId]);
                    delete loadedLayers[layerId];
                }
            }
        });
    });
});