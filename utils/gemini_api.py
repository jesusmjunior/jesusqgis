import os
import json
import base64
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def get_gemini_api_key():
    """
    Obtém a chave da API Gemini de forma segura, seguindo esta ordem:
    1. Arquivo .env
    2. Variáveis de ambiente do sistema
    3. Valor codificado (apenas para desenvolvimento)
    """
    # Tenta obter do .env primeiro
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Se não encontrar no .env, verifica variáveis de ambiente do sistema
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    # Se ainda não encontrar, usa valor de fallback (apenas para demonstração)
    if not api_key:
        # Para propósitos de demonstração, a chave é armazenada criptografada
        # Em produção, NUNCA use este método - sempre use variáveis de ambiente
        encoded_key = "QUl6YVN5RG8zTTZKejI2UVJ4Sm14Qzc2NW5TbElRSktEdmhXN0k4"
        api_key = base64.b64decode(encoded_key).decode('utf-8')
    
    return api_key

def query_gemini_api(prompt, temperature=0.2, max_tokens=2048):
    """
    Consulta a API Gemini para geração de conteúdo.
    
    Args:
        prompt (str): O prompt textual para enviar à API
        temperature (float): Controla aleatoriedade (0.0 a 1.0)
        max_tokens (int): Número máximo de tokens na resposta
        
    Returns:
        str: Texto gerado ou None em caso de erro
    """
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
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Lança exceção para códigos de erro HTTP
        
        result = response.json()
        
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            print(f"Erro ao processar resposta da API: {e}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição à API Gemini: {e}")
        return None

def extract_coordinates_from_text(text):
    """
    Utiliza a API Gemini para extrair coordenadas geográficas de um texto.
    
    Args:
        text (str): Texto contendo descrições de locais
        
    Returns:
        list: Lista de dicionários com coordenadas extraídas
    """
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
                print("Formato de coordenadas não identificado na resposta.")
                return []
        except Exception as e:
            print(f"Erro ao processar coordenadas: {e}")
            return []
    
    return []

def generate_geo_analysis(region_text, coordinates):
    """
    Gera uma análise geoespacial detalhada para a região usando a API Gemini.
    
    Args:
        region_text (str): Descrição da região 
        coordinates (list): Lista de coordenadas extraídas
        
    Returns:
        str: Análise detalhada da região
    """
    prompt = f"""
    Realize uma análise geoespacial da seguinte região amazônica:
    {region_text}
    
    Locais identificados:
    {', '.join([f"{c['name']} ({c['type']})" for c in coordinates])}
    
    Forneça uma análise detalhada sobre:
    1. Potenciais riscos ambientais na região
    2. Características geomorfológicas notáveis
    3. Recomendações para monitoramento ambiental
    4. Pontos de interesse para um estudo de campo
    
    Estruture a resposta em tópicos claros.
    """
    
    return query_gemini_api(prompt, temperature=0.3, max_tokens=4096)

def generate_lidar_sampling_strategy(region_text, coordinates):
    """
    Gera uma estratégia de amostragem LiDAR personalizada para a região.
    
    Args:
        region_text (str): Descrição da região
        coordinates (list): Lista de coordenadas extraídas
        
    Returns:
        dict: Estratégia de amostragem com parâmetros recomendados
    """
    prompt = f"""
    Com base na descrição da região amazônica a seguir e nas coordenadas extraídas,
    sugira os melhores parâmetros para uma amostragem LiDAR:
    
    Região: {region_text}
    
    Coordenadas: {json.dumps(coordinates)}
    
    Responda APENAS com um JSON no seguinte formato:
    {{
        "densidade_pontos": <número recomendado entre 500 e 5000>,
        "raio_amostragem": <valor entre 0.01 e 0.2>,
        "altitude_voo": <valor recomendado em metros>,
        "areas_prioritarias": [<lista de 2-3 áreas prioritárias com breve justificativa>],
        "epoca_ideal": "<melhor período do ano para coleta>"
    }}
    """
    
    result = query_gemini_api(prompt, temperature=0.2)
    
    if result:
        try:
            # Encontra e extrai o objeto JSON
            import re
            json_match = re.search(r'{.*}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                strategy = json.loads(json_str)
                return strategy
            else:
                print("Formato de estratégia não identificado na resposta.")
                return {}
        except Exception as e:
            print(f"Erro ao processar estratégia LiDAR: {e}")
            return {}
    
    return {}

# Exemplo de uso
if __name__ == "__main__":
    # Testar a API
    test_text = "Quero analisar a região próxima a Manaus, especialmente as áreas de confluência do Rio Negro com o Rio Solimões."
    coords = extract_coordinates_from_text(test_text)
    print("Coordenadas extraídas:", coords)
    
    if coords:
        strategy = generate_lidar_sampling_strategy(test_text, coords)
        print("Estratégia LiDAR:", strategy)
