import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import requests
import base64
from PIL import Image
from io import BytesIO
import time

# Configuração da página
st.set_page_config(
    page_title="GAIA DIGITAL - GeoAnálise Amazônica",
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

def create_download_link(df, filename, link_text):
    """Cria um link para download de um DataFrame como CSV."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

# --------- INTERFACE DO APLICATIVO STREAMLIT ---------
st.title("🌎 GAIA DIGITAL - Análise Geoespacial Amazônica")
st.markdown("""
Este aplicativo gera análises geoespaciais para a região Amazônica,
utilizando inteligência artificial para processar descrições textuais e gerar
camadas compatíveis com QGIS, incluindo dados LiDAR simulados.
""")

# Barra lateral com opções
st.sidebar.title("Configurações")

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
    
    # Exibir coordenadas encontradas
    st.subheader("Coordenadas Identificadas")
    coord_df = pd.DataFrame(coordinates)
    st.dataframe(coord_df)
    
    # Criar dados LiDAR simulados
    center_lat = sum(c["lat"] for c in coordinates) / len(coordinates)
    center_lon = sum(c["lon"] for c in coordinates) / len(coordinates)
    
    lidar_data = generate_lidar_sample(center_lat, center_lon, lidar_radius, lidar_density)
    
    # Visualizar amostra dos dados LiDAR
    st.subheader("Amostra de Dados LiDAR (Simulados)")
    st.dataframe(lidar_data.head(10))
    
    # Criar visualização simples com matplotlib
    st.subheader("Visualização de Elevação LiDAR")
    
    # Plotar dados 2D coloridos por elevação
    fig, ax = st.columns(2)
    with fig:
        from matplotlib import pyplot as plt
        
        # Criar figura
        plt.figure(figsize=(10, 6))
        plt.scatter(lidar_data['X'], lidar_data['Y'], c=lidar_data['Z'], 
                   cmap='terrain', alpha=0.6, s=2)
        plt.colorbar(label='Elevação (m)')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Dados LiDAR Simulados (Vista de Topo)')
        
        # Exibir
        st.pyplot(plt)
    
    # Seção de downloads
    st.subheader("Exportar para QGIS")
    
    # Criar links de download
    st.markdown(create_download_link(lidar_data, "amazonia_lidar.csv", 
                                   "⬇️ Download Dados LiDAR (CSV)"), unsafe_allow_html=True)
    
    # Criar um arquivo GeoJSON simplificado para os pontos
    st.markdown("""
    ```javascript
    {
      "type": "FeatureCollection",
      "features": [
    """ + ",\n".join([f"""    {{
      "type": "Feature",
      "properties": {{
        "name": "{point['name']}",
        "type": "{point['type']}"
      }},
      "geometry": {{
        "type": "Point",
        "coordinates": [{point['lon']}, {point['lat']}]
      }}
    }}""" for point in coordinates]) + """
      ]
    }
    ```
    """)
    
    # Instruções para QGIS
    with st.expander("Como importar no QGIS"):
        st.markdown("""
        1. Baixe o arquivo CSV com dados LiDAR
        2. No QGIS, vá para "Camada > Adicionar Camada > Adicionar Camada de Texto Delimitado"
        3. Selecione o arquivo CSV baixado
        4. Especifique "X" como longitude e "Y" como latitude (ou coordenadas X/Y)
        5. Selecione CRS EPSG:4326 (WGS 84)
        6. Para os pontos de interesse, crie um arquivo GeoJSON copiando o texto acima
        7. Para adicionar o ícone de caravela, use um símbolo SVG personalizado em "Simbologia"
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
