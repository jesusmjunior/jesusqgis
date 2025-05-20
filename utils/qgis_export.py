import os
import tempfile
import zipfile
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_qgis_style_file(filepath, icon_type="ship"):
    """
    Cria um arquivo de estilo QML para QGIS com ícone personalizado.
    
    Args:
        filepath (str): Caminho do arquivo a ser estilizado
        icon_type (str): Tipo de ícone ('ship', 'flag', 'marker', etc.)
        
    Returns:
        str: Caminho do arquivo QML criado
    """
    # Definir o ícone com base no tipo selecionado
    icon_path = "transport/transport_nautical_harbour.svg"
    icon_color = "0,0,0,255"
    
    if icon_type == "ship":
        icon_path = "transport/transport_nautical_harbour.svg"
    elif icon_type == "flag":
        icon_path = "gpsicons/flag.svg"
    elif icon_type == "marker":
        icon_path = "gpsicons/pin_red.svg"
    elif icon_type == "tree":
        icon_path = "ecology/tree.svg" 
        icon_color = "0,100,0,255"
    elif icon_type == "water":
        icon_path = "water/water_tank.svg"
        icon_color = "0,0,255,255"
        
    # Criar conteúdo QML
    qml_content = f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="singleSymbol" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol name="0" force_rhr="0" type="marker" clip_to_extent="1" alpha="1">
        <layer locked="0" enabled="1" class="SvgMarker" pass="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="{icon_color}"/>
          <prop k="fixedAspectRatio" v="0"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="{icon_path}"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="{icon_color}"/>
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
    
    # Salvar para arquivo
    style_filepath = f"{filepath}.qml"
    with open(style_filepath, 'w') as f:
        f.write(qml_content)
    
    return style_filepath

def create_lidar_style_file(filepath):
    """
    Cria um arquivo de estilo QML para visualização de nuvem de pontos LiDAR no QGIS.
    
    Args:
        filepath (str): Caminho do arquivo a ser estilizado
        
    Returns:
        str: Caminho do arquivo QML criado
    """
    qml_content = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="categorizedSymbol" attr="Classification" symbollevels="0" enableorderby="0">
    <categories>
      <category symbol="0" value="1" label="Floresta"/>
      <category symbol="1" value="2" label="Água"/>
      <category symbol="2" value="3" label="Vegetação Baixa"/>
      <category symbol="3" value="4" label="Solo Exposto"/>
      <category symbol="4" value="5" label="Construções"/>
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
    
    # Salvar para arquivo
    style_filepath = f"{filepath}.qml"
    with open(style_filepath, 'w') as f:
        f.write(qml_content)
    
    return style_filepath

def create_elevation_style_file(filepath):
    """
    Cria um arquivo de estilo QML para visualização de dados de elevação (DEM) no QGIS.
    
    Args:
        filepath (str): Caminho do arquivo a ser estilizado
        
    Returns:
        str: Caminho do arquivo QML criado
    """
    qml_content = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.0-Białowieża" styleCategories="Symbology">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" band="1" type="singlebandpseudocolor" classificationMin="0" classificationMax="100">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" classificationMode="1" clip="0" labelPrecision="0">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="68,1,84,255"/>
            <prop k="color2" v="59,187,59,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.25;59,81,139,255:0.5;44,154,135,255:0.75;53,183,120,255"/>
          </colorramp>
          <item color="#440154" label="0" value="0" alpha="255"/>
          <item color="#3b528b" label="25" value="25" alpha="255"/>
          <item color="#2c9a87" label="50" value="50" alpha="255"/>
          <item color="#35b778" label="75" value="75" alpha="255"/>
          <item color="#3bbb3b" label="100" value="100" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
"""
    
    # Salvar para arquivo
    style_filepath = f"{filepath}.qml"
    with open(style_filepath, 'w') as f:
        f.write(qml_content)
    
    return style_filepath

def create_qgis_project_file(layers, output_file="amazon_project.qgs", 
                            title="Projeto Amazônia GAIA DIGITAL"):
    """
    Cria um arquivo de projeto QGIS completo com as camadas especificadas.
    
    Args:
        layers (list): Lista de dicionários com informações de camadas
                       Cada camada deve ter: 'path', 'name', 'type', e opcionalmente 'style'
        output_file (str): Nome do arquivo de projeto
        title (str): Título do projeto
        
    Returns:
        str: Caminho do arquivo de projeto QGIS criado
    """
    # Criar estrutura XML do projeto
    root = ET.Element("qgis")
    root.set("projectname", title)
    root.set("version", "3.22.0-Białowieża")
    
    # Adicionar sistema de referência
    projectcrs = ET.SubElement(root, "projectCrs")
    spatialrefsys = ET.SubElement(projectcrs, "spatialrefsys")
    ET.SubElement(spatialrefsys, "wkt").text = "GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563]],PRIMEM[\"Greenwich\",0],UNIT[\"degree\",0.0174532925199433]]"
    ET.SubElement(spatialrefsys, "proj4").text = "+proj=longlat +datum=WGS84 +no_defs"
    ET.SubElement(spatialrefsys, "srsid").text = "3452"
    ET.SubElement(spatialrefsys, "srid").text = "4326"
    ET.SubElement(spatialrefsys, "authid").text = "EPSG:4326"
    ET.SubElement(spatialrefsys, "description").text = "WGS 84"
    ET.SubElement(spatialrefsys, "projectionacronym").text = "longlat"
    ET.SubElement(spatialrefsys, "ellipsoidacronym").text = "WGS84"
    ET.SubElement(spatialrefsys, "geographicflag").text = "true"
    
    # Configurar visualização do mapa
    mapcanvas = ET.SubElement(root, "mapcanvas")
    mapcanvas.set("name", "theMapCanvas")
    ET.SubElement(mapcanvas, "units").text = "degrees"
    
    # Definir extensão do mapa (aproximadamente região amazônica)
    extent = ET.SubElement(mapcanvas, "extent")
    ET.SubElement(extent, "xmin").text = "-65.0"
    ET.SubElement(extent, "ymin").text = "-10.0"
    ET.SubElement(extent, "xmax").text = "-50.0"
    ET.SubElement(extent, "ymax").text = "0.0"
    ET.SubElement(mapcanvas, "rotation").text = "0"
    
    # Adicionar estrutura de camadas
    layer_tree_group = ET.SubElement(root, "layer-tree-group")
    
    # Adicionar camadas ao projeto
    layer_order = ET.SubElement(root, "layer-tree-canvas")
    custom_order = ET.SubElement(layer_order, "custom-order")
    custom_order.set("enabled", "0")
    
    # Mapas de propriedades
    mapcanvas_items = ET.SubElement(root, "mapcanvas-items")
    
    # Legendas
    legendlayers = ET.SubElement(root, "legendlayers")
    
    # Lista de camadas
    for i, layer in enumerate(layers):
        layer_id = f"layer_{i+1}_{os.path.basename(layer['path']).split('.')[0]}"
        
        # Criar elemento de camada na árvore
        layer_tree_layer = ET.SubElement(layer_tree_group, "layer-tree-layer")
        layer_tree_layer.set("id", layer_id)
        layer_tree_layer.set("name", layer['name'])
        layer_tree_layer.set("checked", "Qt::Checked")
        layer_tree_layer.set("expanded", "1")
        layer_tree_layer.set("source", layer['path'])
        
        # Criar propriedades da camada
        maplayer = ET.SubElement(root, "maplayer")
        maplayer.set("type", layer['type'])
        maplayer.set("geometry", "Point" if layer['type'] == "vector" else "")
        maplayer.set("id", layer_id)
        maplayer.set("name", layer['name'])
        maplayer.set("readOnly", "0")
        
        # Definir CRS da camada
        layercrs = ET.SubElement(maplayer, "srs")
        lspatialrefsys = ET.SubElement(layercrs, "spatialrefsys")
        ET.SubElement(lspatialrefsys, "wkt").text = "GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563]],PRIMEM[\"Greenwich\",0],UNIT[\"degree\",0.0174532925199433]]"
        ET.SubElement(lspatialrefsys, "proj4").text = "+proj=longlat +datum=WGS84 +no_defs"
        ET.SubElement(lspatialrefsys, "srsid").text = "3452"
        ET.SubElement(lspatialrefsys, "srid").text = "4326"
        ET.SubElement(lspatialrefsys, "authid").text = "EPSG:4326"
        
        # Se houver estilo, adicionar referência
        if 'style' in layer and layer['style']:
            pipe = ET.SubElement(maplayer, "pipe")
            renderer = ET.SubElement(pipe, "renderer-v2")
            renderer.set("type", "singleSymbol")
            # Mais elementos de estilo poderiam ser adicionados aqui
        
        # Adicionar à legenda
        legendlayer = ET.SubElement(legendlayers, "legendlayer")
        legendlayer.set("open", "true")
        legendlayer.set("checked", "Qt::Checked")
        legendlayer.set("name", layer['name'])
        legendlayer.set("showFeatureCount", "0")
        
        # Referência na ordem de camadas
        item = ET.SubElement(custom_order, "item")
        item.text = layer_id
    
    # Converter XML para string formatada
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    # Salvar para arquivo
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, output_file)
    with open(filepath, 'w') as f:
        f.write(xmlstr)
    
    return filepath

def create_qgis_project_package(layers, output_file="amazon_project.qgz", 
                               title="Projeto Amazônia GAIA DIGITAL"):
    """
    Cria um pacote de projeto QGIS (.qgz) com todas as camadas e estilos.
    
    Args:
        layers (list): Lista de dicionários com informações de camadas
        output_file (str): Nome do arquivo de projeto
        title (str): Título do projeto
        
    Returns:
        str: Caminho do arquivo de pacote QGIS criado
    """
    # Criar diretório temporário para o pacote
    temp_dir = tempfile.mkdtemp()
    project_base_name = output_file.replace('.qgz', '')
    
    # Criar arquivo de projeto QGIS
    project_file = create_qgis_project_file(layers, f"{project_base_name}.qgs", title)
    
    # Criar arquivo zipado (.qgz)
    temp_qgz = os.path.join(tempfile.gettempdir(), output_file)
    
    with zipfile.ZipFile(temp_qgz, 'w') as zipf:
        # Adicionar arquivo de projeto
        zipf.write(project_file, arcname=os.path.basename(project_file))
        
        # Adicionar camadas e estilos
        for layer in layers:
            # Adicionar arquivo da camada
            layer_file = layer['path']
            zipf.write(layer_file, arcname=os.path.basename(layer_file))
            
            # Adicionar estilo se existir
            if 'style' in layer and layer['style']:
                style_file = layer['style']
                zipf.write(style_file, arcname=os.path.basename(style_file))
    
    return temp_qgz

def prepare_export_files(files_dict):
    """
    Prepara todos os arquivos para exportação, criando um arquivo ZIP.
    
    Args:
        files_dict (dict): Dicionário com arquivos a incluir
                        {
                            'lidar': 'path/to/lidar.csv', 
                            'points': 'path/to/points.geojson',
                            'raster': 'path/to/elevation.tif'
                        }
        
    Returns:
        str: Caminho do arquivo ZIP criado
    """
    # Criar diretório temporário
    temp_dir = tempfile.mkdtemp()
    
    # Nome do arquivo ZIP
    temp_zip = os.path.join(tempfile.gettempdir(), "gaia_digital_qgis_export.zip")
    
    # Criar metadados para o pacote
    metadata = {
        "project": "GAIA DIGITAL",
        "description": "Análise geoespacial da Amazônia",
        "files": [],
        "instructions": {
            "pt_BR": "Abra o arquivo de projeto QGIS para visualizar todas as camadas configuradas.",
            "en_US": "Open the QGIS project file to view all configured layers."
        }
    }
    
    # Listar camadas para o projeto QGIS
    qgis_layers = []
    
    # Processar cada arquivo
    for key, filepath in files_dict.items():
        if not filepath or not os.path.exists(filepath):
            continue
        
        filename = os.path.basename(filepath)
        file_info = {
            "name": filename,
            "type": key,
            "path": filename  # Caminho relativo dentro do ZIP
        }
        
        # Adicionar ao metadados
        metadata["files"].append(file_info)
        
        # Configurar camada QGIS
        if key == "lidar":
            # Criar estilo para LiDAR
            style_path = create_lidar_style_file(filepath)
            qgis_layers.append({
                'path': filepath,
                'name': "Dados LiDAR",
                'type': "delimitedtext",
                'style': style_path
            })
            file_info["style"] = os.path.basename(style_path)
        elif key == "points":
            # Criar estilo para pontos com ícone de caravela
            style_path = create_qgis_style_file(filepath, "ship")
            qgis_layers.append({
                'path': filepath,
                'name': "Pontos de Interesse",
                'type': "vector",
                'style': style_path
            })
            file_info["style"] = os.path.basename(style_path)
        elif key == "raster":
            # Criar estilo para raster de elevação
            style_path = create_elevation_style_file(filepath)
            qgis_layers.append({
                'path': filepath,
                'name': "Modelo Digital de Elevação",
                'type': "raster",
                'style': style_path
            })
            file_info["style"] = os.path.basename(style_path)
    
    # Criar projeto QGIS
    if qgis_layers:
        project_file = create_qgis_project_file(qgis_layers, "amazonia_gaia_digital.qgs")
        project_info = {
            "name": os.path.basename(project_file),
            "type": "qgis_project",
            "path": os.path.basename(project_file)
        }
        metadata["files"].append(project_info)
    
    # Salvar metadados
    metadata_file = os.path.join(temp_dir, "metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Criar README
    readme_file = os.path.join(temp_dir, "README.txt")
    with open(readme_file, 'w') as f:
        f.write(f"""GAIA DIGITAL - Pacote de Dados Geoespaciais para QGIS
===================================================

Este pacote contém arquivos para análise geoespacial da Amazônia no QGIS.

ARQUIVOS INCLUÍDOS:
------------------
""")
        
        # Listar todos os arquivos incluídos
        for file_info in metadata["files"]:
            f.write(f"- {file_info['name']} ({file_info['type']})\n")
            if "style" in file_info:
                f.write(f"  Estilo: {file_info['style']}\n")
        
        f.write("""
INSTRUÇÕES:
----------
1. Extraia todos os arquivos para um diretório
2. Abra o arquivo de projeto QGIS (.qgs)
3. Se necessário, ajuste os caminhos das camadas no QGIS

Este pacote foi gerado pelo aplicativo GAIA DIGITAL para análise geoespacial amazônica.
""")
    
    # Criar arquivo ZIP com todos os arquivos
    with zipfile.ZipFile(temp_zip, 'w') as zipf:
        # Adicionar metadados e README
        zipf.write(metadata_file, arcname=os.path.basename(metadata_file))
        zipf.write(readme_file, arcname=os.path.basename(readme_file))
        
        # Adicionar todos os arquivos de dados e estilos
        for key, filepath in files_dict.items():
            if filepath and os.path.exists(filepath):
                zipf.write(filepath, arcname=os.path.basename(filepath))
                
                # Adicionar arquivo de estilo se existir
                style_path = f"{filepath}.qml"
                if os.path.exists(style_path):
                    zipf.write(style_path, arcname=os.path.basename(style_path))
        
        # Adicionar projeto QGIS
        if qgis_layers:
            zipf.write(project_file, arcname=os.path.basename(project_file))
    
    return temp_zip
