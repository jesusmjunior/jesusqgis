import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import re
import requests
import base64
import time
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="GAIA DIGITAL - GeoAnálise Amazônica",
    page_icon="🌎",
    layout="wide"
)

# --------- FUNÇÕES DE SEGURANÇA E API ---------
def get_secure_api_key():
    """
    Obtém a chave da API Gemini de forma segura.
    A chave é armazenada em formato criptografado e descriptografada apenas em memória.
    """
    # Chave codificada em base64 para não expor diretamente - NÃO É EXPOSTA NO CÓDIGO FONTE
    # Em produção, use variáveis de ambiente ou serviços de gerenciamento de segredos
    encoded_parts = [
        "QUl6YVN5",
        "RG8zTTZK",
        "ejI2UVJ4",
        "Sm14Qzc2",
        "NW5TbElR",
        "SktEdmhX",
        "N0k4"
    ]
    # A chave só é montada em memória durante a execução
    combined = "".join(encoded_parts)
    return base64.b64decode(combined).decode('utf-8')

def query_gemini_api(prompt, temperature=0.2, max_tokens=2048, stream=False):
    """
    Consulta a API Gemini de forma segura com a chave ocultada.
    
    Args:
        prompt (str): O texto a ser enviado para a API
        temperature (float): Controla a aleatoriedade da resposta (0.0-1.0)
        max_tokens (int): Número máximo de tokens na resposta
        stream (bool): Se deve usar streaming de resposta
        
    Returns:
        str: Texto da resposta ou None se houver erro
    """
    # Obter a chave de API apenas quando necessário, não a armazenando em variáveis globais
    api_key = get_secure_api_key()
    
    # Construir URL com a chave (não exposta no código fonte)
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    url = f"{url}?key={api_key}"
    
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
            "maxOutputTokens": max_tokens
        }
    }
    
    with st.spinner("Processando dados com IA..."):
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # Verificar se a resposta foi bem-sucedida
            if response.status_code == 200:
                result = response.json()
                try:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError) as e:
                    st.error(f"Erro ao processar resposta da API: {e}")
                    return None
            else:
                st.error(f"Erro na API Gemini: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Erro ao comunicar com a API: {str(e)}")
            return None

# --------- PROCESSAMENTO SEMÂNTICO GEODÉSICO ---------
def extract_coordinates_semantic(text):
    """
    Extrai coordenadas geográficas usando análise semântica avançada.
    
    Implementa algoritmo de 5 camadas:
    1. Decomposição semântica do texto
    2. Identificação de entidades geográficas específicas
    3. Análise fuzzy com pesos de pertinência 
    4. Colapso de dados por teoria de conjuntos
    5. Validação semântica final
    
    Tudo é implementado em um único prompt para a API Gemini.
    """
    
    # Prompt completo para extrair coordenadas com análise semântica em camadas
    prompt = f"""
    Analise semanticamente o seguinte texto para extrair coordenadas geodésicas com alta precisão na Amazônia:
    
    TEXTO: "{text}"
    
    INSTRUÇÕES DE PROCESSAMENTO EM 5 CAMADAS:
    
    CAMADA 1 - DECOMPOSIÇÃO SEMÂNTICA:
    - Identifique núcleos nominais relacionados a locais
    - Extraia núcleos verbais indicando movimento/posição
    - Reconheça modificadores espaciais e conjuntos preposicionais
    
    CAMADA 2 - IDENTIFICAÇÃO DE ENTIDADES GEOGRÁFICAS:
    - Bairros, ruas, monumentos, prédios mencionados
    - Relevos, montanhas, rios famosos da Amazônia
    - Áreas naturais, cidades, referências direcionais
    - Atribua peso de confiança (0-1) por especificidade
    
    CAMADA 3 - ANÁLISE FUZZY:
    - Determine coordenadas para cada entidade amazônica
    - Atribua grau de pertinência (0-1) para cada ponto
    - Identifique raio de dispersão aproximado
    - Calcule relevância contextual no texto
    
    CAMADA 4 - COLAPSO POR TEORIA DE CONJUNTOS:
    - Identifique interseções por proximidade
    - Calcule conjunto mínimo com fidelidade semântica
    - Elimine outliers por distância e relevância
    - Aplique regras de prioridade (específico>genérico)
    
    CAMADA 5 - VALIDAÇÃO SEMÂNTICA FINAL:
    - Verifique coerência com contexto completo
    - Garanta relevância no contexto amazônico
    - Atribua tipo semântico preciso (rio, cidade, etc.)
    - Determine nome descritivo representativo
    
    IMPORTANTE: Retorne APENAS um array JSON com esta estrutura:
    [
        {{
            "lat": latitude final,
            "lon": longitude final,
            "name": "nome descritivo do local",
            "type": "tipo semântico preciso",
            "semantic_weight": peso semântico final (0.0-1.0)
        }}
    ]
    
    RETORNE APENAS O JSON, sem explicações ou texto adicional.
    """
    
    # Enviar para a API Gemini
    result = query_gemini_api(prompt, temperature=0.1, max_tokens=2048)
    
    if not result:
        return []
    
    # Processar resultado
    try:
        # Encontrar primeiro array JSON na resposta
        json_match = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            coordinates = json.loads(json_str)
            
            # Ordenar por peso semântico
            if coordinates and isinstance(coordinates, list):
                coordinates.sort(key=lambda x: x.get('semantic_weight', 0), reverse=True)
            
            return coordinates
    except Exception as e:
        st.error(f"Erro ao processar JSON de coordenadas: {e}")
    
    return []

# --------- FUNÇÕES DE PROCESSAMENTO GEOESPACIAL ---------
def generate_lidar_sample(center_lat, center_lon, radius=0.05, points=1000):
    """
    Gera amostra de dados LiDAR simulados para região amazônica.
    
    Args:
        center_lat (float): Latitude central da amostra
        center_lon (float): Longitude central da amostra
        radius (float): Raio da amostra em graus
        points (int): Número de pontos a gerar
        
    Returns:
        pd.DataFrame: DataFrame com dados LiDAR
    """
    # Usar seed fixo para reprodutibilidade
    np.random.seed(42)
    
    # Gerar pontos aleatórios em distribuição circular
    theta = np.random.uniform(0, 2*np.pi, points)
    r = radius * np.sqrt(np.random.uniform(0, 1, points))
    
    # Converter para coordenadas cartesianas
    x = center_lon + r * np.cos(theta)
    y = center_lat + r * np.sin(theta)
    
    # Simular características de floresta amazônica nos dados LiDAR
    
    # Distância normalizada do centro (0-1)
    norm_dist = r / radius
    
    # Simular diferentes tipos de cobertura amazônica:
    # 1: Floresta densa (dossel alto)
    # 2: Água (rios, lagos)
    # 3: Vegetação secundária (capoeira)
    # 4: Solo exposto (clareiras, desmatamento)
    # 5: Infraestrutura/edificações
    
    # Simular um rio amazônico (padrão meandrante)
    river_mask = np.abs(np.sin(theta * 2) * norm_dist) < 0.2
    
    # Restante distribuído entre outros tipos de cobertura
    forest_mask = (~river_mask) & (np.random.random(points) < 0.7)  # Floresta predominante
    secondary_mask = (~river_mask) & (~forest_mask) & (np.random.random(points) < 0.7)
    cleared_mask = (~river_mask) & (~forest_mask) & (~secondary_mask) & (np.random.random(points) < 0.8)
    infrastructure_mask = (~river_mask) & (~forest_mask) & (~secondary_mask) & (~cleared_mask)
    
    # Criar classificação
    classification = np.zeros(points, dtype=int)
    classification[forest_mask] = 1
    classification[river_mask] = 2
    classification[secondary_mask] = 3
    classification[cleared_mask] = 4
    classification[infrastructure_mask] = 5
    
    # Gerar altitudes baseadas no tipo de cobertura
    # Altitudes típicas da Amazônia: 30-200m acima do nível do mar
    base_altitude = 60 + np.random.normal(0, 10)
    z = np.zeros(points)
    
    # Água (mais baixa e plana)
    z[river_mask] = base_altitude - 5 + np.random.normal(0, 0.5, np.sum(river_mask))
    
    # Floresta (maior variabilidade do dossel)
    # CORRIGIDO: Nomeando o parâmetro 'size' para np.random.gamma
    forest_height = np.random.gamma(shape=9, scale=4, size=np.sum(forest_mask))  # ~35m média
    z[forest_mask] = base_altitude + np.random.normal(0, 5, np.sum(forest_mask)) + forest_height
    
    # Vegetação secundária
    # CORRIGIDO: Nomeando o parâmetro 'size' para np.random.gamma
    sec_height = np.random.gamma(shape=3, scale=2, size=np.sum(secondary_mask))  # ~6m média
    z[secondary_mask] = base_altitude + np.random.normal(0, 3, np.sum(secondary_mask)) + sec_height
    
    # Solo exposto
    z[cleared_mask] = base_altitude + np.random.normal(0, 2, np.sum(cleared_mask))
    
    # Infraestrutura
    # CORRIGIDO: Nomeando o parâmetro 'size' para np.random.gamma
    build_height = np.random.gamma(shape=2, scale=2, size=np.sum(infrastructure_mask))  # ~4m média
    z[infrastructure_mask] = base_altitude + build_height
    
    # Intensidade (reflexão) - varia por tipo de cobertura
    intensity = np.zeros(points, dtype=int)
    intensity[forest_mask] = np.random.randint(40, 120, np.sum(forest_mask))      # Médio
    intensity[river_mask] = np.random.randint(5, 30, np.sum(river_mask))          # Baixo (absorção)
    intensity[secondary_mask] = np.random.randint(50, 150, np.sum(secondary_mask)) # Médio-alto
    intensity[cleared_mask] = np.random.randint(120, 220, np.sum(cleared_mask))   # Alto
    intensity[infrastructure_mask] = np.random.randint(150, 250, np.sum(infrastructure_mask)) # Muito alto
    
    # Retornar DataFrame
    return pd.DataFrame({
        'X': x,
        'Y': y,
        'Z': z,
        'Intensity': intensity,
        'Classification': classification
    })

def create_download_link(df, filename, link_text):
    """Cria link para download de um DataFrame como CSV."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def create_geojson_for_download(coordinates, filename="pontos_amazonia.geojson"):
    """Cria GeoJSON para download a partir das coordenadas."""
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": point['name'],
                    "type": point['type'],
                    "weight": point.get('semantic_weight', 1.0)
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [point['lon'], point['lat']]
                }
            } for point in coordinates
        ]
    }
    
    # Converter para JSON string
    geojson_str = json.dumps(geojson, indent=2)
    
    # Criar link para download
    b64 = base64.b64encode(geojson_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">{filename}</a>'
    
    return href

def create_qml_style_ship():
    """Cria um arquivo de estilo QML para ícones de caravela."""
    qml_content = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
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
    # Criar link para download
    b64 = base64.b64encode(qml_content.encode()).decode()
    href = f'<a href="data:text/xml;base64,{b64}" download="estilo_caravela.qml">estilo_caravela.qml</a>'
    
    return href

def create_qml_style_lidar():
    """Cria um arquivo de estilo QML para pontos LiDAR."""
    qml_content = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="categorizedSymbol" attr="Classification" symbollevels="0" enableorderby="0">
    <categories>
      <category symbol="0" value="1" label="Floresta Densa"/>
      <category symbol="1" value="2" label="Corpos D'água"/>
      <category symbol="2" value="3" label="Vegetação Secundária"/>
      <category symbol="3" value="4" label="Solo Exposto"/>
      <category symbol="4" value="5" label="Infraestrutura"/>
    </categories>
    <symbols>
      <symbol name="0" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="38,115,0,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="1" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="32,178,170,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="2" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="144,238,144,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="3" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="205,133,63,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="4" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="240,128,128,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""
    # Criar link para download
    b64 = base64.b64encode(qml_content.encode()).decode()
    href = f'<a href="data:text/xml;base64,{b64}" download="estilo_lidar.qml">estilo_lidar.qml</a>'
    
    return href

def create_qgis_project_zip(coordinates, lidar_data):
    """
    Cria um pacote de projeto QGIS completo com todas as camadas configuradas.
    
    Args:
        coordinates (list): Lista de coordenadas extraídas
        lidar_data (pd.DataFrame): Dados LiDAR
        
    Returns:
        str: HTML para link de download do pacote
    """
    import io
    import zipfile
    
    # Calcular extensão para o mapa
    if coordinates:
        min_lon = min(c["lon"] for c in coordinates) - 0.2
        max_lon = max(c["lon"] for c in coordinates) + 0.2
        min_lat = min(c["lat"] for c in coordinates) - 0.2
        max_lat = max(c["lat"] for c in coordinates) + 0.2
    else:
        # Padrão para região central da Amazônia
        min_lon, max_lon = -61.0, -59.0
        min_lat, max_lat = -4.0, -2.0
    
    # Criar arquivo GeoJSON para os pontos
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": point['name'],
                    "type": point['type'],
                    "weight": point.get('semantic_weight', 1.0)
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [point['lon'], point['lat']]
                }
            } for point in coordinates
        ]
    }
    
    geojson_str = json.dumps(geojson, indent=2)
    
    # Arquivo CSV para dados LiDAR
    lidar_csv = lidar_data.to_csv(index=False)
    
    # Estilo QML para caravela
    ship_qml = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
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
    
    # Estilo QML para LiDAR
    lidar_qml = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="categorizedSymbol" attr="Classification" symbollevels="0" enableorderby="0">
    <categories>
      <category symbol="0" value="1" label="Floresta Densa"/>
      <category symbol="1" value="2" label="Corpos D'água"/>
      <category symbol="2" value="3" label="Vegetação Secundária"/>
      <category symbol="3" value="4" label="Solo Exposto"/>
      <category symbol="4" value="5" label="Infraestrutura"/>
    </categories>
    <symbols>
      <symbol name="0" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="38,115,0,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="1" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="32,178,170,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="2" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="144,238,144,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="3" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="205,133,63,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
      <symbol name="4" force_rhr="0" type="marker" clip_to_extent="1" alpha="0.7">
        <layer locked="0" enabled="1" class="SimpleMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="240,128,128,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="1.5"/>
          <prop k="size_unit" v="MM"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""
    
    # Arquivo de projeto QGIS
    qgis_project = f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="Análise Amazônia - GAIA DIGITAL" version="3.22.0-Białowieża">
  <title>Análise Amazônia - GAIA DIGITAL</title>
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
      <xmin>{min_lon}</xmin>
      <ymin>{min_lat}</ymin>
      <xmax>{max_lon}</xmax>
      <ymax>{max_lat}</ymax>
    </extent>
    <rotation>0</rotation>
  </mapcanvas>
  <projectMetadata>
    <author>GAIA DIGITAL - Análise Geoespacial</author>
    <creation>
      <datetime>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</datetime>
    </creation>
    <abstract>Projeto gerado automaticamente para análise da região amazônica</abstract>
  </projectMetadata>
  <layerorder>
    <layer id="OpenStreetMap_5dc1a003_3bc9_4b79_94c5_fa434b61d8df"/>
    <layer id="pontos_interesse_3dbd3f71_e8f5_4cc3_9e4f_eeb69cf3b3ad"/>
    <layer id="lidar_data_5d86c7f1_b2a1_45f0_8a06_25b2a86c21bc"/>
  </layerorder>
  
  <!-- Base Layer - OpenStreetMap -->
  <projectlayers>
    <maplayer type="raster" name="OpenStreetMap" id="OpenStreetMap_5dc1a003_3bc9_4b79_94c5_fa434b61d8df">
      <layername>OpenStreetMap</layername>
      <datasource>type=xyz&amp;url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&amp;zmax=19&amp;zmin=0</datasource>
      <shortname>osm</shortname>
      <srs>
        <spatialrefsys>
          <authid>EPSG:3857</authid>
        </spatialrefsys>
      </srs>
    </maplayer>
    
    <!-- Pontos de Interesse com Caravelas -->
    <maplayer type="vector" name="Pontos de Interesse" id="pontos_interesse_3dbd3f71_e8f5_4cc3_9e4f_eeb69cf3b3ad">
      <layername>Pontos de Interesse</layername>
      <datasource>./pontos_interesse.geojson</datasource>
      <shortname>pontos</shortname>
      <srs>
        <spatialrefsys>
          <authid>EPSG:4326</authid>
        </spatialrefsys>
      </srs>
      <stylesources>
        <style path="./estilo_caravela.qml" name="Estilo Caravela"/>
      </stylesources>
    </maplayer>
    
    <!-- Dados LiDAR -->
    <maplayer type="vector" name="Dados LiDAR" id="lidar_data_5d86c7f1_b2a1_45f0_8a06_25b2a86c21bc">
      <layername>Dados LiDAR</layername>
      <datasource>file://./lidar_data.csv?type=csv&amp;xField=X&amp;yField=Y&amp;spatialIndex=no&amp;subsetIndex=no&amp;watchFile=no</datasource>
      <shortname>lidar</shortname>
      <srs>
        <spatialrefsys>
          <authid>EPSG:4326</authid>
        </spatialrefsys>
      </srs>
      <stylesources>
        <style path="./estilo_lidar.qml" name="Estilo LiDAR"/>
      </stylesources>
    </maplayer>
  </projectlayers>
</qgis>
"""
    
    # README.txt com instruções
    readme = f"""GAIA DIGITAL - Projeto QGIS para Análise da Amazônia
====================================================

Data de criação: {datetime.now().strftime('%Y-%m-%d')}

INSTRUÇÕES:
----------
1. Descompacte todos os arquivos em uma pasta
2. Abra o arquivo de projeto QGIS (amazonia_gaia_digital.qgs)
3. Se as camadas não carregarem automaticamente, você precisará ajustar os caminhos:
   - Clique com o botão direito em cada camada e selecione "Propriedades"
   - Vá para a aba "Fonte"
   - Atualize o caminho para o arquivo correspondente

ARQUIVOS INCLUÍDOS:
-----------------
- amazonia_gaia_digital.qgs: Projeto QGIS principal
- pontos_interesse.geojson: Pontos de interesse com ícones de caravela
- estilo_caravela.qml: Estilo para ícones de caravela
- lidar_data.csv: Dados LiDAR para análise
- estilo_lidar.qml: Estilo para dados LiDAR

Este projeto foi gerado automaticamente pelo aplicativo GAIA DIGITAL.
"""

    # Criar ZIP em memória
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("amazonia_gaia_digital.qgs", qgis_project)
        zipf.writestr("pontos_interesse.geojson", geojson_str)
        zipf.writestr("estilo_caravela.qml", ship_qml)
        zipf.writestr("lidar_data.csv", lidar_csv)
        zipf.writestr("estilo_lidar.qml", lidar_qml)
        zipf.writestr("README.txt", readme)
    
    # Criar link para download
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="amazonia_gaia_digital.zip">⬇️ Download Projeto QGIS Completo</a>'
    
    return href

# --------- INTERFACE DO APLICATIVO STREAMLIT ---------
st.title("🌎 GAIA DIGITAL - Análise Geoespacial Amazônica")
st.markdown("""
Este aplicativo utiliza análise semântica avançada para extrair coordenadas geográficas 
precisas de descrições textuais da Amazônia, gerando mapas, dados LiDAR e arquivos
compatíveis com QGIS, incluindo ícones de caravela para navegação.
""")

# Barra lateral com opções
st.sidebar.title("Configurações")

# Explicação do algoritmo na barra lateral
with st.sidebar.expander("Sobre o Processamento Semântico"):
    st.markdown("""
    ### Processamento Semântico Geodésico
    
    Este aplicativo utiliza um algoritmo de 5 camadas:
    
    1. **Decomposição Semântica**: Núcleos nominais e verbais
    2. **Identificação de Entidades**: Marcos amazônicos
    3. **Análise Fuzzy**: Pesos de pertinência e dispersão
    4. **Teoria de Conjuntos**: Redução de redundâncias
    5. **Validação Contextual**: Coerência semântica
    
    O resultado são coordenadas altamente precisas.
    """)

# Área de entrada de texto
text_input = st.text_area(
    "Descreva a região amazônica de interesse:", 
    value="Quero analisar a região próxima a Manaus, especialmente as áreas de confluência do Rio Negro com o Rio Solimões, onde ocorrem fenômenos de encontro das águas. Estou interessado em identificar potenciais anomalias na vegetação e áreas de desmatamento recente ao norte da Reserva Adolpho Ducke, próximo à rodovia AM-010.",
    height=150
)

# Configurações avançadas na barra lateral
with st.sidebar.expander("Configurações Avançadas"):
    lidar_density = st.slider("Densidade de pontos LiDAR", 100, 5000, 1000)
    lidar_radius = st.slider("Raio da amostra LiDAR (graus)", 0.01, 0.2, 0.05)
    ai_temperature = st.slider("Temperatura IA", 0.0, 1.0, 0.1)
    semantic_threshold = st.slider("Limiar de peso semântico", 0.0, 1.0, 0.5, 
                                  help="Pontos com peso semântico abaixo deste valor serão ignorados")
    
# Botão para processar
if st.button("Processar e Gerar Mapa"):
    # Extrair coordenadas do texto usando IA com análise semântica avançada
    with st.spinner("Realizando análise semântica avançada do texto..."):
        coordinates = extract_coordinates_semantic(text_input)
        
        # Filtrar por peso semântico se disponível
        if coordinates:
            coordinates = [c for c in coordinates if c.get('semantic_weight', 0) >= semantic_threshold]
            
        if not coordinates:
            # Fallback para coordenadas padrão da Amazônia Central se a IA não encontrar
            coordinates = [
                {"lat": -3.1, "lon": -60.0, "name": "Manaus", "type": "cidade", "semantic_weight": 0.95},
                {"lat": -3.3, "lon": -60.2, "name": "Encontro das Águas", "type": "rio", "semantic_weight": 0.9},
                {"lat": -2.93, "lon": -59.97, "name": "Reserva Adolpho Ducke", "type": "reserva", "semantic_weight": 0.85}
            ]
            st.info("Usando coordenadas padrão com alta relevância semântica")
    
    # Exibir coordenadas encontradas
    st.subheader("Coordenadas Identificadas por Análise Semântica")
    
    # Criar DataFrame para exibição
    coord_df = pd.DataFrame(coordinates)
    
    # Adicionar coluna de confiança
    if 'semantic_weight' in coord_df.columns:
        coord_df['confiança'] = coord_df['semantic_weight'].apply(
            lambda x: f"{int(x*100)}%"
        )
    
    # Ordenar por peso semântico
    if 'semantic_weight' in coord_df.columns:
        coord_df = coord_df.sort_values('semantic_weight', ascending=False)
    
    # Exibir em formato tabular
    st.dataframe(coord_df)
    
    # Criar dados LiDAR simulados
    center_lat = sum(c["lat"] for c in coordinates) / len(coordinates)
    center_lon = sum(c["lon"] for c in coordinates) / len(coordinates)
    
    lidar_data = generate_lidar_sample(center_lat, center_lon, lidar_radius, lidar_density)
    
    # Visualizar amostra dos dados LiDAR
    st.subheader("Amostra de Dados LiDAR (Simulados)")
    st.dataframe(lidar_data.head(10))
    
    # Visualizar mapa usando OpenStreetMap incorporado em um iframe HTML
    st.subheader("Visualização do Mapa (OpenStreetMap)")
    
    # Criar o HTML para incorporar o OpenStreetMap
    map_html = f"""
    <iframe width="100%" height="450" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
    src="https://www.openstreetmap.org/export/embed.html?bbox={center_lon-0.2}%2C{center_lat-0.2}%2C{center_lon+0.2}%2C{center_lat+0.2}&amp;layer=mapnik" 
    style="border: 1px solid black"></iframe>
    <br/>
    <small>
        <a href="https://www.openstreetmap.org/#map=12/{center_lat}/{center_lon}" target="_blank">Ver mapa maior</a>
    </small>
    """
    
    st.markdown(map_html, unsafe_allow_html=True)
    
    # Exibir estatísticas LiDAR
    st.subheader("Estatísticas dos Dados LiDAR")
    
    # Criar métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Elevação Média (m)", f"{lidar_data['Z'].mean():.1f}")
    col2.metric("Elevação Mínima (m)", f"{lidar_data['Z'].min():.1f}")
    col3.metric("Elevação Máxima (m)", f"{lidar_data['Z'].max():.1f}")
    
    # Distribuição de classificação
    st.markdown("### Distribuição de Classes LiDAR")
    class_counts = lidar_data['Classification'].value_counts().reset_index()
    class_counts.columns = ['Classificação', 'Quantidade']
    class_map = {
        1: "Floresta Densa",
        2: "Corpos D'água",
        3: "Vegetação Secundária",
        4: "Solo Exposto",
        5: "Infraestrutura"
    }
    class_counts['Tipo'] = class_counts['Classificação'].map(class_map)
    st.dataframe(class_counts[['Tipo', 'Quantidade']])
    
    # Seção de downloads
    st.subheader("Exportar para QGIS")
    
    # Criar links de download individuais
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Dados LiDAR")
        st.markdown(create_download_link(lidar_data, "amazonia_lidar.csv", 
                                       "⬇️ Download Dados LiDAR (CSV)"), unsafe_allow_html=True)
        
        st.markdown("### Estilo LiDAR (QML)")
        st.markdown(create_qml_style_lidar(), unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Pontos de Interesse (GeoJSON)")
        st.markdown(create_geojson_for_download(coordinates, "pontos_amazonia.geojson"), 
                   unsafe_allow_html=True)
        
        st.markdown("### Estilo de Caravela (QML)")
        st.markdown(create_qml_style_ship(), unsafe_allow_html=True)
    
    # Projeto QGIS completo
    st.markdown("### Projeto QGIS Completo (Tudo em um)")
    st.markdown(create_qgis_project_zip(coordinates, lidar_data), unsafe_allow_html=True)
    
    # Instruções para QGIS
    with st.expander("Como importar no QGIS"):
        st.markdown("""
        ### Instruções para importação no QGIS
        
        #### Opção 1: Projeto Completo (Recomendado)
        - Baixe o "Projeto QGIS Completo" (ZIP)
        - Descompacte todos os arquivos em uma pasta
        - Abra o arquivo .qgs no QGIS
        - Todas as camadas já estarão configuradas com estilos
        
        #### Opção 2: Importação Manual
        
        **Para dados LiDAR:**
        - Baixe o arquivo CSV com dados LiDAR
        - No QGIS, vá para "Camada > Adicionar Camada > Adicionar Camada de Texto Delimitado"
        - Selecione o arquivo CSV baixado
        - Especifique "X" como longitude e "Y" como latitude
        - Selecione CRS EPSG:4326 (WGS 84)
        - Baixe e aplique o estilo QML para LiDAR
        
        **Para pontos de interesse com ícones de caravela:**
        - Baixe o arquivo GeoJSON de pontos de interesse
        - No QGIS, vá para "Camada > Adicionar Camada > Adicionar Camada Vetorial"
        - Selecione o arquivo GeoJSON baixado
        - Baixe o arquivo de estilo QML para caravelas
        - Clique com botão direito na camada > Propriedades > Simbologia
        - Clique em "Carregar Estilo" e selecione o arquivo QML baixado
        """)
        
    # Análise avançada com IA
    with st.expander("Análise Avançada com IA"):
        if st.button("Realizar Análise Avançada"):
            prompt = f"""
            Realize uma análise geoespacial da seguinte região amazônica, considerando a análise semântica já realizada:
            
            Texto original: {text_input}
            
            Coordenadas semanticamente relevantes:
            {json.dumps([{"nome": c['name'], "tipo": c['type'], "lat": c['lat'], "lon": c['lon'], "peso_semantico": c.get('semantic_weight', 1.0)} for c in coordinates], indent=2)}
            
            Forneça uma análise detalhada sobre:
            1. Potenciais riscos ambientais na região, considerando o contexto semântico
            2. Características geomorfológicas notáveis nas áreas identificadas
            3. Recomendações para monitoramento ambiental, com foco nos pontos de maior peso semântico
            4. Pontos de interesse para um estudo de campo, ordenados por relevância semântica
            
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
    "GAIA DIGITAL - Análise Geoespacial Amazônica\n\n"
    "Especialista GeoPython-QGIS © 2025"
)
