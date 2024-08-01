# README

Modelos de elevação digital (DEMs) são frequentemente usados ​​para delineamento de bacias hidrográficas e dados extraídos da bacia hidrográfica delineada são relevantes, exigidos por modelos hidrológicos distribuídos.

Uma bacia hidrográfica é a área de declive que contribui com o fluxo — geralmente água — para uma saída comum como drenagem concentrada. Pode ser parte de uma bacia hidrográfica maior e também pode conter bacias hidrográficas menores, chamadas sub-bacias. Os limites entre bacias hidrográficas são denominados divisores de drenagem. A saída, ou ponto de escoamento, é o ponto na superfície em que a água flui para fora de uma área. É o ponto mais baixo ao longo do limite de uma bacia hidrográfica. Uma bacia hidrográfica pode ser delineada a partir de um modelo de elevação digital (DEM) calculando a direção do fluxo.

Este README mostrará como delinear bacias hidrográficas a partir de um modelo de elevação digital (DEM) com base no pacote python do pysheds. O Pysheds é um pacote Python 3 projetado para delimitação de bacias hidrográficas e extração de rede de fluxo. Esta biblioteca requer um conjunto de bibliotecas avançadas de processamento de dados e análise espacial como Numpy, Pandas, Scipy, Scikit-Image,  e outras.

A versão mais recente do Pysheds permite o uso de modelos de elevação digital em coordenadas geográficas (WGS84 como neste notebook) e coordenadas projetadas (WGS 84 UTM). Este recurso aumenta a versatilidade da análise hidrológica. Além disso, o Pysheds fornece muitos tutoriais excelentes.
```bash
import numpy as np
from pysheds.grid import Grid
import seaborn as sns
import matplotlib.colors as colors
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings('ignore')
```



```python
grid = Grid.from_raster('data/n30w100_con', data_name='dem')
```



É importante usar um DEM sem ***depressões*** ou ***sumidouros***. Um sumidouro é uma célula que não tem um valor de drenagem associado. Os valores de drenagem indicam a direção em que a água fluirá para fora da célula e são atribuídos durante o processo de criação de uma grade de direção de fluxo para a paisagem. A rede de drenagem resultante depende de encontrar o "caminho de fluxo" de cada célula na grade, portanto, é importante que a etapa de preenchimento seja realizada antes de criar uma grade de direção de fluxo.

Duas tarefas de pré-processamento incluem:
- Detectar e preencher depressões
- Detectar e resolver flats

```python
grid.fill_depressions(data='dem', out_name='flooded_dem')

grid.resolve_flats('flooded_dem', out_name='inflated_dem')
```

## Calcular direções de fluxo

Uma grade de direção de fluxo atribui um valor a cada célula para indicar a direção do fluxo, ou seja, a direção em que a água fluirá daquela célula específica com base na topografia subjacente da paisagem. Esta é uma etapa crucial na modelagem hidrológica, pois a direção do fluxo determinará o destino final da água que flui pela superfície da terra.

Por padrão, o pysheds calculará as direções de fluxo usando o ***esquema de roteamento D8***. Neste modo de roteamento, cada célula é roteada para uma das oito células vizinhas com base na direção da descida mais íngreme.

***Mapeamentos direcionais***

As direções cardeais e intercardinais são representadas por valores numéricos na grade de saída. Por padrão, o esquema ESRI é usado:

- Norte: 64
- Nordeste: 128
- Leste: 1
- Sudeste: 2
- Sul: 4
- Sudoeste: 8
- Oeste: 16
- Noroeste: 32

```python
#         N    NE    E    SE    S    SW    W    NW
dirmap = (64,  128,  1,   2,    4,   8,    16,  32)

grid.flowdir(data='inflated_dem', out_name='dir', dirmap=dirmap)
boundaries = ([0] + sorted(list(dirmap)))
```

## Delinear captação

Para delinear uma captação, primeiro especifique um ***ponto de escoamento*** (a ***saída*** da captação). O posicionamento do ponto de escoamento é uma etapa importante no processo de delineamento da bacia hidrográfica. Um ponto de escoamento deve existir dentro de uma área de alto acúmulo de fluxo porque é usado para calcular o fluxo total de água contribuinte para aquele ponto dado. Em muitos casos, você já pode saber onde estão os locais dos seus pontos de escoamento. Se os componentes x e y do ponto de escoamento forem coordenadas espaciais no sistema de referência espacial da grade, especifique xytype='label'.

```python
# Specify pour point
x, y = -97.294167, 32.73750

# Delineate the catchment
grid.catchment(data='dir', x=x, y=y, dirmap=dirmap, out_name='catch',
               recursionlimit=15000, xytype='label', nodata_out=0)

# Clip the bounding box to the catchment
grid.clip_to('catch')

# Get a view of the catchment
catch = grid.view('catch', nodata=np.nan)

# Plot the catchment
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(catch, extent=grid.extent, zorder=1, cmap='viridis')
plt.colorbar(im, ax=ax, boundaries=boundaries, values=sorted(dirmap), label='Flow Direction')
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('Delineated Catchment', fontsize=16)
```

## Obter acumulação de fluxo

A ferramenta Flow Accumulation calcula o fluxo em cada célula identificando as células a montante que fluem para cada célula a jusante. Em outras palavras, o valor de acumulação de fluxo de cada célula é determinado pelo número de células a montante que fluem para ela com base na topografia da paisagem.

```python
grid.accumulation(data='catch', dirmap=dirmap, out_name='acc')
acc_img = np.where(grid.mask, grid.acc + 1, np.nan)

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(acc_img, extent=grid.extent, zorder=2,
               cmap='cubehelix',
               norm=colors.LogNorm(1, grid.acc.max()))
plt.colorbar(im, ax=ax, label='Upstream Cells')
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('Flow Accumulation', fontsize=16)
```



```python
grid.flow_distance(data='catch', x=x, y=y, dirmap=dirmap, out_name='dist',
                   xytype='label', nodata_out=np.nan)

fig, ax = plt.subplots(figsize=(10, 8))

im = ax.imshow(grid.dist, extent=grid.extent, zorder=2,
               cmap='cubehelix_r')
plt.colorbar(im, ax=ax, label='Distance to outlet (cells)')
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('Flow Distance', fontsize=16)
```

## Extraindo a rede fluvial

Para extrair a rede fluvial em um dado limite de acumulação, podemos chamar o método grid.extract_river_network. Por padrão, o método usará um limite de acumulação de 100 células:

```python
branches = grid.extract_river_network('catch', 'acc')

fig, ax = plt.subplots(figsize=(10, 8))
for branch in branches['features']:
    line = np.asarray(branch['geometry']['coordinates'])
    ax.plot(line[:, 0], line[:, 1])
    
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('River Network (>100 accumulation )', fontsize=16)
```

***Especificando o limite de acumulação***

Podemos alterar a geometria da rede fluvial retornada especificando diferentes limites de acumulação. Por exemplo, definimos limite=5. No entanto, limites menores produzirão muitos ramos que podem estar sobre detalhes.

```python
branches_5 = grid.extract_river_network('catch', 'acc', threshold=5)

fig, ax = plt.subplots(figsize=(10, 8))
for branch in branches_5['features']:
    line = np.asarray(branch['geometry']['coordinates'])
    ax.plot(line[:, 0], line[:, 1])
    
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('River Network (>5 accumulation )', fontsize=16)
```

Documentaçao https://mattbartos.com/pysheds/
