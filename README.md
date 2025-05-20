# GAIA DIGITAL - Ambiente de Desenvolvimento

Este arquivo contém instruções para configurar o ambiente de desenvolvimento para o aplicativo Streamlit de análise geoespacial da Amazônia.

## Dependências

Instale as dependências necessárias usando o seguinte comando:

```bash
pip install streamlit folium streamlit-folium geopandas shapely pandas numpy requests python-dotenv matplotlib rasterio pillow
```

## Configuração das Variáveis de Ambiente

Crie um arquivo `.env` na mesma pasta do aplicativo com o seguinte conteúdo:

```
GEMINI_API_KEY=sua_chave_aqui
```

## Executando o Aplicativo

Execute o aplicativo com o comando:

```bash
streamlit run app.py
```

## Configuração Alternativa para o QGIS

Para integração completa com QGIS, você também pode instalar os seguintes pacotes:

```bash
pip install qgis-plugin-tools pyqgis qgis-processing
```

Note que a instalação do PyQGIS pode ser complexa e depende da sua plataforma. Consulte a documentação oficial do QGIS para mais informações.

## Estrutura de Diretórios Recomendada

```
gaia-digital/
├── app.py                # Aplicativo Streamlit principal
├── .env                  # Arquivo de variáveis de ambiente (não comitar)
├── requirements.txt      # Dependências do projeto
├── README.md             # Documentação
├── data/                 # Dados de exemplo ou estáticos
│   ├── icons/            # Ícones personalizados (como caravela)
│   └── sample_regions/   # Regiões de exemplo da Amazônia
└── utils/                # Módulos utilitários Python
    ├── lidar_processing.py
    ├── gemini_api.py
    └── qgis_export.py
```

## Notas sobre Segurança

- Nunca comite seu arquivo `.env` ou credenciais API para repositórios públicos
- A chave da API no código está codificada apenas para fins de demonstração
- Em ambiente de produção, sempre use variáveis de ambiente ou serviços de gerenciamento de segredos

## Recursos Adicionais

- [Documentação do Streamlit](https://docs.streamlit.io/)
- [Documentação do Folium](https://python-visualization.github.io/folium/)
- [Documentação do GeoPandas](https://geopandas.org/en/stable/)
- [Documentação da API Gemini](https://ai.google.dev/docs/gemini_api_overview)
- [Documentação do QGIS Python API](https://qgis.org/pyqgis/3.0/)
