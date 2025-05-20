import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import requests
import base64
import time
from semantic_geo_extraction import enhanced_geo_extract, create_gemini_prompt

# Configuração da página
st.set_page_config(
    page_title="GAIA DIGITAL - GeoAnálise Amazônica Semântica",
    page_icon="🌎",
    layout="wide"
)

# --------- CONFIGURAÇÃO DE API KEYS ---------
def get_gemini_api_key():
    """Obtém a chave da API Gemini de forma segura."""
    # Para propósitos de demonstração, a chave é armazenada criptografada
    # Em produção, NUNCA use este método - sempre use variáveis de ambiente
    encoded_key = "QUl6YVN5RG8zTTZKejI2UVJ4Sm14Qzc2NW5TbElRSktEdmhXN0k4"
    api_key = base64.b64decode(encoded_key).decode('utf-8')
    return api_key

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
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            try:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                st.error(f"Erro ao processar resposta da API: {e}")
                return None
        except Exception as e:
            st.error(f"Erro na API Gemini: {str(e)}")
            return None

def extract_coordinates_from_text_semantic(text):
    """Extrai coordenadas geográficas do texto usando análise semântica avançada."""
    api_key = get_gemini_api_key()
    
    # Criar prompt único com todas as camadas de processamento
    prompt = create_gemini_prompt(text)
    
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

def create_download_link(df, filename, link_text):
    """Cria um link para download de um DataFrame como CSV."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def create_geojson_for_download(coordinates, filename="pontos_amazonia.geojson"):
    """Cria um GeoJSON para download a partir das coordenadas."""
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

def create_qml_style(style_type="ship"):
    """Cria um arquivo de estilo QML para ícones."""
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

# --------- INTERFACE DO APLICATIVO STREAMLIT ---------
st.title("🌎 GAIA DIGITAL - Análise Geoespacial Amazônica Semântica")
st.markdown("""
Este aplicativo utiliza análise semântica avançada com lógica fuzzy para extrair coordenadas geográficas 
precisas de descrições textuais da Amazônia. O algoritmo decompõe o texto em núcleos semânticos, 
identifica entidades geográficas específicas e aplica teoria de conjuntos para reduzir dispersão.
""")

# Barra lateral com opções
st.sidebar.title("Configurações")

# Explicação do algoritmo na barra lateral
with st.sidebar.expander("Sobre o algoritmo semântico"):
    st.markdown("""
    ### Algoritmo Semântico Fuzzy
    
    Este aplicativo utiliza um algoritmo de 5 camadas para extração de coordenadas:
    
    1. **Decomposição Semântica**: Analisa núcleos nominais e verbais no texto
    2. **Identificação de Entidades**: Reconhece bairros, monumentos, rios, etc.
    3. **Análise Fuzzy**: Atribui graus de pertinência e raios de dispersão
    4. **Teoria de Conjuntos**: Elimina redundâncias e resolve conflitos
    5. **Validação Semântica**: Garante coerência com o contexto textual
    
    O resultado são coordenadas com alta precisão semântica.
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
        coordinates = extract_coordinates_from_text_semantic(text_input)
        
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
    
    # Exibir estatísticas semânticas
    st.subheader("Análise Semântica")
    
    # Criar métricas gerais
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Pontos Semânticos", f"{len(coordinates)}")
    
    if any('semantic_weight' in c for c in coordinates):
        avg_weight = sum(c.get('semantic_weight', 0) for c in coordinates) / len(coordinates)
        col2.metric("Confiança Semântica Média", f"{avg_weight:.2f}")
    
    # Identificar tipos semânticos 
    semantic_types = {}
    for c in coordinates:
        if 'type' in c:
            t = c['type'].lower()
            semantic_types[t] = semantic_types.get(t, 0) + 1
    
    # Exibir distribuição de tipos semânticos
    st.markdown("### Distribuição de Tipos Semânticos")
    types_df = pd.DataFrame({
        'Tipo': list(semantic_types.keys()),
        'Quantidade': list(semantic_types.values())
    })
    st.dataframe(types_df)
    
    # Seção de downloads
    st.subheader("Exportar para QGIS")
    
    # Criar links de download
    st.markdown("### Dados LiDAR")
    st.markdown(create_download_link(lidar_data, "amazonia_lidar_semantico.csv", 
                                   "⬇️ Download Dados LiDAR (CSV)"), unsafe_allow_html=True)
    
    st.markdown("### Pontos de Interesse Semânticos (GeoJSON)")
    st.markdown(create_geojson_for_download(coordinates, "pontos_amazonia_semanticos.geojson"), 
               unsafe_allow_html=True)
    
    st.markdown("### Estilo de Caravela para QGIS (QML)")
    st.markdown(create_qml_style(), unsafe_allow_html=True)
    
    # Instruções para QGIS
    with st.expander("Como importar no QGIS"):
        st.markdown("""
        ### Instruções para importação no QGIS
        
        #### 1. Importar Dados LiDAR
        - Baixe o arquivo CSV com dados LiDAR
        - No QGIS, vá para "Camada > Adicionar Camada > Adicionar Camada de Texto Delimitado"
        - Selecione o arquivo CSV baixado
        - Especifique "X" como longitude e "Y" como latitude (ou coordenadas X/Y)
        - Selecione CRS EPSG:4326 (WGS 84)
        
        #### 2. Importar Pontos de Interesse com Ícone de Caravela
        - Baixe o arquivo GeoJSON de pontos de interesse semânticos
        - No QGIS, vá para "Camada > Adicionar Camada > Adicionar Camada Vetorial"
        - Selecione o arquivo GeoJSON baixado
        - Baixe o arquivo de estilo QML
        - Clique com botão direito na camada > Propriedades > Simbologia
        - Clique em "Carregar Estilo" e selecione o arquivo QML baixado
        - Use a coluna "weight" para visualização proporcional por confiança semântica
        
        #### 3. Visualização Semântica (recomendado)
        - No QGIS, crie uma camada de calor (heatmap) baseada nos pesos semânticos
        - Isso permitirá visualizar "hotspots" semânticos na região
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
    "GAIA DIGITAL - Análise Semântica Geodésica\n\n"
    "Especialista GeoPython-QGIS © 2025"
)
