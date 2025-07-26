import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import folium
from folium.plugins import Draw
import webbrowser
import os
import json
import math
import requests
#import threading
import time
#from geopy.distance import geodesic

class MapApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Selector de Campo - Argentina")
        self.root.geometry("700x600")
        
        # Variables para almacenar datos
        self.coordenadas = []
        self.area_m2 = 0
        self.departamento = ""
        self.provincia = ""
        
        # Crear interfaz
        self.create_interface()
        
    def create_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Selector de Campo", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Instrucciones
        instructions = """📋 INSTRUCCIONES:
            1. Haz clic en 'Abrir Mapa Interactivo'
            2. Navega hasta encontrar tu campo
            3. Usa la herramienta de polígono (□) para marcar el área
            4. Haz clic derecho sobre el polígono dibujado
            5. Copia las coordenadas que aparecen
            6. Pégalas en el cuadro de texto de abajo
            7. Haz clic en 'Procesar Coordenadas'"""
        
        inst_label = ttk.Label(main_frame, text=instructions, justify=tk.LEFT, font=("Arial", 9))
        inst_label.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        # Botón para abrir mapa
        self.btn_map = ttk.Button(main_frame, text="🗺️ Abrir Mapa Interactivo", 
                                 command=self.open_map, style="Accent.TButton")
        self.btn_map.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        # Frame para entrada de coordenadas
        input_frame = ttk.LabelFrame(main_frame, text="Coordenadas del Polígono", padding="10")
        input_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(input_frame, text="Pega aquí las coordenadas del polígono:").grid(row=0, column=0, sticky=tk.W)
        
        # Cuadro de texto para coordenadas
        self.coords_input = scrolledtext.ScrolledText(input_frame, height=4, width=70)
        self.coords_input.grid(row=1, column=0, columnspan=2, pady=(5, 10))
        
        # Ejemplo de formato
        example_text = """Ejemplo de formato esperado:
            [[-34.123456, -58.987654], [-34.234567, -58.876543], [-34.345678, -58.765432]]"""
        ttk.Label(input_frame, text=example_text, font=("Arial", 8), foreground="gray").grid(row=2, column=0, sticky=tk.W)
        
        # Botones de procesamiento
        button_frame1 = ttk.Frame(input_frame)
        button_frame1.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame1, text="📊 Procesar Coordenadas", 
                  command=self.process_manual_coordinates).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame1, text="🗑️ Limpiar", 
                  command=self.clear_input).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame1, text="📁 Cargar desde Archivo", 
                  command=self.load_from_file).pack(side=tk.LEFT)
        
        # Frame para resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        results_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Área
        ttk.Label(results_frame, text="Área:").grid(row=0, column=0, sticky=tk.W)
        self.area_var = tk.StringVar(value="No calculada")
        self.area_label = ttk.Label(results_frame, textvariable=self.area_var, font=("Arial", 10, "bold"))
        self.area_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Ubicación
        ttk.Label(results_frame, text="Ubicación:").grid(row=1, column=0, sticky=tk.W)
        self.location_var = tk.StringVar(value="No determinada")
        self.location_label = ttk.Label(results_frame, textvariable=self.location_var, font=("Arial", 10, "bold"))
        self.location_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Coordenadas procesadas
        ttk.Label(results_frame, text="Coordenadas procesadas:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.coords_output = scrolledtext.ScrolledText(results_frame, height=6, width=70)
        self.coords_output.grid(row=3, column=0, columnspan=2, pady=(5, 0))
        
        # Botones adicionales
        button_frame2 = ttk.Frame(main_frame)
        button_frame2.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame2, text="💾 Exportar Datos", 
                  command=self.export_coordinates).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame2, text="🔄 Limpiar Resultados", 
                  command=self.clear_results).pack(side=tk.LEFT)
        
        # Configurar redimensionamiento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def create_map(self):
        """Crear mapa con controles de dibujo mejorados"""
        # Centrar en Argentina
        m = folium.Map(
            location=[-34.6037, -58.3816],  # Buenos Aires como centro
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Agregar plugin de dibujo
        draw = Draw(
            draw_options={
                'polygon': True,
                'rectangle': True,
                'circle': False,
                'marker': False,
                'circlemarker': False,
                'polyline': False
            },
            edit_options={'edit': True}
        )
        draw.add_to(m)
        
        # Agregar instrucciones en el mapa
        instructions_html = """
        <div style="position: fixed; 
                    top: 10px; 
                    right: 10px; 
                    width: 300px; 
                    background: white; 
                    border: 2px solid #333; 
                    border-radius: 5px; 
                    padding: 10px; 
                    font-family: Arial; 
                    z-index: 1000;">
            <h4>📋 Instrucciones:</h4>
            <ol>
                <li>Usa la herramienta de polígono (□) del panel izquierdo</li>
                <li>Haz clic en el mapa para crear puntos del polígono</li>
                <li>Haz doble clic para terminar el polígono</li>
                <li>Haz clic derecho sobre el polígono dibujado</li>
                <li>Copia las coordenadas que aparecen</li>
                <li>Pégalas en la aplicación Python</li>
            </ol>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(instructions_html))
        
        # Agregar script para mostrar coordenadas al hacer clic
        coordinate_script = """
        <script>
        var drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        
        map.on('draw:created', function(e) {
            var layer = e.layer;
            drawnItems.addLayer(layer);
            
            // Agregar evento de clic derecho
            layer.on('contextmenu', function(e) {
                var coords = layer.getLatLngs()[0];
                var coordsArray = [];
                coords.forEach(function(coord) {
                    coordsArray.push([coord.lat, coord.lng]);
                });
                
                // Mostrar coordenadas en popup
                var coordsText = JSON.stringify(coordsArray, null, 2);
                var popup = L.popup()
                    .setLatLng(e.latlng)
                    .setContent('<div style="max-width: 300px;"><strong>Coordenadas:</strong><br>' + 
                               '<textarea style="width: 100%; height: 100px;" readonly>' + 
                               coordsText + '</textarea><br>' +
                               '<small>Selecciona todo el texto y cópialo (Ctrl+A, Ctrl+C)</small></div>')
                    .openOn(map);
                    
                // Seleccionar automáticamente el texto
                setTimeout(function() {
                    var textarea = document.querySelector('textarea');
                    if (textarea) {
                        textarea.select();
                    }
                }, 100);
            });
        });
        </script>
        """
        
        m.get_root().html.add_child(folium.Element(coordinate_script))
        
        # Guardar mapa
        map_path = os.path.join(os.getcwd(), 'campo_selector.html')
        m.save(map_path)
        
        return map_path
        
    def open_map(self):
        """Abrir mapa en navegador"""
        try:
            self.btn_map.config(text="Abriendo mapa...", state="disabled")
            
            # Crear mapa actualizado
            map_path = self.create_map()
            
            # Abrir en navegador
            webbrowser.open(f'file://{os.path.abspath(map_path)}')
            
            # Mostrar mensaje de instrucciones
            messagebox.showinfo("Mapa Abierto", 
                "✅ El mapa se abrió en tu navegador.\n\n" +
                "🔹 Dibuja el polígono de tu campo\n" +
                "🔹 Haz clic derecho sobre el polígono\n" +
                "🔹 Copia las coordenadas\n" +
                "🔹 Pégalas en la aplicación y procesa")
            
            self.btn_map.config(text="🗺️ Abrir Mapa Interactivo", state="normal")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el mapa: {str(e)}")
            self.btn_map.config(text="🗺️ Abrir Mapa Interactivo", state="normal")
            
    def process_manual_coordinates(self):
        """Procesar coordenadas ingresadas manualmente"""
        try:
            # Obtener texto del cuadro de entrada
            coords_text = self.coords_input.get("1.0", tk.END).strip()
            
            if not coords_text:
                messagebox.showwarning("Advertencia", "Por favor ingresa las coordenadas del polígono")
                return
            
            # Limpiar y parsear coordenadas
            coords_text = coords_text.replace('\n', '').replace('\r', '')
            
            # Intentar parsear como JSON
            try:
                self.coordenadas = json.loads(coords_text)
            except json.JSONDecodeError:
                # Intentar parsear formato alternativo
                coords_text = coords_text.replace('(', '[').replace(')', ']')
                self.coordenadas = json.loads(coords_text)
            
            # Validar formato
            if not isinstance(self.coordenadas, list) or len(self.coordenadas) < 3:
                raise ValueError("Se necesitan al menos 3 coordenadas para formar un polígono")
            
            # Validar que cada coordenada tenga lat y lon
            for coord in self.coordenadas:
                if not isinstance(coord, list) or len(coord) != 2:
                    raise ValueError("Cada coordenada debe tener formato [lat, lon]")
                if not (-90 <= coord[0] <= 90) or not (-180 <= coord[1] <= 180):
                    raise ValueError("Coordenadas fuera de rango válido")
            
            # Procesar coordenadas
            self.process_coordinates()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar coordenadas: {str(e)}\n\n" +
                                "Formato esperado: [[-34.123, -58.987], [-34.234, -58.876], ...]")
            
    def process_coordinates(self):
        """Procesar coordenadas y calcular área"""
        if not self.coordenadas:
            return
            
        try:
            # Calcular área
            self.area_m2 = self.calcular_area_poligono(self.coordenadas)
            
            # Obtener ubicación (centro del polígono)
            centro_lat = sum(coord[0] for coord in self.coordenadas) / len(self.coordenadas)
            centro_lon = sum(coord[1] for coord in self.coordenadas) / len(self.coordenadas)
            
            # Obtener departamento y provincia
            self.departamento, self.provincia = self.obtener_ubicacion(centro_lat, centro_lon)
            
            # Actualizar interfaz
            self.update_results()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar coordenadas: {str(e)}")
            
    def calcular_area_poligono(self, coordenadas):
        """Calcular área de polígono usando fórmula de Shoelace"""
        if len(coordenadas) < 3:
            return 0
            
        # Fórmula de Shoelace para área en grados
        n = len(coordenadas)
        area = 0
        
        for i in range(n):
            j = (i + 1) % n
            area += coordenadas[i][0] * coordenadas[j][1]
            area -= coordenadas[j][0] * coordenadas[i][1]
        
        area = abs(area) / 2.0
        
        # Convertir a metros cuadrados (aproximado)
        # 1 grado ≈ 111,320 metros en el ecuador
        # Ajustar por latitud promedio
        lat_promedio = sum(coord[0] for coord in coordenadas) / len(coordenadas)
        factor_lat = math.cos(math.radians(lat_promedio))
        
        metros_por_grado_lat = 111320
        metros_por_grado_lon = 111320 * factor_lat
        
        area_m2 = area * metros_por_grado_lat * metros_por_grado_lon
        
        return area_m2
        
    def obtener_ubicacion(self, lat, lon):
        """Obtener departamento y provincia usando reverse geocoding"""
        try:
            # Usar Nominatim de OpenStreetMap
            url = f"https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'es'
            }
            
            headers = {
                'User-Agent': 'CampoSelector/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            address = data.get('address', {})
            
            # Extraer departamento/partido/distrito
            departamento = (address.get('county') or 
                          address.get('municipality') or 
                          address.get('city') or 
                          address.get('town') or 
                          address.get('village') or 
                          'No determinado')
            
            # Extraer provincia/estado
            provincia = (address.get('state') or 
                        address.get('province') or 
                        'No determinada')
            
            return departamento, provincia
            
        except Exception as e:
            print(f"Error obteniendo ubicación: {e}")
            return "No determinado", "No determinada"
            
    def update_results(self):
        """Actualizar resultados en la interfaz"""
        # Formatear área
        if self.area_m2 > 10000:  # Más de 1 hectárea
            hectareas = self.area_m2 / 10000
            area_text = f"{hectareas:.2f} hectáreas ({self.area_m2:.0f} m²)"
        else:
            area_text = f"{self.area_m2:.0f} m²"
            
        self.area_var.set(area_text)
        
        # Formatear ubicación
        location_text = f"{self.departamento}, {self.provincia}"
        self.location_var.set(location_text)
        
        # Mostrar coordenadas procesadas
        coords_text = f"Polígono con {len(self.coordenadas)} puntos:\n"
        for i, coord in enumerate(self.coordenadas):
            coords_text += f"Punto {i+1}: {coord[0]:.6f}, {coord[1]:.6f}\n"
            
        # Agregar centro del polígono
        centro_lat = sum(coord[0] for coord in self.coordenadas) / len(self.coordenadas)
        centro_lon = sum(coord[1] for coord in self.coordenadas) / len(self.coordenadas)
        coords_text += f"\nCentro del polígono: {centro_lat:.6f}, {centro_lon:.6f}"
            
        self.coords_output.delete(1.0, tk.END)
        self.coords_output.insert(1.0, coords_text)
        
        messagebox.showinfo("Éxito", "¡Área calculada exitosamente!")
        
    def load_from_file(self):
        """Cargar coordenadas desde archivo"""
        try:
            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo de coordenadas",
                filetypes=[("Archivos JSON", "*.json"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.coords_input.delete(1.0, tk.END)
                self.coords_input.insert(1.0, content)
                
                messagebox.showinfo("Éxito", "Archivo cargado. Ahora haz clic en 'Procesar Coordenadas'")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar archivo: {str(e)}")
            
    def export_coordinates(self):
        """Exportar coordenadas a archivo JSON"""
        if not self.coordenadas:
            messagebox.showwarning("Advertencia", "No hay coordenadas para exportar")
            return
            
        try:
            # Datos a exportar
            centro_lat = sum(coord[0] for coord in self.coordenadas) / len(self.coordenadas)
            centro_lon = sum(coord[1] for coord in self.coordenadas) / len(self.coordenadas)
            
            data = {
                'coordenadas': self.coordenadas,
                'area_m2': self.area_m2,
                'area_hectareas': self.area_m2 / 10000,
                'departamento': self.departamento,
                'provincia': self.provincia,
                'centro': {
                    'lat': centro_lat,
                    'lon': centro_lon
                },
                'fecha_procesamiento': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Seleccionar ubicación de archivo
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
                title="Guardar datos del campo"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                messagebox.showinfo("Éxito", f"Datos exportados a:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
            
    def clear_input(self):
        """Limpiar cuadro de entrada"""
        self.coords_input.delete(1.0, tk.END)
        
    def clear_results(self):
        """Limpiar resultados"""
        self.coordenadas = []
        self.area_m2 = 0
        self.departamento = ""
        self.provincia = ""
        
        self.area_var.set("No calculada")
        self.location_var.set("No determinada")
        self.coords_output.delete(1.0, tk.END)
        self.coords_input.delete(1.0, tk.END)
        
    def run(self):
        """Ejecutar aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import folium
        import requests
        from geopy.distance import geodesic
        
        print("Iniciando Selector de Campo...")
        app = MapApp()
        app.run()
        
    except ImportError as e:
        print(f"Error: Falta instalar dependencias: {e}")
        print("Ejecuta: pip install folium requests geopy")