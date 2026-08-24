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
    // NUEVO: PANEL DINÁMICO DE METADATOS
    // ==========================================
    const metadatosCapasActivas = {};

    function actualizarPanelMetadatos() {
            const contenedor = document.getElementById('contenido-metadatos');
            const panelGeneral = document.getElementById('panel-metadatos-activos');

            if (!contenedor || !panelGeneral) return;

            contenedor.innerHTML = ''; // Limpiamos el contenido anterior
            const idsCapas = Object.keys(metadatosCapasActivas);

            if (idsCapas.length === 0) {
                // Ocultar usando la clase d-none de Bootstrap
                panelGeneral.classList.add('d-none');
                return;
            }

            // Mostrar quitando la clase d-none
            panelGeneral.classList.remove('d-none');

            idsCapas.forEach(id => {
                const meta = metadatosCapasActivas[id];

                // Creamos una "Tarjeta" de Bootstrap para cada capa
                // col-md-6 col-lg-4 col-xl-3 indica que ocupará diferentes tamaños según la pantalla
                // y se acomodarán consecutivamente de izquierda a derecha.
                contenedor.innerHTML += `
                    <div class="col-md-6 col-lg-4 col-xl-3">
                        <div class="card h-100 shadow-sm border-0 border-top border-primary border-3">
                            <div class="card-body">
                                <h6 class="card-title fw-bold text-dark mb-3">${meta.nombre}</h6>
                                <ul class="list-unstyled mb-0" style="font-size: 0.85rem;">
                                    <li class="mb-2">
                                        <strong class="text-secondary">Descripción:</strong>
                                        <span class="d-block mt-1 text-muted">${meta.descripcion}</span>
                                    </li>
                                    <li class="mb-2">
                                        <strong class="text-secondary">Tipo Geometría:</strong>
                                        <span class="text-dark">${meta.tipo_geometria}</span>
                                    </li>
                                    <li>
                                        <strong class="text-secondary">Total Elementos:</strong>
                                        <span class="badge bg-primary rounded-pill ms-1">${meta.total}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

    // ==========================================
    // 4. LÓGICA DE CAPAS (Cargar/Descargar)
    // ==========================================
    const loadedLayers = {};
    const checkboxes = document.querySelectorAll(".layer-checkbox");

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener("change", function () {
            const layerId = this.value;
            // Intentar obtener un nombre amigable para la capa desde el label o asignarle uno genérico
            const layerName = this.nextElementSibling ? this.nextElementSibling.textContent.trim() : "Capa " + layerId;
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

                        // -- NUEVO: EXTRAER Y GUARDAR METADATOS DE LA RESPUESTA JSON --
                        let tipoGeometria = "Desconocido";
                        let totalFeatures = 0;

                        // Validamos de qué tipo de geometría es y cuántos elementos trae el GeoJSON
                        if (data.features && data.features.length > 0) {
                            tipoGeometria = data.features[0].geometry.type;
                            totalFeatures = data.features.length;
                        }

                        // Guardamos los datos. Si tu backend de Django manda un objeto 'metadatos',
                        // lo usamos; si no, calculamos valores dinámicos.
                        metadatosCapasActivas[layerId] = {
                            nombre: layerName,
                            descripcion: data.metadatos?.descripcion || 'Cargada desde servidor espacial',
                            tipo_geometria: data.metadatos?.tipo_geometria || tipoGeometria,
                            total: data.metadatos?.total_registros || totalFeatures
                        };

                        // Refrescamos el panel
                        actualizarPanelMetadatos();
                        // -------------------------------------------------------------

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

                    // -- NUEVO: ELIMINAR LOS METADATOS CUANDO SE APAGA LA CAPA --
                    delete metadatosCapasActivas[layerId];
                    actualizarPanelMetadatos();
                    // -----------------------------------------------------------
                }
            }
        });
    });
});
