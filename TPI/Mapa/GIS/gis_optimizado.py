import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import folium
from folium.plugins import Draw
import webbrowser
import threading
from flask import Flask, request, jsonify
import os
import json
import math
import requests
import time
from Mapa.GIS.departamento import encontrar_departamento

class MapApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Selector de Campo - Argentina")
        self.root.geometry("600x500")
        
        self.coordenadas = []
        self.area_m2 = 0
        self.area_ha = 0
        self.departamento = ""
        self.provincia = ""
        self._flask_thread = None
        
        #Flask
        self.app = Flask(__name__)
        self._setup_flask_routes()

        threading.Thread(target=lambda: self.app.run(port=5001, debug=False, use_reloader=False)).start()

        self.create_interface()
        
    def create_interface(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        ttk.Label(main_frame, text="Selector de Campo", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Instrucciones compactas
        instructions = ("1. Abrir mapa \n2. Dibujar polígono \n3. Clic derecho")
        ttk.Label(main_frame, text=instructions, justify=tk.LEFT, 
                 font=("Arial", 9)).grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        # Botón mapa
        ttk.Button(main_frame, text="Abrir Mapa", 
                  command=self.open_map).grid(row=2, column=0, columnspan=2, pady=(0, 15))
        
        # Entrada de coordenadas
        ttk.Label(main_frame, text="Coordenadas:").grid(row=3, column=0, sticky=tk.W)
        self.coords_input = scrolledtext.ScrolledText(main_frame, height=4, width=60)
        self.coords_input.grid(row=4, column=0, columnspan=2, pady=(5, 10))
        
        # Botones de acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(0, 15))
        
        ttk.Button(btn_frame, text="Procesar", 
                  command=self.process_coordinates).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Limpiar", 
                  command=self.clear_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Cargar", 
                  command=self.load_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Exportar", 
                  command=self.export_data).pack(side=tk.LEFT)
        
        # Resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        results_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.area_var = tk.StringVar(value="Área: No calculada")
        self.location_var = tk.StringVar(value="Ubicación: No determinada")
        
        ttk.Label(results_frame, textvariable=self.area_var, 
                 font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(results_frame, textvariable=self.location_var, 
                 font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W)
        
        # Configurar redimensionamiento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def create_map(self):
        """Crear mapa con controles de dibujo"""
        m = folium.Map(location=[-33.33, -60.23], zoom_start=10)
        
        # Plugin de dibujo
        Draw(draw_options={'polygon': True, 'rectangle': True, 'circle': False, 
                          'marker': False, 'circlemarker': False, 'polyline': False},
             edit_options={'edit': True}).add_to(m)
        
        # Script para mostrar coordenadas
        script = """
            <script>
            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);

            map.on('draw:created', function(e) {
                var layer = e.layer;
                drawnItems.addLayer(layer);

                var coords = layer.getLatLngs()[0].map(c => [c.lat, c.lng]);
                fetch("http://127.0.0.1:5001/guardar_coords", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({coordenadas: coords})
                }).then(r => console.log("Enviado"));
            });
            </script>
            """
        m.get_root().html.add_child(folium.Element(script))
        
        return m
    
    def _setup_flask_routes(self):
        coords_container = self.coordenadas

        @self.app.route("/")
        def index():
            return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Mapa Selector de Campo</title>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
                    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                    <script src="https://cdn.jsdelivr.net/npm/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
                </head>
                <body>
                    <div id="map" style="width: 100%; height: 100vh;"></div>
                    <script>
                        var map = L.map('map').setView([-33.33, -60.23], 10);
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '© OpenStreetMap'
                        }).addTo(map);

                        var drawnItems = new L.FeatureGroup();
                        map.addLayer(drawnItems);

                        var drawControl = new L.Control.Draw({
                            draw: {
                                polygon: true,
                                rectangle: true,
                                polyline: false,
                                circle: false,
                                marker: false,
                                circlemarker: false
                            },
                            edit: {
                                featureGroup: drawnItems
                            }
                        });
                        map.addControl(drawControl);

                        map.on('draw:created', function(e) {
                            var layer = e.layer;
                            drawnItems.addLayer(layer);

                            layer.on('contextmenu', function(e) {
                                var latlngs = layer.getLatLngs()[0];
                                var coordsArray = latlngs.map(function(p) {
                                    return [p.lng, p.lat];
                                });

                                // Enviar al servidor y esperar respuesta
                                fetch('/guardar_coords', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({coordenadas: coordsArray})
                                })
                                .then(response => response.json())
                                .then(data => {
                                    console.log("Coordenadas enviadas:", data.coordenadas);
                                    // Solo cerrar la ventana después de 500ms para asegurar envío
                                    setTimeout(() => { window.close(); }, 500);
                                })
                                .catch(err => {
                                    console.error("Error enviando coordenadas:", err);
                                    alert("Error enviando coordenadas, revisa la consola.");
                                });
                            });

                        });
                    </script>
                </body>
                </html>
                """

        @self.app.route("/guardar_coords", methods=["POST"])
        def guardar_coords():
            data = request.get_json()
            coords = data['coordenadas']
            print("Coordenadas recibidas:", coords)

            coords_container.clear()
            coords_container.extend(coords)

            coords_str = json.dumps(coords, indent=2)
            self.coords_input.delete(1.0, tk.END)
            self.coords_input.insert(1.0, coords_str)

            shutdown_func = request.environ.get('werkzeug.server.shutdown')
            if shutdown_func:
                shutdown_func()

            return jsonify({'coordenadas': coords})

    def start_flask_server(self):
        if self._flask_thread is None:
            self._flask_thread = threading.Thread(
                target=lambda: self.app.run(port=5001, debug=False, use_reloader=False)
            )
            self._flask_thread.daemon = True
            self._flask_thread.start()

    def open_map(self):
        """"Abrir mapa servido por Flask"""
        try:
            self.start_flask_server()  # Arranca servidor en segundo plano si no está corriendo
            webbrowser.open("http://127.0.0.1:5001/")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el mapa: {str(e)}")
    
    def cleanup_temp_file(self, filepath):
        """Limpiar archivo temporal"""
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except:
            pass  # Ignorar errores de limpieza
            
    def process_coordinates(self):
        """Procesar coordenadas ingresadas"""
        try:
            coords_text = self.coords_input.get("1.0", tk.END).strip()
            if not coords_text:
                messagebox.showwarning("Advertencia", "Ingresa las coordenadas")
                return
            
            # Parsear coordenadas
            coords_text = coords_text.replace('\n', '').replace('\r', '')
            try:
                self.coordenadas = json.loads(coords_text)
            except json.JSONDecodeError:
                coords_text = coords_text.replace('(', '[').replace(')', ']')
                self.coordenadas = json.loads(coords_text)
            
            # Validar
            if not isinstance(self.coordenadas, list) or len(self.coordenadas) < 3:
                raise ValueError("Se necesitan al menos 3 coordenadas")
            
            for coord in self.coordenadas:
                if not isinstance(coord, list) or len(coord) != 2:
                    raise ValueError("Formato: [[-34.123, -58.987], ...]")
                if not (-90 <= coord[0] <= 90) or not (-180 <= coord[1] <= 180):
                    raise ValueError("Coordenadas fuera de rango")
            
            # Calcular área y ubicación
            self.area_m2 = self.calcular_area(self.coordenadas)
            centro_lat = sum(c[0] for c in self.coordenadas) / len(self.coordenadas)
            centro_lon = sum(c[1] for c in self.coordenadas) / len(self.coordenadas)
            self.departamento, self.provincia = encontrar_departamento(self.coordenadas)
            
            # Actualizar resultados
            hectareas = self.area_m2 / 10000
            self.area_ha = hectareas
            if hectareas >= 1:
                area_text = f"Área: {hectareas:.2f} hectáreas ({self.area_m2:.0f} m²)"
            else:
                area_text = f"Área: {self.area_m2:.0f} m²"
            
            self.area_var.set(area_text)
            self.location_var.set(f"Ubicación: {self.departamento}, {self.provincia}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
            
    def calcular_area(self, coords):
        """Calcular área usando fórmula de Shoelace"""
        if len(coords) < 3:
            return 0
            
        # Fórmula de Shoelace
        n = len(coords)
        area = sum(coords[i][0] * coords[(i + 1) % n][1] - 
                  coords[(i + 1) % n][0] * coords[i][1] for i in range(n))
        area = abs(area) / 2.0
        
        # Convertir a metros cuadrados
        lat_promedio = sum(c[0] for c in coords) / len(coords)
        factor_lat = math.cos(math.radians(lat_promedio))
        metros_por_grado = 111320
        
        return area * metros_por_grado * metros_por_grado * factor_lat
        
    def obtener_ubicacion(self, lat, lon):
        """Geocodificación inversa"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {'lat': lat, 'lon': lon, 'format': 'json', 'addressdetails': 1}
            headers = {'User-Agent': 'CampoSelector/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            address = response.json().get('address', {})
            
            departamento = (address.get('county') or address.get('municipality') or 
                          address.get('city') or 'No determinado')
            provincia = address.get('state') or 'No determinada'
            
            return departamento, provincia
            
        except:
            return "No determinado", "No determinada"
            
    def load_file(self):
        """Cargar coordenadas desde archivo"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON", "*.json"), ("Texto", "*.txt"), ("Todos", "*.*")])
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.coords_input.delete(1.0, tk.END)
                    self.coords_input.insert(1.0, f.read())
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar: {str(e)}")
            
    def export_data(self):
        """Exportar datos a JSON"""
        if not self.coordenadas:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
            
        try:
            centro_lat = sum(c[0] for c in self.coordenadas) / len(self.coordenadas)
            centro_lon = sum(c[1] for c in self.coordenadas) / len(self.coordenadas)
            
            data = {
                'coordenadas': self.coordenadas,
                'area_ha': self.area_m2,
                'area_hectareas': self.area_m2 / 10000,
                'departamento': self.departamento,
                'provincia': self.provincia,
                'centro': {'lat': centro_lat, 'lon': centro_lon},
                'fecha': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                title="Guardar datos")
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Éxito", f"Exportado a: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
            
    def clear_all(self):
        """Limpiar todo"""
        self.coords_input.delete(1.0, tk.END)
        self.coordenadas = []
        self.area_m2 = 0
        self.area_var.set("Área: No calculada")
        self.location_var.set("Ubicación: No determinada")
        
    def run(self):
        """Ejecutar aplicación"""
        self.root.mainloop()


def correr_app():
    app = MapApp()
    app.run()

    return app

if __name__ == "__main__":
    try:
        app = MapApp()
        app.run()
    except ImportError as e:
        print(f"Instala dependencias: pip install folium requests")
        print(f"Error: {e}")