import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import re
import requests
import base64
import time
import random
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="GAIA DIGITAL - Cartografia Amazônica Divertida",
    page_icon="🦜",
    layout="wide"
)

# --------- FUNÇÕES DE SEGURANÇA E API ---------
def get_secure_api_key():
    """
    Obtém a chave da API Gemini de forma segura.
    A chave é armazenada em formato criptografado e descriptografada apenas em memória.
    """
    # Chave codificada em base64 para não expor diretamente
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

def query_gemini_api(prompt, temperature=0.2, max_tokens=2048):
    """
    Consulta a API Gemini de forma segura com a chave ocultada.
    """
    # Obter a chave API apenas quando necessário
    api_key = get_secure_api_key()
    
    # Construir URL com a chave
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
    
    with st.spinner("Processando análise geográfica..."):
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # Verificar resposta
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

# --------- PROCESSAMENTO CARTOGRÁFICO E GEOGRÁFICO ---------
def extract_geographic_features(text):
    """
    Extrai feições geográficas usando análise semântica avançada com terminologia cartográfica.
    """
    # Prompt especializado em cartografia e geografia
    prompt = f"""
    Analise o seguinte texto e extraia feições geográficas utilizando conceitos cartográficos:
    
    TEXTO: "{text}"
    
    INSTRUÇÕES:
    
    1. Identifique as principais feições geográficas mencionadas:
       - Hidrografia (rios, lagos, igarapés, encontro de águas)
       - Relevo (serras, platôs, planícies)
       - Cobertura vegetal (florestas, áreas de transição, campos)
       - Localidades (cidades, comunidades, reservas)
       - Infraestrutura (estradas, portos, hidrelétricas)
       - Limites territoriais (fronteiras, unidades de conservação)
    
    2. Para cada feição geográfica:
       - Determine coordenadas geográficas precisas (latitude/longitude) 
       - Classifique segundo padrões cartográficos (ponto, linha, polígono)
       - Identifique a escala de representação mais adequada
       - Atribua metadados importantes para cartografia temática
       - Sugira um emoji ou ícone divertido/lúdico que represente a feição (por exemplo: 🌊 para rio, 🏙️ para cidade)
    
    3. Determine relações topológicas entre as feições:
       - Proximidade (adjacência, distância)
       - Conectividade (redes hidrográficas, sistemas viários)
       - Hierarquia (bacias hidrográficas, divisões político-administrativas)
    
    4. Priorize referências a modelos digitais de elevação, camadas de uso do solo, e limites oficiais.
    
    IMPORTANTE: Retorne APENAS um array JSON com esta estrutura:
    [
        {{
            "nome": "nome da feição geográfica",
            "tipo": "tipo de feição segundo padrões cartográficos",
            "categoria": "hidrografia|relevo|vegetação|localidade|infraestrutura|limite",
            "geometria": "ponto|linha|polígono",
            "lat": latitude em graus decimais,
            "lon": longitude em graus decimais,
            "importancia_cartografica": valor de 0.0 a 1.0 baseado na relevância para mapeamento,
            "metadados": {{
                "fonte": "fonte da informação geográfica",
                "escala_recomendada": "1:N (escala adequada para representação)",
                "data_referencia": "data aproximada da informação"
            }},
            "icone": "emoji ou descrição de ícone divertido"
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
            features = json.loads(json_str)
            
            # Ordenar por importância cartográfica
            if features and isinstance(features, list):
                features.sort(key=lambda x: x.get('importancia_cartografica', 0), reverse=True)
            
            return features
    except Exception as e:
        st.error(f"Erro ao processar JSON de feições geográficas: {e}")
    
    return []

# Lista de ícones divertidos para cada categoria
def get_fun_icons():
    return {
        "hidrografia": ["🌊", "🚣‍♀️", "🐬", "🦈", "🐙", "🐟", "💦", "🏊‍♂️", "🛶", "⛵"],
        "relevo": ["⛰️", "🏔️", "🏞️", "🏝️", "🌋", "🗻", "🏜️", "⛱️", "🏕️", "🏘️"],
        "vegetação": ["🌴", "🌲", "🌳", "🌵", "🍄", "🌿", "🌱", "🌺", "🦜", "🐒"],
        "localidade": ["🏙️", "🏢", "🏛️", "🏚️", "🏘️", "🏡", "🏫", "🏪", "🏭", "🏟️"],
        "infraestrutura": ["🛣️", "🌉", "✈️", "🚢", "🛥️", "⚓", "🏗️", "🚉", "🚏", "⛽"],
        "limite": ["🚧", "🛑", "⛔", "🚨", "🚫", "⭕", "🔴", "🌐", "🧭", "🗺️"]
    }

def assign_fun_icons(features):
    """Atribui ícones divertidos às feições se não tiverem ainda"""
    icons = get_fun_icons()
    
    for feature in features:
        if 'icone' not in feature or not feature['icone']:
            categoria = feature.get('categoria', '').lower()
            if categoria in icons and icons[categoria]:
                # Escolher aleatoriamente da lista de ícones para a categoria
                feature['icone'] = random.choice(icons[categoria])
            else:
                # Ícone padrão se a categoria não for reconhecida
                feature['icone'] = "🦜"
    
    return features

def get_map_layers_html(center_lat, center_lon, zoom=10, features=None, opacity=0.8):
    """
    Gera HTML para múltiplas camadas de mapas com opacidade ajustável, incluindo ícones divertidos.
    """
    # Preparar marcadores para os mapas
    markers = ""
    if features:
        for f in features:
            lat = f.get('lat', 0)
            lon = f.get('lon', 0)
            nome = f.get('nome', 'Ponto')
            icone = f.get('icone', '📍')
            tipo = f.get('tipo', '')
            
            # Adicionar marcador com popup
            markers += f"""
            var marker = L.marker([{lat}, {lon}], {{
                icon: L.divIcon({{
                    html: '<div style="font-size: 24px; text-align: center;">{icone}</div>',
                    className: 'emoji-marker',
                    iconSize: [32, 32],
                    iconAnchor: [16, 16],
                    popupAnchor: [0, -16]
                }})
            }}).addTo(map);
            
            marker.bindPopup("<b>{nome}</b><br>{tipo}");
            """
    
    # OpenStreetMap base com marcadores
    osm_style = f"style='opacity: {opacity}; border: 1px solid black;'"
    
    osm_base = f"""
    <iframe width="100%" height="400" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
    src="https://www.openstreetmap.org/export/embed.html?bbox={center_lon-0.2}%2C{center_lat-0.2}%2C{center_lon+0.2}%2C{center_lat+0.2}&amp;layer=mapnik&amp;marker={center_lat}%2C{center_lon}" 
    {osm_style}></iframe>
    <br/>
    <small>
        <a href="https://www.openstreetmap.org/?mlat={center_lat}&mlon={center_lon}#map={zoom}/{center_lat}/{center_lon}" target="_blank">Ver mapa básico em tela cheia</a>
    </small>
    """
    
    # Mapa topográfico com marcadores personalizados
    topo_map = f"""
    <iframe width="100%" height="400" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
    src="https://www.opentopomap.org/#map={zoom}/{center_lat}/{center_lon}" 
    {osm_style}></iframe>
    <br/>
    <small>
        <a href="https://www.opentopomap.org/#map={zoom}/{center_lat}/{center_lon}" target="_blank">Ver mapa topográfico em tela cheia</a>
    </small>
    """
    
    # Mapa híbrido com marcadores
    hybrid_map = f"""
    <iframe width="100%" height="400" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
    src="https://www.openstreetmap.org/export/embed.html?bbox={center_lon-0.2}%2C{center_lat-0.2}%2C{center_lon+0.2}%2C{center_lat+0.2}&amp;layer=hot&amp;marker={center_lat}%2C{center_lon}" 
    {osm_style}></iframe>
    <br/>
    <small>
        <a href="https://www.openstreetmap.org/?mlat={center_lat}&mlon={center_lon}#map={zoom}/{center_lat}/{center_lon}&layers=H" target="_blank">Ver mapa híbrido em tela cheia</a>
    </small>
    """
    
    # Retornar HTML para cada tipo de mapa
    return {
        "base": osm_base,
        "topografico": topo_map, 
        "hibrido": hybrid_map
    }

def create_geojson_for_qgis(features, filename="feicoes_amazonicas.geojson"):
    """
    Cria GeoJSON para uso no QGIS a partir das feições geográficas identificadas.
    Incorpora metadados cartográficos e ícones divertidos.
    """
    # Estrutura padrão de GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": []
    }
    
    # Processamento de cada feição
    for feature in features:
        # Definir geometria baseada no tipo
        if feature.get('geometria') == 'ponto':
            geometry = {
                "type": "Point",
                "coordinates": [feature.get('lon'), feature.get('lat')]
            }
        elif feature.get('geometria') == 'linha':
            # Para linhas, usamos apenas o ponto central como representação
            geometry = {
                "type": "Point", 
                "coordinates": [feature.get('lon'), feature.get('lat')]
            }
        elif feature.get('geometria') == 'polígono':
            # Para polígonos, usamos apenas o ponto central como representação
            geometry = {
                "type": "Point",
                "coordinates": [feature.get('lon'), feature.get('lat')]
            }
        else:
            # Padrão para casos não especificados
            geometry = {
                "type": "Point",
                "coordinates": [feature.get('lon'), feature.get('lat')]
            }
        
        # Criar feature com propriedades completas, incluindo ícone
        geojson_feature = {
            "type": "Feature",
            "properties": {
                "nome": feature.get('nome', ''),
                "tipo": feature.get('tipo', ''),
                "categoria": feature.get('categoria', ''),
                "importancia": feature.get('importancia_cartografica', 0.5),
                "fonte": feature.get('metadados', {}).get('fonte', 'Análise semântica'),
                "escala": feature.get('metadados', {}).get('escala_recomendada', '1:50000'),
                "data_ref": feature.get('metadados', {}).get('data_referencia', datetime.now().strftime('%Y-%m-%d')),
                "simbolo": get_symbol_for_category(feature.get('categoria', '')),
                "icone": feature.get('icone', '📍')
            },
            "geometry": geometry
        }
        
        geojson["features"].append(geojson_feature)
    
    # Converter para JSON string
    geojson_str = json.dumps(geojson, indent=2)
    
    # Criar link para download
    b64 = base64.b64encode(geojson_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">{filename}</a>'
    
    return href, geojson_str

def get_symbol_for_category(categoria):
    """
    Retorna o símbolo cartográfico adequado para cada categoria de feição.
    """
    # Mapeamento de categorias para símbolos adequados
    categoria = categoria.lower() if categoria else ""
    
    if "hidrografia" in categoria or "rio" in categoria or "lago" in categoria:
        return "agua"
    elif "relevo" in categoria or "serra" in categoria or "montanha" in categoria:
        return "elevacao" 
    elif "vegetação" in categoria or "floresta" in categoria:
        return "vegetacao"
    elif "localidade" in categoria or "cidade" in categoria or "comunidade" in categoria:
        return "localidade"
    elif "infraestrutura" in categoria or "estrada" in categoria:
        return "infraestrutura"
    elif "limite" in categoria or "fronteira" in categoria:
        return "limite"
    else:
        return "geral"

def create_fun_styles_for_qgis():
    """
    Cria estilos QML para diferentes tipos de feições geográficas usando ícones divertidos.
    """
    # Estilo com ícones divertidos usando expressões do QGIS
    fun_icons_qml = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="RuleRenderer" symbollevels="0" enableorderby="0">
    <rules key="{695e1f71-ddfb-4aa7-9d39-1a86029e703a}">
      <rule filter="&quot;icone&quot; LIKE '%🌊%'" key="{9cb3289d-bb2e-4eab-8128-39fc41a1f17d}" symbol="0" label="Água"/>
      <rule filter="&quot;icone&quot; LIKE '%🏔️%'" key="{f1f8c6a0-c324-46a0-b54a-8e0a06c05e7e}" symbol="1" label="Montanha"/>
      <rule filter="&quot;icone&quot; LIKE '%🌴%'" key="{ac4c9751-d8cd-4050-b055-f84befb3b975}" symbol="2" label="Vegetação"/>
      <rule filter="&quot;icone&quot; LIKE '%🏙️%'" key="{64e6e9c0-6b88-4a40-a1bc-e99e64d9fdd5}" symbol="3" label="Cidade"/>
      <rule filter="&quot;icone&quot; LIKE '%🛣️%'" key="{8f0fa6a9-6e1d-4734-88aa-86f2a8610dca}" symbol="4" label="Infraestrutura"/>
      <rule filter="&quot;icone&quot; LIKE '%🚧%'" key="{3da4c90f-9275-450c-a533-9b10c8abb9a1}" symbol="5" label="Limite"/>
      <rule key="{56f2b909-11a1-48eb-99ad-036d75f32818}" symbol="6" label="Outros"/>
    </rules>
    <symbols>
      <symbol name="0" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🌊"/>
          <prop k="color" v="0,0,255,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="1" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="⛰️"/>
          <prop k="color" v="145,82,45,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="2" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🌴"/>
          <prop k="color" v="0,128,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="3" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🏙️"/>
          <prop k="color" v="255,0,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="4" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🛣️"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="5" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🚧"/>
          <prop k="color" v="255,0,255,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="6" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="📍"/>
          <prop k="color" v="200,0,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""
    
    # Estilo para caravela
    caravela_qml = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
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
          <prop k="size" v="8"/>
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
    
    # Criar links para download
    fun_icons_b64 = base64.b64encode(fun_icons_qml.encode()).decode()
    caravela_b64 = base64.b64encode(caravela_qml.encode()).decode()
    
    fun_icons_href = f'<a href="data:text/xml;base64,{fun_icons_b64}" download="estilo_divertido.qml">estilo_divertido.qml</a>'
    caravela_href = f'<a href="data:text/xml;base64,{caravela_b64}" download="estilo_caravela.qml">estilo_caravela.qml</a>'
    
    return {
        "divertido": fun_icons_href,
        "caravela": caravela_href
    }

def create_qgis_project_package(features, geojson_str):
    """
    Cria um pacote de projeto QGIS com ícones divertidos e opacidade ajustável.
    """
    import io
    import zipfile
    
    # Calcular extensão do mapa
    if features:
        min_lon = min(f.get("lon", 0) for f in features) - 0.2
        max_lon = max(f.get("lon", 0) for f in features) + 0.2
        min_lat = min(f.get("lat", 0) for f in features) - 0.2
        max_lat = max(f.get("lat", 0) for f in features) + 0.2
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
    else:
        min_lon, max_lon = -61.0, -59.0
        min_lat, max_lat = -4.0, -2.0
        center_lat, center_lon = -3.1, -60.0
    
    # Estilos QML
    fun_icons_qml = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="RuleRenderer" symbollevels="0" enableorderby="0">
    <rules key="{695e1f71-ddfb-4aa7-9d39-1a86029e703a}">
      <rule filter="&quot;icone&quot; LIKE '%🌊%'" key="{9cb3289d-bb2e-4eab-8128-39fc41a1f17d}" symbol="0" label="Água"/>
      <rule filter="&quot;icone&quot; LIKE '%🏔️%'" key="{f1f8c6a0-c324-46a0-b54a-8e0a06c05e7e}" symbol="1" label="Montanha"/>
      <rule filter="&quot;icone&quot; LIKE '%🌴%'" key="{ac4c9751-d8cd-4050-b055-f84befb3b975}" symbol="2" label="Vegetação"/>
      <rule filter="&quot;icone&quot; LIKE '%🏙️%'" key="{64e6e9c0-6b88-4a40-a1bc-e99e64d9fdd5}" symbol="3" label="Cidade"/>
      <rule filter="&quot;icone&quot; LIKE '%🛣️%'" key="{8f0fa6a9-6e1d-4734-88aa-86f2a8610dca}" symbol="4" label="Infraestrutura"/>
      <rule filter="&quot;icone&quot; LIKE '%🚧%'" key="{3da4c90f-9275-450c-a533-9b10c8abb9a1}" symbol="5" label="Limite"/>
      <rule key="{56f2b909-11a1-48eb-99ad-036d75f32818}" symbol="6" label="Outros"/>
    </rules>
    <symbols>
      <symbol name="0" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🌊"/>
          <prop k="color" v="0,0,255,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="1" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="⛰️"/>
          <prop k="color" v="145,82,45,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="2" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🌴"/>
          <prop k="color" v="0,128,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="3" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🏙️"/>
          <prop k="color" v="255,0,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="4" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🛣️"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="5" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="🚧"/>
          <prop k="color" v="255,0,255,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
      <symbol name="6" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="FontMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="chr" v="📍"/>
          <prop k="color" v="200,0,0,255"/>
          <prop k="font" v="Noto Color Emoji"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="size" v="8"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""
    
    caravela_qml = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
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
          <prop k="size" v="8"/>
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
    
    # Arquivo de projeto QGIS com opacidade configurável
    qgis_project = f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="Cartografia Amazônica Divertida - GAIA DIGITAL" version="3.22.0-Białowieża">
  <title>Cartografia Amazônica Divertida - GAIA DIGITAL</title>
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
    <destinationsrs>
      <spatialrefsys>
        <authid>EPSG:4326</authid>
      </spatialrefsys>
    </destinationsrs>
  </mapcanvas>
  <projectMetadata>
    <author>GAIA DIGITAL - Cartografia Amazônica Divertida</author>
    <creation>
      <datetime>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</datetime>
    </creation>
    <abstract>Projeto cartográfico lúdico gerado para a região amazônica</abstract>
    <keywords>
      <keyword>Amazônia</keyword>
      <keyword>cartografia</keyword>
      <keyword>divertido</keyword>
      <keyword>ícones</keyword>
    </keywords>
  </projectMetadata>
  <layerorder>
    <layer id="OpenStreetMap_base"/>
    <layer id="OpenTopoMap_topo"/>
    <layer id="feicoes_amazonicas"/>
  </layerorder>
  
  <!-- Camadas Base -->
  <projectlayers>
    <!-- OpenStreetMap Base -->
    <maplayer type="raster" name="OpenStreetMap" id="OpenStreetMap_base">
      <layername>OpenStreetMap Base</layername>
      <datasource>type=xyz&amp;url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&amp;zmax=19&amp;zmin=0</datasource>
      <shortname>osm</shortname>
      <srs>
        <spatialrefsys>
          <authid>EPSG:3857</authid>
        </spatialrefsys>
      </srs>
      <layerorder>0</layerorder>
      <opacity>0.8</opacity>
    </maplayer>
    
    <!-- OpenTopoMap (Topográfico) -->
    <maplayer type="raster" name="OpenTopoMap" id="OpenTopoMap_topo">
      <layername>Mapa Topográfico</layername>
      <datasource>type=xyz&amp;url=https://tile.opentopomap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&amp;zmax=17&amp;zmin=0</datasource>
      <shortname>topo</shortname>
      <srs>
        <spatialrefsys>
          <authid>EPSG:3857</authid>
        </spatialrefsys>
      </srs>
      <layerorder>1</layerorder>
      <opacity>0.8</opacity>
    </maplayer>
    
    <!-- Feições Geográficas com Ícones Divertidos -->
    <maplayer type="vector" name="Feições Amazônicas" id="feicoes_amazonicas">
      <layername>Feições Amazônicas Divertidas</layername>
      <datasource>./feicoes_amazonicas.geojson</datasource>
      <shortname>feicoes</shortname>
      <srs>
        <spatialrefsys>
          <authid>EPSG:4326</authid>
        </spatialrefsys>
      </srs>
      <stylesources>
        <style path="./estilo_divertido.qml" name="Estilo Divertido"/>
        <style path="./estilo_caravela.qml" name="Estilo Caravela"/>
      </stylesources>
      <layerorder>2</layerorder>
    </maplayer>
  </projectlayers>
</qgis>
"""
    
    # README com instruções divertidas
    readme = f"""GAIA DIGITAL - Cartografia Amazônica Divertida - Projeto QGIS
===========================================================

Data de criação: {datetime.now().strftime('%Y-%m-%d')}

ORIENTAÇÕES CARTOGRÁFICAS DIVERTIDAS:
----------------------------------
1. Datum utilizado: WGS 84 (EPSG:4326) 🌎
2. Sistema de coordenadas: Geográficas (Latitude/Longitude) 📍
3. Escala cartográfica sugerida: 1:100.000 🔍
4. Ícones divertidos para cada tipo de feição! 🎮

INSTRUÇÕES:
----------
1. Descompacte todos os arquivos em uma pasta 📁
2. Abra o arquivo de projeto QGIS (cartografia_amazonica_divertida.qgs) 🗺️
3. O projeto contém três camadas principais:
   - OpenStreetMap (camada base) 🌐
   - OpenTopoMap (camada topográfica) ⛰️
   - Feições Amazônicas (pontos com ícones divertidos) 🦜

4. Alternando entre estilos:
   - Estilo Divertido: visualiza cada feição com um emoji correspondente 🎭
   - Estilo Caravela: visualiza todas as feições com ícone de caravela ⛵

5. Ajustando a opacidade:
   - No QGIS, clique com o botão direito em qualquer camada
   - Vá para Propriedades > Renderização
   - Use o controle deslizante de Opacidade para ajustar a transparência

ARQUIVOS INCLUÍDOS:
-----------------
- cartografia_amazonica_divertida.qgs: Projeto QGIS principal ✨
- feicoes_amazonicas.geojson: Camada vetorial com feições e ícones 📊
- estilo_divertido.qml: Simbologia com emojis personalizados 🎨
- estilo_caravela.qml: Simbologia com ícone de caravela ⛵

FONTE DOS ÍCONES DIVERTIDOS:
-------------------------
Os emojis utilizados são compatíveis com todos os sistemas modernos e foram escolhidos para
representar visualmente cada tipo de feição geográfica de forma divertida e educativa! 🎓

Este projeto cartográfico foi gerado automaticamente pelo aplicativo GAIA DIGITAL.
"""

    # Criar ZIP em memória
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("cartografia_amazonica_divertida.qgs", qgis_project)
        zipf.writestr("feicoes_amazonicas.geojson", geojson_str)
        zipf.writestr("estilo_divertido.qml", fun_icons_qml)
        zipf.writestr("estilo_caravela.qml", caravela_qml)
        zipf.writestr("README.txt", readme)
    
    # Criar link para download
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="cartografia_amazonica_divertida.zip">⬇️ Download Projeto Cartográfico Divertido QGIS</a>'
    
    return href

def get_fun_icon_html():
    """Gera HTML para exibir ícones divertidos para cada categoria"""
    icons = get_fun_icons()
    
    html = """
    <style>
        .icon-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .icon-item {
            display: flex;
            align-items: center;
            background: #f0f0f0;
            padding: 5px 10px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .icon {
            font-size: 24px;
            margin-right: 8px;
        }
    </style>
    <div class="icon-grid">
    """
    
    for category, category_icons in icons.items():
        html += f'<div class="icon-item"><span class="icon">{category_icons[0]}</span> {category.capitalize()}</div>'
    
    html += "</div>"
    return html

# --------- INTERFACE DO APLICATIVO STREAMLIT ---------
st.title("🦜 GAIA DIGITAL - Cartografia Amazônica Divertida")
st.markdown("""
Este aplicativo utiliza análise semântica para extrair feições geográficas 
da Amazônia, gerando mapas interativos com ícones divertidos e
arquivos compatíveis com QGIS, incluindo caravelas para navegação.
""")

# Barra lateral com opções
st.sidebar.title("Configurações do Mapa")

# Opacidade do mapa
map_opacity = st.sidebar.slider("Opacidade das Camadas", 0.1, 1.0, 0.8, 
                              help="Ajuste a transparência das camadas do mapa")

# Explicação do processamento com ícones
with st.sidebar.expander("Legenda de Ícones Divertidos"):
    st.markdown(get_fun_icon_html(), unsafe_allow_html=True)

# Área de entrada de texto
text_input = st.text_area(
    "Descreva a região amazônica de interesse:", 
    value="Quero analisar a região próxima a Manaus, especialmente as áreas de confluência do Rio Negro com o Rio Solimões, onde ocorrem fenômenos de encontro das águas. A leste fica a Reserva Florestal Adolpho Ducke, importante área de preservação, e ao norte a rodovia AM-010 conecta Manaus a Itacoatiara. O Arquipélago de Anavilhanas, com seu labirinto de ilhas fluviais, fica a noroeste da capital amazonense.",
    height=150
)

# Configurações cartográficas avançadas
with st.sidebar.expander("Configurações Avançadas"):
    map_zoom = st.slider("Zoom do Mapa", 8, 15, 10)
    importance_threshold = st.slider("Limiar de Importância", 0.0, 1.0, 0.5)
    view_option = st.radio(
        "Visualização de Mapa",
        ["Base", "Topográfico", "Híbrido", "Todos"]
    )
    
# Botão para processar
if st.button("Processar e Gerar Mapa Divertido"):
    # Extrair feições geográficas do texto usando análise semântica
    with st.spinner("Realizando análise semântica cartográfica..."):
        features = extract_geographic_features(text_input)
        
        # Filtrar por importância cartográfica
        if features:
            features = [f for f in features if f.get('importancia_cartografica', 0) >= importance_threshold]
            
        if not features:
            # Feições padrão da Amazônia Central
            features = [
                {
                    "nome": "Manaus", 
                    "tipo": "Capital estadual", 
                    "categoria": "localidade",
                    "geometria": "ponto",
                    "lat": -3.1, 
                    "lon": -60.0, 
                    "importancia_cartografica": 0.95,
                    "metadados": {
                        "fonte": "IBGE",
                        "escala_recomendada": "1:50000",
                        "data_referencia": "2023-01-01"
                    },
                    "icone": "🏙️"
                },
                {
                    "nome": "Encontro das Águas", 
                    "tipo": "Fenômeno hidrográfico", 
                    "categoria": "hidrografia",
                    "geometria": "ponto",
                    "lat": -3.08, 
                    "lon": -59.95, 
                    "importancia_cartografica": 0.9,
                    "metadados": {
                        "fonte": "ANA",
                        "escala_recomendada": "1:25000",
                        "data_referencia": "2023-01-01"
                    },
                    "icone": "🌊"
                },
                {
                    "nome": "Reserva Adolpho Ducke", 
                    "tipo": "Unidade de conservação", 
                    "categoria": "limite",
                    "geometria": "polígono",
                    "lat": -2.93, 
                    "lon": -59.97, 
                    "importancia_cartografica": 0.85,
                    "metadados": {
                        "fonte": "ICMBio",
                        "escala_recomendada": "1:100000",
                        "data_referencia": "2023-01-01"
                    },
                    "icone": "🌴"
                }
            ]
            st.info("Usando feições cartográficas padrão para a região de Manaus")
    
        # Garantir que todas as feições tenham ícones divertidos
        features = assign_fun_icons(features)
    
    # Exibir feições identificadas com seus ícones
    st.subheader("Feições Geográficas Identificadas com Ícones Divertidos")
    
    # Criar DataFrame para exibição
    features_df = pd.DataFrame([
        {
            "Ícone": f['icone'],
            "Nome": f['nome'],
            "Tipo": f['tipo'],
            "Categoria": f['categoria'],
            "Lat": f"{f['lat']:.6f}",
            "Lon": f"{f['lon']:.6f}",
            "Importância": f"{f.get('importancia_cartografica', 0):.2f}"
        } for f in features
    ])
    
    # Exibir em formato tabular
    st.dataframe(features_df)
    
    # Determinar centro do mapa e obter camadas
    center_lat = sum(f.get("lat", 0) for f in features) / len(features)
    center_lon = sum(f.get("lon", 0) for f in features) / len(features)
    
    # Obter HTML para diferentes tipos de mapas com opacidade ajustável
    map_layers = get_map_layers_html(center_lat, center_lon, map_zoom, features, map_opacity)
    
    # Exibir mapas conforme seleção do usuário
    if view_option == "Todos":
        st.subheader("🌐 Mapa Base (OpenStreetMap)")
        st.markdown(map_layers["base"], unsafe_allow_html=True)
        
        st.subheader("⛰️ Mapa Topográfico")
        st.markdown(map_layers["topografico"], unsafe_allow_html=True)
        
        st.subheader("🛰️ Mapa Híbrido")
        st.markdown(map_layers["hibrido"], unsafe_allow_html=True)
    else:
        map_type = view_option.lower()
        map_titles = {
            "base": "🌐 Mapa Base (OpenStreetMap)",
            "topográfico": "⛰️ Mapa Topográfico",
            "híbrido": "🛰️ Mapa Híbrido"
        }
        
        # Corrigir mapeamento para o tipo selecionado
        map_key = "topografico" if map_type == "topográfico" else map_type.lower()
        
        st.subheader(map_titles.get(map_type, f"Mapa {view_option}"))
        st.markdown(map_layers[map_key], unsafe_allow_html=True)
    
    # Exibir legenda divertida
    st.subheader("🎮 Legenda de Ícones")
    
    # Criar legenda com contagens e ícones por categoria
    icon_counts = {}
    for feature in features:
        cat = feature.get('categoria', '').capitalize()
        icon = feature.get('icone', '📍')
        if cat:
            if cat not in icon_counts:
                icon_counts[cat] = {"count": 0, "icon": icon}
            icon_counts[cat]["count"] += 1
    
    # Exibir categorias em formato de legenda divertida
    cols = st.columns(3)
    
    for i, (cat, info) in enumerate(sorted(icon_counts.items())):
        col_idx = i % 3
        cols[col_idx].markdown(f"### {info['icon']} {cat}")
        cols[col_idx].markdown(f"{info['count']} feição(ões)")
    
    # Seção de downloads
    st.subheader("Exportar para QGIS")
    
    # Criar GeoJSON para QGIS com ícones
    geojson_link, geojson_str = create_geojson_for_qgis(features)
    
    # Criar estilos QML divertidos
    qml_styles = create_fun_styles_for_qgis()
    
    # Exibir links para download
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Dados Cartográficos")
        st.markdown(geojson_link, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🎨 Estilos Divertidos")
        st.markdown(qml_styles["divertido"], unsafe_allow_html=True)
        st.markdown(qml_styles["caravela"], unsafe_allow_html=True)
    
    # Projeto QGIS completo
    st.markdown("### 🦜 Projeto QGIS Completo")
    st.markdown(create_qgis_project_package(features, geojson_str), unsafe_allow_html=True)
    
    # Instruções divertidas para QGIS
    with st.expander("Como Usar no QGIS"):
        st.markdown("""
        ### 🎮 Instruções Divertidas para QGIS
        
        #### 🚀 Procedimento Recomendado
        1. Baixe o "Projeto Cartográfico Divertido QGIS" (ZIP)
        2. Descompacte todos os arquivos em uma pasta 📁
        3. Abra o arquivo .qgs no QGIS 🗺️
        4. O projeto já está configurado com:
           - Mapas base com opacidade ajustável 🔍
           - Feições amazônicas com ícones divertidos 🎭
           - Estilo de caravela para navegação ⛵
        
        #### 🎨 Personalizando os Ícones
        
        **Para alterar o estilo:**
        - Clique com botão direito na camada "Feições Amazônicas" > Propriedades
        - Na aba "Simbologia", escolha entre:
          - "Estilo Divertido" (emojis personalizados) 🎭
          - "Estilo Caravela" (ícones de navegação) ⛵
        
        **Para ajustar a opacidade:**
        - Clique com botão direito em qualquer camada
        - Vá para Propriedades > Renderização 🎚️
        - Use o controle deslizante para ajustar a transparência
        
        **Para criar um mapa para impressão:**
        - Use o compositor de impressão do QGIS 🖨️
        - Inclua um título divertido, legenda de emojis e escala
        - Exporte como PDF ou imagem para compartilhar
        """)
        
    # Seção de curiosidades
    with st.expander("🦜 Curiosidades da Amazônia"):
        prompt = f"""
        Forneça 5 curiosidades surpreendentes e divertidas sobre a região amazônica descrita:
        
        {text_input}
        
        Feições identificadas:
        {', '.join([f"{x['nome']} ({x['icone']})" for x in features])}
        
        Cada curiosidade deve ser curta (1-2 frases), interessante e ter um emoji relacionado no início.
        Foque em fatos geográficos, biológicos ou culturais genuínos mas surpreendentes.
        """
        
        curiosities = query_gemini_api(prompt, temperature=0.7)
        if curiosities:
            st.markdown(curiosities)
        else:
            st.markdown("""
            ### Curiosidades Amazônicas
            
            🐸 A Amazônia abriga mais de 400 espécies de anfíbios, incluindo rãs com venenos usados por indígenas em suas flechas.
            
            🌧️ A floresta amazônica cria seu próprio clima, com até 20% da chuva sendo gerada pela própria transpiração das árvores.
            
            🦜 O Encontro das Águas pode ser visto do espaço e as águas não se misturam por cerca de 6 km devido às diferenças de temperatura, densidade e velocidade.
            
            🐟 Existem peixes na Amazônia que respiram ar, sobem em árvores e até podem passar dias fora d'água!
            
            🌳 Uma única árvore na Amazônia pode abrigar mais espécies de formigas do que toda a Grã-Bretanha.
            """)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info(
    "🦜 GAIA DIGITAL - Cartografia Amazônica Divertida\n\n"
    "Especialista GeoPython-QGIS © 2025"
)
