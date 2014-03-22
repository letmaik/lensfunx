from __future__ import division

import os
import numpy as np
import lensfun

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from prettyplotlib.colors import blue_red

def vectorLengths(vectors):
    return np.sqrt((vectors*vectors).sum(axis=1))

def lensDistortionPixelDistances(mod):
    '''
    Returns the distance between distorted and undistorted location for each pixel.    
    :rtype: ndarray of shape (h,w)
    '''
    undistCoordsXY = mod.applyGeometryDistortion()

    y, x = np.mgrid[0:undistCoordsXY.shape[0], 0:undistCoordsXY.shape[1]]
    coordsXY = np.dstack((x,y))
    
    vectors = (coordsXY - undistCoordsXY).reshape(-1, 2)
    distances = vectorLengths(vectors).reshape(coordsXY.shape[0], coordsXY.shape[1])
    
    return distances

def drawHeatmap(data, path):
    fig, ax = plt.subplots()
    im = ax.imshow(data, cmap=blue_red)
    fig.colorbar(im)
    fig.savefig(path)
    plt.close(fig)
    
camMaker = 'NIKON CORPORATION'
camModel = 'NIKON D3S'
lensMaker = 'Nikon'
lensModel = 'Nikkor 28mm f/2.8D AF'

distance = 10
focalLength = lens.MinFocal
aperture = lens.MinAperture
width, height = 600, 400 # 3:2 aspect ratio

db = lensfun.Database()
cam = db.findCameras(camMaker, camModel)[0]
lens = db.findLenses(cam, lensMaker, lensModel)[0]

plotsPath = 'plots'
os.mkdir(plotsPath)

mod = lensfun.Modifier(lens, cam.CropFactor, width, height)
mod.initialize(focalLength, aperture, distance)
dist = lensDistortionPixelDistances(mod)
drawHeatmap(dist, os.path.join(plotsPath, 'dist.svg'))