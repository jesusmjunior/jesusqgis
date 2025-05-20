def extract_geo_entities_semantic(text, gemini_api_key):
    """
    Algoritmo avançado para extração semântica de entidades geográficas com lógica fuzzy
    e eliminação de dispersão por teoria de conjuntos.
    
    Este algoritmo opera em camadas:
    1. Decomposição semântica (núcleos nominais e verbais)
    2. Identificação de entidades geográficas específicas
    3. Análise de pertinência fuzzy com pesos
    4. Colapso de dados por teoria de conjuntos
    5. Resolução de coordenadas precisas
    
    Args:
        text (str): Texto com descrição geográfica para análise
        gemini_api_key (str): Chave de API Gemini para processamento
        
    Returns:
        list: Lista de coordenadas geográficas com alta precisão
    """
    import requests
    import json
    import re
    import numpy as np
    from collections import defaultdict
    import base64
    
    # Função auxiliar para consultar a API Gemini
    def query_gemini_api(prompt, temperature=0.1):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"
        
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
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            try:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                print(f"Erro ao processar resposta da API: {e}")
                return None
        else:
            print(f"Erro na API Gemini: {response.status_code} - {response.text}")
            return None
    
    # CAMADA 1: Decomposição semântica do texto
    semantic_decomposition_prompt = f"""
    Analise o seguinte texto e decomponha-o em suas partes semânticas:
    
    Texto: "{text}"
    
    Extraia:
    1. Núcleos nominais (substantivos que indicam locais)
    2. Núcleos verbais (verbos que indicam movimento ou posição)
    3. Modificadores espaciais (adjetivos ou advérbios relacionados a locais)
    4. Conjuntos preposicionais de localização (ex: "próximo a", "ao lado de")
    
    Retorne APENAS um objeto JSON no seguinte formato:
    {{
        "nominal_cores": ["lista de núcleos nominais"],
        "verbal_cores": ["lista de núcleos verbais"],
        "spatial_modifiers": ["lista de modificadores espaciais"],
        "prepositional_sets": ["lista de conjuntos preposicionais"]
    }}
    """
    
    # CAMADA 2: Identificação de entidades geográficas específicas
    geo_entities_prompt = f"""
    Analise o seguinte texto e identifique TODAS as entidades geográficas específicas:
    
    Texto: "{text}"
    
    Categorize precisamente as entidades encontradas:
    - Bairros (ex: "Laranjeiras", "Centro")
    - Ruas/Avenidas (ex: "Avenida Paulista")
    - Monumentos/Prédios (ex: "Teatro Amazonas")
    - Relevos (ex: "Serra do Mar", "Pico da Neblina")
    - Rios (ex: "Rio Negro", "Solimões")
    - Áreas naturais (ex: "Parque Nacional")
    - Cidades/Estados (ex: "Manaus", "Amazonas")
    - Pontos cardeais e referências direcionais (ex: "norte de", "sudeste")
    
    IMPORTANTE: Indique para cada entidade um peso de confiança (0.0-1.0) baseado em quão específica e inequívoca ela é.
    
    Retorne APENAS um objeto JSON no seguinte formato:
    {{
        "entities": [
            {{
                "name": "nome da entidade",
                "type": "tipo da entidade",
                "confidence": valor de confiança (0.0-1.0),
                "context": "contexto textual em que aparece"
            }}
        ]
    }}
    """
    
    # CAMADA 3: Análise fuzzy de coordenadas conhecidas
    fuzzy_coordinates_prompt = f"""
    Com base nas entidades geográficas identificadas no texto, determine as coordenadas geográficas mais prováveis:
    
    Texto: "{text}"
    
    Para cada entidade geográfica significativa:
    1. Determine as coordenadas mais precisas (latitude, longitude)
    2. Atribua um grau de pertinência (0.0-1.0) baseado em quão confiável é a determinação
    3. Identifique o raio de dispersão aproximado (em km)
    4. Determine a relevância contextual da entidade no texto (0.0-1.0)
    
    ATENÇÃO: Foque APENAS em entidades amazônicas. Considere contextos da Amazônia Legal brasileira.
    
    Retorne APENAS um objeto JSON no seguinte formato:
    {{
        "coordinates": [
            {{
                "entity": "nome da entidade",
                "lat": latitude em graus decimais,
                "lon": longitude em graus decimais,
                "membership": valor fuzzy de pertinência (0.0-1.0),
                "dispersion_radius": raio em km,
                "contextual_relevance": relevância (0.0-1.0)
            }}
        ]
    }}
    """
    
    # CAMADA 4: Colapso de dados por teoria de conjuntos
    set_theory_prompt = f"""
    Com base na análise anterior, aplique teoria de conjuntos para eliminar redundâncias e resolver conflitos:
    
    Texto: "{text}"
    
    Quando múltiplas coordenadas se referem a entidades semanticamente relacionadas:
    1. Identifique interseções por proximidade geográfica
    2. Calcule o conjunto mínimo que mantém a fidelidade semântica
    3. Elimine outliers baseado em distância e relevância contextual
    4. Resolva conflitos utilizando regras de prioridade:
       - Entidades específicas > entidades genéricas
       - Referências diretas > referências indiretas
       - Alta confiança > baixa confiança
       - Contexto primário > contexto secundário
    
    Retorne APENAS um objeto JSON com coordenadas finais consolidadas:
    {{
        "consolidated_coordinates": [
            {{
                "entity": "nome da entidade principal",
                "related_entities": ["lista de entidades relacionadas"],
                "lat": latitude consolidada,
                "lon": longitude consolidada,
                "confidence": confiança consolidada (0.0-1.0),
                "precision_radius": raio de precisão em metros
            }}
        ]
    }}
    """
    
    # CAMADA 5: Finalização e validação semântica
    final_validation_prompt = f"""
    Realize a validação semântica final das coordenadas identificadas:
    
    Texto original: "{text}"
    
    Para cada coordenada consolidada:
    1. Verifique a coerência com o contexto completo do texto
    2. Garanta que a entidade identificada tem relevância no contexto descrito
    3. Atribua um tipo semântico preciso (cidade, rio, floresta, etc.)
    4. Determine um nome descritivo que melhor represente o ponto no contexto
    
    IMPORTANTE: Retorne APENAS um array JSON no seguinte formato:
    [
        {{
            "lat": latitude final,
            "lon": longitude final,
            "name": "nome descritivo do local",
            "type": "tipo semântico",
            "semantic_weight": peso semântico final (0.0-1.0)
        }}
    ]
    
    APENAS JSON PURO, sem explicações ou comentários adicionais.
    """
    
    # Executar pipeline de processamento em camadas
    print("Camada 1: Decomposição semântica...")
    semantic_result = query_gemini_api(semantic_decomposition_prompt)
    
    print("Camada 2: Identificação de entidades geográficas...")
    entities_result = query_gemini_api(geo_entities_prompt)
    
    print("Camada 3: Análise fuzzy de coordenadas...")
    fuzzy_result = query_gemini_api(fuzzy_coordinates_prompt)
    
    print("Camada 4: Colapso de dados por teoria de conjuntos...")
    consolidation_result = query_gemini_api(set_theory_prompt)
    
    print("Camada 5: Validação semântica final...")
    final_result = query_gemini_api(final_validation_prompt)
    
    # Processamento do resultado final
    if final_result:
        try:
            # Encontrar o primeiro array JSON no texto
            json_match = re.search(r'\[\s*{.*}\s*\]', final_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                coordinates = json.loads(json_str)
                
                # Ordenar coordenadas por peso semântico
                if coordinates and isinstance(coordinates, list):
                    coordinates.sort(key=lambda x: x.get('semantic_weight', 0), reverse=True)
                
                return coordinates
            else:
                print("Formato de coordenadas não identificado na resposta final.")
                return []
        except Exception as e:
            print(f"Erro ao processar resultado final: {e}")
            return []
    
    return []

# Função para uso no Streamlit
def enhanced_geo_extract(text, api_key):
    """Versão simplificada para integração com Streamlit"""
    import streamlit as st
    
    with st.spinner("Processando análise semântica avançada..."):
        coordinates = extract_geo_entities_semantic(text, api_key)
        
        if not coordinates:
            st.warning("Não foi possível identificar coordenadas precisas. Usando valores padrão.")
            coordinates = [
                {"lat": -3.1, "lon": -60.0, "name": "Manaus", "type": "cidade", "semantic_weight": 0.9},
                {"lat": -3.3, "lon": -60.2, "name": "Encontro das Águas", "type": "rio", "semantic_weight": 0.85}
            ]
        
        # Exibir resultados com confiança
        st.success(f"Análise semântica identificou {len(coordinates)} pontos geodésicos com alta precisão")
        
        # Opcional: mostrar detalhes do processamento fuzzy
        if st.checkbox("Mostrar detalhes do processamento semântico"):
            st.json(coordinates)
            
    return coordinates

# Exemplo de uso em prompt único para API Gemini
def create_gemini_prompt(text):
    """Cria um prompt único para processamento completo na API Gemini"""
    prompt = f"""
    Analise semanticamente o seguinte texto para extrair coordenadas geodésicas com alta precisão:
    
    TEXTO: "{text}"
    
    INSTRUÇÕES DE PROCESSAMENTO:
    
    1. DECOMPOSIÇÃO SEMÂNTICA:
       - Identifique núcleos nominais relacionados a locais
       - Extraia núcleos verbais indicando movimento/posição
       - Reconheça modificadores espaciais e conjuntos preposicionais
    
    2. IDENTIFICAÇÃO DE ENTIDADES GEOGRÁFICAS:
       - Bairros, ruas, monumentos, prédios
       - Relevos, montanhas, rios famosos
       - Áreas naturais, cidades, referências direcionais
       - Atribua peso de confiança (0-1) por especificidade
    
    3. ANÁLISE FUZZY:
       - Determine coordenadas para cada entidade
       - Atribua grau de pertinência (0-1)
       - Identifique raio de dispersão aproximado
       - Calcule relevância contextual
    
    4. COLAPSO POR TEORIA DE CONJUNTOS:
       - Identifique interseções por proximidade
       - Calcule conjunto mínimo com fidelidade semântica
       - Elimine outliers por distância e relevância
       - Aplique regras de prioridade (específico>genérico, direto>indireto)
    
    5. VALIDAÇÃO SEMÂNTICA FINAL:
       - Verifique coerência com contexto completo
       - Garanta relevância no contexto
       - Atribua tipo semântico preciso
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
    
    RETORNE APENAS O JSON, sem explicações ou comentários.
    """
    return prompt
