# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 15:00:36 2024

@author: rodri
"""
#%%

import numpy as np
from pysheds.grid import Grid
import seaborn as sns
import matplotlib.colors as colors
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings('ignore')

#%%
grid = Grid.from_raster('C:/Users/rodri/Documents/testes/hidro/Nova pasta/s24_w047_1arc_v3.tif', data_name='dem')

#%%
grid.fill_depressions(data='dem', out_name='flooded_dem')

grid.resolve_flats('flooded_dem', out_name='inflated_dem')

#%%
dirmap = (64,  128,  1,   2,    4,   8,    16,  32)

grid.flowdir(data='inflated_dem', out_name='dir', dirmap=dirmap)
boundaries = ([0] + sorted(list(dirmap)))

#%%
# Specify pour point
x, y = -46.467348,  -22.908965

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

#%%
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

#%%

grid.flow_distance(data='catch', x=x, y=y, dirmap=dirmap, out_name='dist',
                   xytype='label', nodata_out=np.nan)

fig, ax = plt.subplots(figsize=(10, 8))

im = ax.imshow(grid.dist, extent=grid.extent, zorder=2,
               cmap='cubehelix_r')
plt.colorbar(im, ax=ax, label='Distance to outlet (cells)')
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('Flow Distance', fontsize=16)
#%%

branches = grid.extract_river_network('catch', 'acc')

fig, ax = plt.subplots(figsize=(10, 8))
for branch in branches['features']:
    line = np.asarray(branch['geometry']['coordinates'])
    ax.plot(line[:, 0], line[:, 1])
    
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('River Network (>100 accumulation )', fontsize=16)
#%%

branches_5 = grid.extract_river_network('catch', 'acc', threshold=5)

fig, ax = plt.subplots(figsize=(10, 8))
for branch in branches_5['features']:
    line = np.asarray(branch['geometry']['coordinates'])
    ax.plot(line[:, 0], line[:, 1])
    
_= ax.set_xlabel('Longitude')
_= ax.set_ylabel('Latitude')
_= ax.set_title('River Network (>5 accumulation )', fontsize=16)
#%%
