import streamlit as st
import folium
from folium import plugins
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
import pandas as pd
import numpy as np
import os
import json
import requests
from dotenv import load_dotenv
import base64
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
import tempfile
import uuid
from PIL import Image
from io import BytesIO
import time

# Carregar variáveis de ambiente (para esconder chaves API)
load_dotenv()

# --------- CONFIGURAÇÃO DE API KEYS ---------
# Função para obter a chave da API Gemini de forma segura
def get_gemini_api_key():
    # Tenta obter do .env primeiro
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Se não encontrar no .env, verifica variáveis de ambiente do sistema
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    # Se ainda não encontrar, usa valor de fallback (apenas para desenvolvimento)
    if not api_key:
        # Para propósitos de demonstração, a chave é armazenada criptografada
        # Em produção, NUNCA use este método - sempre use variáveis de ambiente
        encoded_key = "QUl6YVN5RG8zTTZKejI2UVJ4Sm14Qzc2NW5TbElRSktEdmhXN0k4"
        api_key = base64.b64decode(encoded_key).decode('utf-8')
    
    return api_key

# Inicializar configuração da página
st.set_page_config(
    page_title="GAIA DIGITAL - GeoAnálise Amazônica",
    page_icon="🌎",
    layout="wide"
)

# --------- FUNÇÕES DE PROCESSAMENTO GEMINI API ---------
def query_gemini_api(prompt, temperature=0.2):
    """Consulta a API Gemini para geração de conteúdo."""
    api_key = get_gemini_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 2048
        }
    }
    
    with st.spinner("Processando com IA..."):
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            try:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                st.error(f"Erro ao processar resposta da API: {e}")
                return None
        else:
            st.error(f"Erro na API Gemini: {response.status_code} - {response.text}")
            return None

def extract_coordinates_from_text(text):
    """Extrai coordenadas geográficas do texto usando Gemini API."""
    prompt = f"""
    Analise o seguinte texto e extraia todas as coordenadas geográficas mencionadas.
    Retorne APENAS um array JSON no formato:
    [
        {{
            "lat": latitude,
            "lon": longitude,
            "name": "nome ou descrição do local",
            "type": "tipo de ponto (cidade, rio, floresta, etc)"
        }}
    ]
    
    Se não houver coordenadas claras, inferir baseado em locais mencionados na Amazônia.
    IMPORTANTE: Responda SOMENTE com o JSON, sem explicações adicionais.
    
    Texto: {text}
    """
    
    result = query_gemini_api(prompt, temperature=0.1)
    
    if result:
        try:
            # Encontra o primeiro array JSON no texto
            import re
            json_match = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                coords = json.loads(json_str)
                return coords
            else:
                st.warning("Formato de coordenadas não identificado na resposta.")
                return []
        except Exception as e:
            st.error(f"Erro ao processar coordenadas: {e}")
            return []
    return []

# --------- FUNÇÕES DE PROCESSAMENTO GEOESPACIAL ---------
def generate_lidar_sample(center_lat, center_lon, radius=0.05, points=1000):
    """Gera uma amostra de dados LiDAR simulados ao redor de um ponto central."""
    np.random.seed(42)  # Para reprodutibilidade
    
    # Gerar pontos aleatórios dentro de um círculo
    theta = np.random.uniform(0, 2*np.pi, points)
    r = radius * np.sqrt(np.random.uniform(0, 1, points))
    
    # Converter para coordenadas cartesianas
    x = center_lon + r * np.cos(theta)
    y = center_lat + r * np.sin(theta)
    
    # Gerar altitudes simuladas (valores Z) - em áreas de floresta, variam bastante
    # Base altitude + variação baseada em distância do centro + ruído
    base_altitude = 100  # metros acima do nível do mar
    z = base_altitude + (1 - r/radius) * 50 + np.random.normal(0, 10, points)
    
    # Retornar como DataFrame
    return pd.DataFrame({
        'X': x,
        'Y': y,
        'Z': z,
        'Intensity': np.random.randint(0, 255, points),
        'Classification': np.random.choice([1, 2, 3, 4, 5], points, p=[0.05, 0.7, 0.1, 0.1, 0.05])
    })

def export_lidar_to_csv(lidar_data, filename="lidar_data.csv"):
    """Exporta dados LiDAR para CSV."""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    lidar_data.to_csv(filepath, index=False)
    return filepath

def create_qgis_style_file(filepath, icon_type="ship"):
    """Cria um arquivo de estilo QGIS para a caravela."""
    qml_content = f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="singleSymbol" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol name="0" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="SvgMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="fixedAspectRatio" v="0"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="transport/transport_nautical_harbour.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_width" v="0.2"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="4"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
</qgis>
"""
    
    style_filepath = f"{filepath}.qml"
    with open(style_filepath, 'w') as f:
        f.write(qml_content)
    return style_filepath

def create_qgis_project_file(data_files, output_file="amazon_project.qgs"):
    """Cria um arquivo de projeto QGIS simples."""
    # Esta é uma versão simplificada - em produção usaríamos
    # bibliotecas específicas como qgis.core se disponível
    qgis_xml = f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="Projeto Amazônia GAIA DIGITAL" version="3.22.0-Białowieża">
  <projectCrs>
    <spatialrefsys>
      <wkt>GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]</wkt>
      <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
      <srsid>3452</srsid>
      <srid>4326</srid>
      <authid>EPSG:4326</authid>
      <description>WGS 84</description>
      <projectionacronym>longlat</projectionacronym>
      <ellipsoidacronym>WGS84</ellipsoidacronym>
      <geographicflag>true</geographicflag>
    </spatialrefsys>
  </projectCrs>
  <mapcanvas name="theMapCanvas">
    <units>degrees</units>
    <extent>
      <xmin>-65.0</xmin>
      <ymin>-10.0</ymin>
      <xmax>-50.0</xmax>
      <ymax>0.0</ymax>
    </extent>
    <rotation>0</rotation>
  </mapcanvas>
  <layer-tree-group>
    <layer-tree-layer id="1" name="Camadas GAIA DIGITAL" checked="Qt::Checked">
    </layer-tree-layer>
  </layer-tree-group>
</qgis>
"""
    
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, output_file)
    with open(filepath, 'w') as f:
        f.write(qgis_xml)
    return filepath

def export_to_geojson(gdf, filename):
    """Exporta GeoDataFrame para GeoJSON."""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    gdf.to_file(filepath, driver='GeoJSON')
    return filepath

def create_download_link(file_path, link_text):
    """Cria um link para download de um arquivo."""
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    filename = os.path.basename(file_path)
    mime_type = "application/octet-stream"
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{link_text}</a>'
    return href

# --------- INTERFACE DO APLICATIVO STREAMLIT ---------
st.title("🌎 GAIA DIGITAL - Análise Geoespacial Amazônica")
st.markdown("""
Este aplicativo gera mapas e análises geoespaciais para a região Amazônica,
utilizando inteligência artificial para processar descrições textuais e gerar
camadas compatíveis com QGIS, incluindo dados LiDAR simulados.
""")

# Barra lateral com opções
st.sidebar.title("Configurações")
st.sidebar.image("https://via.placeholder.com/150?text=GAIA+DIGITAL", width=150)

# Área de entrada de texto
text_input = st.text_area(
    "Descreva a região amazônica de interesse:", 
    value="Quero analisar a região próxima a Manaus, especialmente as áreas de confluência do Rio Negro com o Rio Solimões, onde ocorrem fenômenos de encontro das águas. Estou interessado em identificar potenciais anomalias na vegetação e áreas de desmatamento recente.",
    height=150
)

# Configurações avançadas na barra lateral
with st.sidebar.expander("Configurações Avançadas"):
    lidar_density = st.slider("Densidade de pontos LiDAR", 100, 5000, 1000)
    lidar_radius = st.slider("Raio da amostra LiDAR (graus)", 0.01, 0.2, 0.05)
    ai_temperature = st.slider("Temperatura IA", 0.0, 1.0, 0.2)
    
# Botão para processar
if st.button("Processar e Gerar Mapa"):
    # Extrair coordenadas do texto usando IA
    with st.spinner("Processando texto com IA para extrair coordenadas..."):
        coordinates = extract_coordinates_from_text(text_input)
        
        if not coordinates:
            # Fallback para coordenadas padrão da Amazônia Central se a IA não encontrar
            coordinates = [
                {"lat": -3.1, "lon": -60.0, "name": "Manaus", "type": "cidade"},
                {"lat": -3.3, "lon": -60.2, "name": "Encontro das Águas", "type": "rio"}
            ]
            st.info("Usando coordenadas padrão da região de Manaus")
    
    # Criar GeoDataFrame com os pontos
    points_data = []
    for coord in coordinates:
        points_data.append({
            'geometry': Point(coord['lon'], coord['lat']),
            'name': coord['name'],
            'type': coord['type']
        })
    
    points_gdf = gpd.GeoDataFrame(points_data, crs="EPSG:4326")
    
    # Criar mapa base
    center_lat = points_gdf.geometry.y.mean()
    center_lon = points_gdf.geometry.x.mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Adicionar camada de satélite
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
    ).add_to(m)
    
    # Gerar dados LiDAR simulados
    lidar_data = generate_lidar_sample(center_lat, center_lon, lidar_radius, lidar_density)
    
    # Adicionar pontos ao mapa
    for idx, point in points_gdf.iterrows():
        popup_text = f"""
        <b>{point['name']}</b><br>
        Tipo: {point['type']}<br>
        Lat: {point.geometry.y:.6f}<br>
        Lon: {point.geometry.x:.6f}
        """
        
        icon = folium.Icon(icon='ship', prefix='fa') if point['type'] == 'rio' else folium.Icon(icon='leaf', prefix='fa')
        
        folium.Marker(
            location=[point.geometry.y, point.geometry.x],
            popup=folium.Popup(popup_text, max_width=300),
            icon=icon
        ).add_to(m)
    
    # Adicionar minimap
    plugins.MiniMap().add_to(m)
    
    # Adicionar controle de camadas
    folium.LayerControl().add_to(m)
    
    # Exibir mapa
    st.subheader("Mapa Interativo")
    folium_static(m)
    
    # Visualizar dados LiDAR
    st.subheader("Visualização de Dados LiDAR (Simulados)")
    
    # Criar figura para visualização 3D simplificada
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(
        lidar_data['X'], 
        lidar_data['Y'], 
        c=lidar_data['Z'], 
        cmap='terrain', 
        alpha=0.6, 
        s=2
    )
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Dados LiDAR Simulados (Vista de Topo)')
    plt.colorbar(scatter, label='Elevação (m)')
    st.pyplot(fig)
    
    # Criar arquivos para download
    lidar_csv = export_lidar_to_csv(lidar_data, "amazonia_lidar.csv")
    points_geojson = export_to_geojson(points_gdf, "pontos_amazonia.geojson")
    style_file = create_qgis_style_file(points_geojson)
    qgis_project = create_qgis_project_file([lidar_csv, points_geojson])
    
    # Seção de downloads
    st.subheader("Exportar para QGIS")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Dados")
        st.markdown(create_download_link(lidar_csv, "⬇️ Download Dados LiDAR (CSV)"), unsafe_allow_html=True)
        st.markdown(create_download_link(points_geojson, "⬇️ Download Pontos (GeoJSON)"), unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Arquivos QGIS")
        st.markdown(create_download_link(style_file, "⬇️ Download Estilo Caravela (QML)"), unsafe_allow_html=True)
        st.markdown(create_download_link(qgis_project, "⬇️ Download Projeto QGIS"), unsafe_allow_html=True)
    
    # Instruções para QGIS
    with st.expander("Como importar no QGIS"):
        st.markdown("""
        1. Baixe todos os arquivos acima
        2. Abra o QGIS e crie um novo projeto 
        3. Para importar os dados LiDAR:
           - Vá para "Camada > Adicionar Camada > Adicionar Camada de Texto Delimitado"
           - Selecione o arquivo CSV baixado
           - Especifique "X" como longitude e "Y" como latitude
           - Selecione CRS EPSG:4326 (WGS 84)
        4. Para importar os pontos com ícone de caravela:
           - Vá para "Camada > Adicionar Camada > Adicionar Camada Vetorial"
           - Selecione o arquivo GeoJSON baixado
           - Clique com botão direito na camada > Propriedades > Simbologia
           - Clique em "Carregar Estilo" e selecione o arquivo QML baixado
        5. Alternativamente, abra diretamente o arquivo de projeto QGIS
        """)
        
    # Análise avançada com IA
    with st.expander("Análise Avançada com IA"):
        if st.button("Realizar Análise Avançada"):
            prompt = f"""
            Realize uma análise geoespacial da seguinte região amazônica:
            {text_input}
            
            Locais identificados:
            {', '.join([f"{c['name']} ({c['type']})" for c in coordinates])}
            
            Forneça uma análise detalhada sobre:
            1. Potenciais riscos ambientais na região
            2. Características geomorfológicas notáveis
            3. Recomendações para monitoramento ambiental
            4. Pontos de interesse para um estudo de campo
            
            Estruture a resposta em tópicos claros.
            """
            
            analysis = query_gemini_api(prompt, temperature=ai_temperature)
            if analysis:
                st.markdown(analysis)
            else:
                st.error("Não foi possível gerar a análise. Tente novamente mais tarde.")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info(
    "GAIA DIGITAL - Projeto para OpenAI to Z Challenge\n\n"
    "Especialista GeoPython-QGIS © 2025"
)
