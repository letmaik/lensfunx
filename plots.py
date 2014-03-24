from __future__ import division

import os
import numpy as np
import numpy.ma as ma
import lensfun

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from prettyplotlib.colors import blue_red

def vectorLengths(vectors):
    return np.sqrt((vectors*vectors).sum(axis=1))

def lensDistortionDistance(mod, retH = False):
    '''
    Returns the difference between the distances from the image center to the distorted and undistorted
    pixel locations.
    .    
    :rtype: ndarray of shape (h,w)
    '''
    undistCoordsXY = mod.applyGeometryDistortion()
    
    height, width = undistCoordsXY.shape[0], undistCoordsXY.shape[1]

    y, x = np.mgrid[0:undistCoordsXY.shape[0], 0:undistCoordsXY.shape[1]]
    coordsXY = np.dstack((x,y))
    
    center = np.array([width/2, height/2])
    
    # TODO not sure if this is right, maybe roles need to be switched
    vectorsDist = (coordsXY - center).reshape(-1, 2)
    vectorsUndist = (undistCoordsXY - center).reshape(-1, 2)
    
    hDist = vectorLengths(vectorsDist).reshape(coordsXY.shape[0], coordsXY.shape[1])
    hUndist = vectorLengths(vectorsUndist).reshape(coordsXY.shape[0], coordsXY.shape[1])
    
    distance = hDist - hUndist
    
    if retH:
        return distance, hDist, hUndist
    else:
        return distance

def lensDistortionRelativeDistance(mod):
    '''
    Returns the relative difference between the distances from the image center to the distorted and undistorted
    pixel locations.
    :rtype: ndarray of shape (h,w)
    '''
    distance, _, hUndist = lensDistortionDistance(mod, retH=True)
    distanceRelative = distance / hUndist
    # TODO make this more clever
    distanceRelative[distanceRelative < -0.99] = np.nan
    distanceRelative[distanceRelative > 0.99] = np.nan

    return distanceRelative

def drawHeatmap(data, path):
    data = ma.masked_invalid(data, copy=False)
    fig, ax = plt.subplots()
    im = ax.imshow(data, cmap=blue_red)
    fig.colorbar(im)
    fig.savefig(path)
    plt.close(fig)
    
camMaker = 'NIKON CORPORATION'
camModel = 'NIKON D3S'
lensMaker = 'Nikon'
lensModel = 'Nikkor 28mm f/2.8D AF'

db = lensfun.Database()
cam = db.findCameras(camMaker, camModel)[0]
lens = db.findLenses(cam, lensMaker, lensModel)[0]

distance = 10
focalLength = lens.MinFocal
aperture = lens.MinAperture
width, height = 600, 400 # 3:2 aspect ratio

plotsPath = 'plots'
if not os.path.exists(plotsPath):
    os.mkdir(plotsPath)

mod = lensfun.Modifier(lens, cam.CropFactor, width, height)
mod.initialize(focalLength, aperture, distance)

dist = lensDistortionDistance(mod)
drawHeatmap(dist, os.path.join(plotsPath, 'dist.svg'))

distRel = lensDistortionRelativeDistance(mod)
drawHeatmap(distRel, os.path.join(plotsPath, 'dist_rel.svg'))