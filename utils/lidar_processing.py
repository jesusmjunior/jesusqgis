import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, LineString
import rasterio
from rasterio.transform import from_origin
import os
import tempfile

def generate_lidar_sample(center_lat, center_lon, radius=0.05, points=1000, 
                         forest_ratio=0.7, water_ratio=0.1, terrain_variability=1.0):
    """
    Gera uma amostra de dados LiDAR simulados para uma área amazônica.
    
    Args:
        center_lat (float): Latitude central da amostra
        center_lon (float): Longitude central da amostra
        radius (float): Raio da área de amostragem em graus
        points (int): Número de pontos a gerar
        forest_ratio (float): Proporção da área coberta por floresta (0-1)
        water_ratio (float): Proporção da área coberta por água (0-1)
        terrain_variability (float): Multiplicador para variabilidade do terreno
        
    Returns:
        pd.DataFrame: DataFrame com dados LiDAR simulados
    """
    np.random.seed(42)  # Para reprodutibilidade
    
    # Gerar pontos em coordenadas polares e converter para cartesianas
    theta = np.random.uniform(0, 2*np.pi, points)
    r = radius * np.sqrt(np.random.uniform(0, 1, points))
    
    # Converter para coordenadas cartesianas
    x = center_lon + r * np.cos(theta)
    y = center_lat + r * np.sin(theta)
    
    # Criar máscara para diferentes tipos de terreno
    # Na Amazônia temos principalmente floresta, água e algum terreno aberto
    
    # Distância do centro normalizada (0-1)
    normalized_dist = r / radius
    
    # Determinar tipo de cobertura (simplificado):
    # 1: Floresta densa
    # 2: Água (rios, lagos)
    # 3: Vegetação baixa
    # 4: Solo exposto
    # 5: Construções/infraestrutura
    
    # Simulando um rio que corta a área (simplificação de um meandro)
    river_mask = np.abs(np.sin(theta * 2) * normalized_dist) < water_ratio
    
    # O resto divido entre floresta e outros tipos
    forest_mask = (~river_mask) & (np.random.random(points) < forest_ratio)
    vegetation_mask = (~river_mask) & (~forest_mask) & (np.random.random(points) < 0.7)
    soil_mask = (~river_mask) & (~forest_mask) & (~vegetation_mask) & (np.random.random(points) < 0.8)
    building_mask = (~river_mask) & (~forest_mask) & (~vegetation_mask) & (~soil_mask)
    
    # Criar array de classificação
    classification = np.zeros(points, dtype=int)
    classification[forest_mask] = 1  # Floresta
    classification[river_mask] = 2   # Água
    classification[vegetation_mask] = 3  # Vegetação baixa
    classification[soil_mask] = 4    # Solo exposto
    classification[building_mask] = 5  # Construções
    
    # Gerar altitudes simuladas que variam conforme o tipo de terreno
    # Base altitude + variação por tipo + distância do centro + ruído
    
    # Altitude base (metros acima do nível do mar)
    # Na Amazônia, altitudes típicas são baixas, entre 30-200m
    base_altitude = 60 + np.random.normal(0, 10)
    
    # Criar matriz de elevação
    z = np.zeros(points)
    
    # Água (rios, etc) - altitude mais baixa e plana
    z[river_mask] = base_altitude - 5 + np.random.normal(0, 0.5, np.sum(river_mask))
    
    # Floresta - maior variabilidade devido às copas das árvores
    forest_height = np.random.gamma(shape=9, scale=4, size=np.sum(forest_mask))  # Altura das árvores (média ~35m)
    terrain_under_forest = base_altitude + np.random.normal(0, 5, np.sum(forest_mask))  # Terreno sob a floresta
    z[forest_mask] = terrain_under_forest + forest_height
    
    # Vegetação baixa
    veg_height = np.random.gamma(shape=2, scale=1.5, size=np.sum(vegetation_mask))  # Altura média ~3m
    terrain_under_veg = base_altitude + np.random.normal(0, 3, np.sum(vegetation_mask))
    z[vegetation_mask] = terrain_under_veg + veg_height
    
    # Solo exposto - mais plano mas com alguma variação
    z[soil_mask] = base_altitude + np.random.normal(0, 2, np.sum(soil_mask))
    
    # Construções - altura variável
    build_height = np.random.gamma(shape=3, scale=2, size=np.sum(building_mask))  # Altura média ~6m
    terrain_under_build = base_altitude + np.random.normal(0, 1, np.sum(building_mask))
    z[building_mask] = terrain_under_build + build_height
    
    # Aplicar o fator de variabilidade global
    z = base_altitude + (z - base_altitude) * terrain_variability
    
    # Intensidade - varia por tipo de superfície
    intensity = np.zeros(points, dtype=int)
    intensity[forest_mask] = np.random.randint(40, 120, np.sum(forest_mask))      # Vegetação - reflexão média
    intensity[river_mask] = np.random.randint(5, 30, np.sum(river_mask))         # Água - baixa reflexão
    intensity[vegetation_mask] = np.random.randint(50, 150, np.sum(vegetation_mask))  # Vegetação baixa
    intensity[soil_mask] = np.random.randint(120, 220, np.sum(soil_mask))        # Solo - alta reflexão
    intensity[building_mask] = np.random.randint(150, 250, np.sum(building_mask))  # Construções - alta reflexão
    
    # Número de retornos (simulação simplificada)
    # Floresta tem mais retornos por pulso
    returns = np.ones(points, dtype=int)
    returns[forest_mask] = np.random.choice([1, 2, 3, 4], size=np.sum(forest_mask), 
                                            p=[0.2, 0.3, 0.3, 0.2])
    
    # Criar DataFrame
    df = pd.DataFrame({
        'X': x,
        'Y': y,
        'Z': z,
        'Intensity': intensity,
        'Classification': classification,
        'ReturnNumber': returns
    })
    
    return df

def export_lidar_to_csv(lidar_data, filename="lidar_data.csv"):
    """
    Exporta dados LiDAR para CSV em formato compatível com QGIS.
    
    Args:
        lidar_data (pd.DataFrame): DataFrame com dados LiDAR
        filename (str): Nome do arquivo para salvar
        
    Returns:
        str: Caminho do arquivo salvo
    """
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    # Garantir que temos as colunas necessárias
    required_cols = ['X', 'Y', 'Z', 'Intensity', 'Classification']
    for col in required_cols:
        if col not in lidar_data.columns:
            lidar_data[col] = 0
    
    # Adicionar metadados como comentários no início do arquivo
    with open(filepath, 'w') as f:
        f.write("# LIDAR data for QGIS - GAIA DIGITAL project\n")
        f.write("# CRS: EPSG:4326 (WGS 84)\n")
        f.write("# Classification codes:\n")
        f.write("# 1: Forest, 2: Water, 3: Low vegetation, 4: Ground, 5: Building\n")
    
    # Adicionar dados ao arquivo
    lidar_data.to_csv(filepath, index=False, mode='a')
    
    return filepath

def lidar_to_raster(lidar_data, attribute='Z', resolution=0.001, 
                    filename="lidar_raster.tif", method='mean'):
    """
    Converte dados LiDAR pontuais para um raster (DEM, DSM, etc)
    
    Args:
        lidar_data (pd.DataFrame): DataFrame com dados LiDAR
        attribute (str): Atributo a rasterizar ('Z', 'Intensity', etc)
        resolution (float): Resolução do raster em graus
        filename (str): Nome do arquivo para salvar
        method (str): Método de agregação ('mean', 'max', 'min', 'count')
        
    Returns:
        str: Caminho do arquivo raster salvo
    """
    # Obter limites da área
    xmin, ymin = lidar_data['X'].min() - resolution, lidar_data['Y'].min() - resolution
    xmax, ymax = lidar_data['X'].max() + resolution, lidar_data['Y'].max() + resolution
    
    # Calcular dimensões do raster
    width = int((xmax - xmin) / resolution)
    height = int((ymax - ymin) / resolution)
    
    # Inicializar array para o raster
    raster_data = np.zeros((height, width), dtype=np.float32)
    raster_data.fill(np.nan)  # Preencher com NaN (sem dados)
    
    # Para cada ponto, calcular a célula correspondente
    for _, point in lidar_data.iterrows():
        x, y = point['X'], point['Y']
        col = int((x - xmin) / resolution)
        row = int((ymax - y) / resolution)  # Inverter Y (raster começa no topo)
        
        # Garantir que estamos dentro dos limites
        if 0 <= row < height and 0 <= col < width:
            # Implementar diferentes métodos de agregação
            if method == 'max':
                if np.isnan(raster_data[row, col]) or point[attribute] > raster_data[row, col]:
                    raster_data[row, col] = point[attribute]
            elif method == 'min':
                if np.isnan(raster_data[row, col]) or point[attribute] < raster_data[row, col]:
                    raster_data[row, col] = point[attribute]
            elif method == 'count':
                if np.isnan(raster_data[row, col]):
                    raster_data[row, col] = 1
                else:
                    raster_data[row, col] += 1
            else:  # default: média
                if np.isnan(raster_data[row, col]):
                    raster_data[row, col] = point[attribute]
                else:
                    # Média cumulativa aproximada
                    raster_data[row, col] = (raster_data[row, col] + point[attribute]) / 2
    
    # Definir transformação geoespacial
    transform = from_origin(xmin, ymax, resolution, resolution)
    
    # Salvar como GeoTIFF
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    # Criar arquivo raster
    with rasterio.open(
        filepath,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=raster_data.dtype,
        crs='+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs',
        transform=transform,
    ) as dst:
        # Preencher NaN com valores nodata
        raster_data = np.nan_to_num(raster_data, nan=-9999)
        dst.write(raster_data, 1)
        dst.nodata = -9999
    
    return filepath

def create_contour_lines(raster_file, interval=5.0, filename="contour.gpkg"):
    """
    Cria linhas de contorno a partir de um raster de elevação.
    
    Args:
        raster_file (str): Caminho para o arquivo raster
        interval (float): Intervalo entre as curvas de nível
        filename (str): Nome do arquivo para salvar
        
    Returns:
        str: Caminho do arquivo de contornos salvo
    """
    import matplotlib.pyplot as plt
    from matplotlib.contour import QuadContourSet
    import rasterio
    
    # Abrir o arquivo raster
    with rasterio.open(raster_file) as src:
        elevation = src.read(1)
        transform = src.transform
        
        # Substituir valores nodata por NaN
        nodata = src.nodata
        elevation = np.where(elevation == nodata, np.nan, elevation)
        
        # Criar grade de coordenadas
        height, width = elevation.shape
        rows, cols = np.mgrid[0:height, 0:width]
        
        # Converter para coordenadas geográficas
        x_coords = transform[0] + cols * transform[1]
        y_coords = transform[3] + rows * transform[5]
        
        # Calcular os níveis para as curvas de contorno
        min_val = np.nanmin(elevation)
        max_val = np.nanmax(elevation)
        levels = np.arange(min_val - (min_val % interval), max_val + interval, interval)
        
        # Gerar contornos
        contour_set = plt.contour(x_coords, y_coords, elevation, levels=levels)
        plt.close()  # Fechar a figura para não exibi-la
        
        # Converter para GeoDataFrame
        contours = []
        elevations = []
        
        # Extrair os contornos
        for i, line in enumerate(contour_set.collections):
            for path in line.get_paths():
                if len(path.vertices) > 1:
                    contours.append(LineString(path.vertices))
                    elevations.append(contour_set.levels[i])
        
        # Criar GeoDataFrame
        gdf = gpd.GeoDataFrame({
            'elevation': elevations,
            'geometry': contours
        }, crs="EPSG:4326")
        
        # Salvar como GeoPackage
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        gdf.to_file(filepath, driver="GPKG")
        
        return filepath

def points_to_heatmap(points_gdf, attribute=None, resolution=0.001, 
                     radius=0.01, filename="heatmap.tif"):
    """
    Cria um mapa de calor a partir de pontos.
    
    Args:
        points_gdf (gpd.GeoDataFrame): GeoDataFrame com geometria de pontos
        attribute (str): Atributo para ponderação (None = sem ponderação)
        resolution (float): Resolução do raster em graus
        radius (float): Raio de influência de cada ponto
        filename (str): Nome do arquivo para salvar
        
    Returns:
        str: Caminho do arquivo de mapa de calor salvo
    """
    # Converter GeoDataFrame para DataFrame regular com coordenadas X e Y
    points_df = pd.DataFrame({
        'X': points_gdf.geometry.x,
        'Y': points_gdf.geometry.y
    })
    
    # Adicionar atributo de peso se especificado
    if attribute and attribute in points_gdf.columns:
        points_df['weight'] = points_gdf[attribute]
    else:
        points_df['weight'] = 1.0
    
    # Obter limites da área
    xmin, ymin = points_df['X'].min() - radius, points_df['Y'].min() - radius
    xmax, ymax = points_df['X'].max() + radius, points_df['Y'].max() + radius
    
    # Calcular dimensões do raster
    width = int((xmax - xmin) / resolution)
    height = int((ymax - ymin) / resolution)
    
    # Inicializar array para o raster
    heatmap = np.zeros((height, width), dtype=np.float32)
    
    # Converter raio de graus para células do raster
    radius_cells = int(radius / resolution)
    
    # Para cada ponto, calcular influência no mapa de calor
    for _, point in points_df.iterrows():
        x, y, weight = point['X'], point['Y'], point['weight']
        
        # Converter coordenadas para índices de célula
        center_col = int((x - xmin) / resolution)
        center_row = int((ymax - y) / resolution)
        
        # Calcular intervalos de células afetadas
        row_min = max(0, center_row - radius_cells)
        row_max = min(height, center_row + radius_cells + 1)
        col_min = max(0, center_col - radius_cells)
        col_max = min(width, center_col + radius_cells + 1)
        
        # Aplicar kernel gaussiano para suavização
        for row in range(row_min, row_max):
            for col in range(col_min, col_max):
                # Calcular distância ao centro
                dist = np.sqrt((row - center_row)**2 + (col - center_col)**2)
                
                # Se está dentro do raio, aplicar peso com decaimento gaussiano
                if dist <= radius_cells:
                    # Kernel gaussiano: e^(-(d²/r²)/2)
                    factor = np.exp(-0.5 * (dist / radius_cells)**2) * weight
                    heatmap[row, col] += factor
    
    # Definir transformação geoespacial
    transform = from_origin(xmin, ymax, resolution, resolution)
    
    # Salvar como GeoTIFF
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    # Normalizar para 0-1
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()
    
    # Criar arquivo raster
    with rasterio.open(
        filepath,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=heatmap.dtype,
        crs='+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs',
        transform=transform,
    ) as dst:
        dst.write(heatmap, 1)
    
    return filepath

# Exemplo de uso
if __name__ == "__main__":
    # Testar geração de dados LiDAR para uma área na Amazônia
    # Coordenadas próximas a Manaus (encontro das águas)
    test_lat, test_lon = -3.1, -60.0
    
    # Gerar dados LiDAR
    lidar_sample = generate_lidar_sample(
        center_lat=test_lat,
        center_lon=test_lon,
        radius=0.05,
        points=5000,
        forest_ratio=0.75,
        water_ratio=0.2
    )
    
    # Verificar os dados
    print(lidar_sample.head())
    print(f"Pontos gerados: {len(lidar_sample)}")
    
    # Estatísticas por classificação
    print("\nEstatísticas por tipo de terreno:")
    print(lidar_sample.groupby('Classification').agg({
        'Z': ['count', 'mean', 'min', 'max'],
        'Intensity': ['mean', 'min', 'max']
    }))
