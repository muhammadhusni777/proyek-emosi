import numpy as np
import math
from math import sin, cos, sqrt, atan2, radians, atan
import pandas as pd
from fastkml import kml
from shapely.geometry import Point, Polygon
from shapely.geometry import LineString
import os

import random

from geopy.distance import geodesic


# Create a KML object
k = kml.KML()

# Create a Document
document = kml.Document()

jarak = 0

ship_passing = 0
total_ship_passing = 0

ship_passing_state = 0
ship_passing_state_prev = 0

ship_name = ""

# Create a placemark for the polyline
placemark = kml.Placemark()

# Define the style for the polyline (orange color, 2 px width)
style = """
<Style>
    <LineStyle>
        <color>ff00a5ff</color>  <!-- Kode warna oranye dalam format ABGR -->
        <width>3</width>
    </LineStyle>
</Style>
"""

placemark.style = style


def filter_nearby_points(latitudes, longitudes, min_distance=100):
    """
    Menghilangkan titik yang jaraknya kurang dari min_distance meter dari titik lainnya.
    """
    # Array untuk menyimpan titik yang sudah dipilih
    filtered_latitudes = []
    filtered_longitudes = []
    
    for i in range(len(latitudes)):
        point = (latitudes[i], longitudes[i])
        is_far_enough = True
        
        # Periksa jarak ke setiap titik yang sudah ada di filtered
        for j in range(len(filtered_latitudes)):
            existing_point = (filtered_latitudes[j], filtered_longitudes[j])
            distance = geodesic(point, existing_point).meters
            
            if distance < min_distance:
                is_far_enough = False
                break

        # Jika jaraknya cukup jauh, tambahkan ke hasil
        if is_far_enough:
            filtered_latitudes.append(latitudes[i])
            filtered_longitudes.append(longitudes[i])
    
    return filtered_latitudes, filtered_longitudes






# Function to load corridor coordinates from KML file
def load_koridor_from_kml(filename):
    with open(filename, 'rb') as file:  # Open file in 'rb' (read binary) mode
        doc = file.read()
    
    # Remove encoding declaration if present
    doc = doc.replace(b'<?xml version="1.0" encoding="UTF-8"?>', b'')
    
    k = kml.KML()
    k.from_string(doc.decode("utf-8"))  # Decode to UTF-8

    # Assuming the corridor is at the first level of the KML
    features = list(k.features())
    placemarks = list(features[0].features())
    
    # Get coordinates from the first polygon in the KML
    for placemark in placemarks:
        if placemark.geometry.geom_type == 'Polygon':
            return Polygon(placemark.geometry.exterior.coords)



def map_angle_conversion(lat1, long1, lat2, long2):
    delta_lat = (lat1 - lat2)*111000
    delta_lon = (long1 - long2)*111000
    map_angle_conversion = math.atan2(float(delta_lon),float(delta_lat)) * (180/math.pi)
    return map_angle_conversion


# Function to check if a point is within the corridor
def is_within_koridor(latitude, longitude, koridor_polygon):
    point = Point(longitude, latitude)  # Shapely uses (longitude, latitude)
    return koridor_polygon.contains(point), point



# Function to find the nearest point on the corridor polygon
def nearest_point_on_koridor(point, koridor_polygon):
    return koridor_polygon.exterior.interpolate(koridor_polygon.exterior.project(point))


def meter_conversion(lat1, long1, lat2, long2):
    delta_lat = (lat1 - lat2)*111000
    delta_lon = (long1 - long2)*111000
    distance = sqrt(pow(delta_lat, 2) +  pow(delta_lon, 2))
    return distance


def nearest_point_in_koridor(point, koridor_polygon, alpha, variation=0):
    if koridor_polygon.contains(point):
        return point.x, point.y  # Titik sudah dalam koridor
    else:
        # Cari titik terdekat di batas koridor
        nearest_point = koridor_polygon.boundary.interpolate(koridor_polygon.boundary.project(point))

        # Sudut alpha dalam radian
        alpha_rad = math.radians(alpha)
        
        # Komponen perubahan delta (latitude dan longitude) berdasarkan sudut tegak lurus
        delta_lat = variation * math.cos(alpha_rad) / 111110
        delta_lon = variation * math.sin(alpha_rad) / (111110 * abs(math.cos(math.radians(nearest_point.y))))
        
        # Tambahkan variasi acak sesuai toleransi (±variation meter)
        delta_lat += random.uniform(-variation, variation) / 111110
        delta_lon += random.uniform(-variation, variation) / (111110 * abs(math.cos(math.radians(nearest_point.y))))
        
        # Kembalikan titik baru yang berada tegak lurus terhadap sudut alpha
        return nearest_point.y + delta_lat, nearest_point.x + delta_lon

# Load corridor from KML file
koridor_polygon = load_koridor_from_kml('coridorslim.kml')

koridor_cable_zone = load_koridor_from_kml('cable_side.kml')

# Dapatkan folder yang sama dengan file Python
folder_path = os.getcwd()  # Mengambil direktori saat ini

# Dapatkan daftar semua file dan folder di folder saat ini
files_and_folders = os.listdir(folder_path)

# Filter hanya nama file dengan ekstensi .csv
csv_files = [f for f in files_and_folders if f.endswith('.csv') and os.path.isfile(os.path.join(folder_path, f))]


alpha = 100
# Tampilkan semua nama file CSV
print("Nama file CSV di folder saat ini:")
for csv_file in csv_files:
    print(csv_file)

    #-----------------------LOOP PROGRAM DIMULAI---------------------------------------------------#


    # Membaca file CSV ke dalam DataFrame
    #csv_file='13-sep-2024.csv'
    df = pd.read_csv(csv_file)  # Ganti 'file.csv' dengan path ke file CSV Anda

    # Mengambil kolom 'latitude' saja dan mengonversi ke array NumPy
    latitude_raw = df['LATITUDE'].to_numpy()
    longitude_raw = df['LONGITUDE'].to_numpy()
    ship_name = df['name'].to_numpy()
    
    latitudes = []
    longitudes= []
    
    for i in range(1, len(latitude_raw)):
        jarak = meter_conversion(latitude_raw[i - 1], longitude_raw[i - 1], latitude_raw[i], longitude_raw[i])
        if jarak > 50:  
            latitudes.append(latitude_raw[i])
            longitudes.append(longitude_raw[i])
    
    print(len(latitude_raw),len(latitudes))
    print((latitude_raw),(latitudes))
    print(len(longitude_raw), len(longitudes))
    
    


    

    #latitudes = np.array([-7.758377, -7.759076, -7.762117])  # Contoh array latitude
    #longitudes = np.array([109.020631, 109.025859, 109.031052])  # Contoh array longitude

    latitudes_memory = []
    longitudes_memory = []
    latitudes_memory_buffer = []
    longitudes_memory_buffer = []

    # Loop through each segment of latitude and longitude pairs
    for i in range(len(latitudes) - 1):
        latitude_buffer = np.linspace(latitudes[i], latitudes[i + 1], 3)  
        longitude_buffer = np.linspace(longitudes[i], longitudes[i + 1], 3)
        
        # Extend the memory arrays with the new buffer points
        latitudes_memory_buffer.extend(latitude_buffer)
        longitudes_memory_buffer.extend(longitude_buffer)

    # Display results
    latitudes_memory, longitudes_memory = filter_nearby_points(latitudes_memory_buffer, longitudes_memory_buffer, min_distance=100)
    
    
    print("Latitude memory:", latitudes_memory)
    print(len(latitudes_memory))
    print("Longitude memory:", longitudes_memory)

    
    latitude_fixed = []
    longitude_fixed = []
    
    print(len(latitude_buffer))
    
    # Periksa setiap titik dalam array
    for lat, lon in zip(latitudes_memory, longitudes_memory):
        is_within, point = is_within_koridor(lat, lon, koridor_polygon)
        
        if is_within:
            #print(f"Titik ({lat}, {lon}) berada di dalam koridor.")
            # Tambahkan ke list fixed
            latitude_fixed.append(lat)
            longitude_fixed.append(lon)
            
        else:
            nearest_point = nearest_point_on_koridor(point, koridor_polygon)
            #print(f"Titik ({lat}, {lon}) berada di luar koridor. Titik terdekat di koridor: {nearest_point.y}, {nearest_point.x}")
            # Tambahkan titik terdekat ke list fixed
            nearest_lat, nearest_lon = nearest_point_in_koridor(point, koridor_polygon, alpha)
            #latitude_fixed.append(lat)
            #longitude_fixed.append(lon)
            latitude_fixed.append(nearest_lat)
            longitude_fixed.append(nearest_lon)
        
        #print("res", latitude_fixed, longitude_fixed)
            
             
        
    
    
    
    for i in range(len(latitude_fixed)):
        is_within, point = is_within_koridor(latitude_fixed[i], longitude_fixed[i], koridor_cable_zone)
        if is_within:
            #print(f"Titik ({lat}, {lon}) berada di dalam zona.")
            ship_passing_state = 1
        else:
            #print(f"Titik ({lat}, {lon}) berada di luar zona.")
            ship_passing_state = 0
        
        if (ship_passing_state != ship_passing_state_prev):
            ship_passing = ship_passing + 1
            print("ship pass")
        
        ship_passing_state_prev = ship_passing_state
        
    print("ship passing", ship_passing)
    
    # Mencetak dan menyimpan ke file
    with open(f"ship passing  {csv_file}.txt", "w") as file:
        output = f"ship passing : {ship_passing}\n"
        print(output.strip())
        file.write(output)
    
    
    total_ship_passing = total_ship_passing + ship_passing
    
    ship_passing = 0
    #print(latitude_fixed, longitude_fixed)

    # Pastikan latitudes dan longitudes memiliki panjang yang sama
    if len(latitude_fixed) == len(longitude_fixed):
        # Buat list of tuples untuk coordinates
        
        coordinates = list(zip(longitude_fixed, latitude_fixed))  # Menggabungkan menjadi (lon, lat)
    else:
        raise ValueError("Arrays latitudes dan longitudes harus memiliki panjang yang sama.")

    #print("Koordinat yang dihasilkan:")
    #print(coordinates)




    #--------------EXTEND THE POINT-------------------------#   
    latitudes_draw_buffer = []
    longitudes_draw_buffer = []
    
    
    # Loop through each segment of latitude and longitude pairs
    for i in range(len(latitude_fixed) - 1):
        latitude_buffer_draw = np.linspace(latitude_fixed[i], latitude_fixed[i + 1], 3)  
        longitude_buffer_draw = np.linspace(longitude_fixed[i], longitude_fixed[i + 1], 3)
        
        # Extend the memory arrays with the new buffer points
        latitudes_draw_buffer.extend(latitude_buffer_draw)
        longitudes_draw_buffer.extend(longitude_buffer_draw)
    
    latitude_draw = []
    longitude_draw = []
    
        
    for lat, lon in zip(latitudes_draw_buffer, longitudes_draw_buffer):
        is_within, point = is_within_koridor(lat, lon, koridor_polygon)
        
        if is_within:
            #print(f"Titik ({lat}, {lon}) berada di dalam koridor.")
            # Tambahkan ke list fixed
            latitude_draw.append(lat)
            longitude_draw.append(lon)
            
        else:
            nearest_point = nearest_point_on_koridor(point, koridor_polygon)
            #print(f"Titik ({lat}, {lon}) berada di luar koridor. Titik terdekat di koridor: {nearest_point.y}, {nearest_point.x}")
            # Tambahkan titik terdekat ke list fixed
            nearest_lat, nearest_lon = nearest_point_in_koridor(point, koridor_polygon, alpha)
            #latitude_fixed.append(lat)
            #longitude_fixed.append(lon)
            latitude_draw.append(nearest_lat)
            longitude_draw.append(nearest_lon)

    print(latitude_draw)
    print("-----------")
    print(longitude_draw)



    # Menyimpan hasil ke dalam KML
    kml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    kml_content += '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
    kml_content += '  <Document>\n'


        
   # Menambahkan Style untuk warna merah
    kml_content += '<Style id="red_style">\n'
    kml_content += '  <IconStyle>\n'
    kml_content += '    <color>ff0000ff</color>\n'  # Format ARGB
    kml_content += '    <Icon>\n'
    kml_content += '      <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>\n'
    kml_content += '    </Icon>\n'
    kml_content += '  </IconStyle>\n'
    kml_content += '</Style>\n'

    # Menambahkan titik-titik yang diperbaiki sebagai Placemarks dengan Style
    for idx, (lat, lon) in enumerate(zip(latitudes, longitudes), start=1):
        kml_content += '    <Placemark>\n'
        kml_content += f'      <name>Point {idx}</name>\n'
        kml_content += '      <styleUrl>#red_style</styleUrl>\n'  # Menggunakan Style yang telah didefinisikan
        kml_content += '      <Point>\n'
        kml_content += f'        <coordinates>{lon},{lat},0</coordinates>\n'
        kml_content += '      </Point>\n'
        kml_content += '    </Placemark>\n'
        
        
    for idx, (lat, lon) in enumerate(zip(latitude_draw, longitude_draw), start=1):
        kml_content += '    <Placemark>\n'
        kml_content += f'      <name>Point {idx}</name>\n'
        kml_content += '      <Point>\n'
        kml_content += f'        <coordinates>{lon},{lat},0</coordinates>\n'
        kml_content += '      </Point>\n'
        kml_content += '    </Placemark>\n'
        
        
    
    
    # Menambahkan garis (LineString) dengan warna oranye
    kml_content += '    <Placemark>\n'
    kml_content += f'      <name>csv_file</name>\n'
    kml_content += '      <Style>\n'
    kml_content += '        <LineStyle>\n'
    #kml_content += '          <color>ff7f00ff</color>  <!-- Oranye -->\n'   #ff007f
    kml_content += '           <color>ff00aaff</color>  <!-- Oranye -->\n'   #ff007f

    kml_content += '          <width>3</width>\n'
    kml_content += '        </LineStyle>\n'
    kml_content += '      </Style>\n'
    kml_content += '      <LineString>\n'
    kml_content += '        <coordinates>\n'
    for lat, lon in zip(latitude_draw, longitude_draw):
        kml_content += f'          {lon},{lat},0\n'
    kml_content += '        </coordinates>\n'
    kml_content += '      </LineString>\n'
    kml_content += '    </Placemark>\n'

    kml_content += '  </Document>\n'
    kml_content += '</kml>'

    # Simpan KML ke file 'koridor_diperbarui.kml'
    with open(f'{csv_file}.kml', 'w') as file:
        file.write(kml_content)

    print(f'disimpan di {csv_file}.kml')
    
    
    
    latitudes_memory = []
    longitudes_memory = []
    
    latitudes = []
    longitudes= []
    
    
    latitudes_fixed = []
    longitudes_fixed = []

try:
    with open(f"{ship_name[1]} total passing .txt", "w") as file:
        output = f"{ship_name[1]} ship passing : {total_ship_passing}\n"
        print(output.strip())
        file.write(output)
except:
    pass
