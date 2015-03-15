from __future__ import division

import os
from functools import partial
from math import asin, sqrt, cos
import numpy as np
import lensfunpy as lensfun
from draw import drawHeatmap, drawLinePlot, saveFig
from models import ptlens, poly3, poly5
from matplotlib.mlab import poly_between

def vectorLengths(vectors):
    return np.sqrt((vectors*vectors).sum(axis=1))

def lensDistortionDistance(mod, retH = False):
    '''
    Returns the difference between the distances from the image center to the distorted and undistorted
    pixel locations.
    .    
    :rtype: ndarray of shape (h,w)
    '''
    undistCoordsXY = mod.apply_geometry_distortion()
    
    height, width = undistCoordsXY.shape[0], undistCoordsXY.shape[1]

    y, x = np.mgrid[0:undistCoordsXY.shape[0], 0:undistCoordsXY.shape[1]]
    coordsXY = np.dstack((x,y))
    
    center = np.array([width/2, height/2])
    
    vectorsDist = (coordsXY - center).reshape(-1, 2)
    vectorsUndist = (undistCoordsXY - center).reshape(-1, 2)
    
    hDist = vectorLengths(vectorsDist).reshape(coordsXY.shape[0], coordsXY.shape[1])
    hUndist = vectorLengths(vectorsUndist).reshape(coordsXY.shape[0], coordsXY.shape[1])
    
    distance = hDist - hUndist
    
    if retH:
        return distance, hDist, hUndist
    else:
        return distance
    
def lensDistortionAbsoluteDistance(mod):
    return np.abs(lensDistortionDistance(mod))

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
    
camMaker = 'NIKON CORPORATION'
camModel = 'NIKON D3S'
lensMaker = 'Nikon'
lensModel = 'Nikkor 28mm f/2.8D AF'

db = lensfun.Database()
cam = db.find_cameras(camMaker, camModel)[0]
#lens = db.findLenses(cam, lensMaker, lensModel)[0]
lens = filter(lambda l: l.Maker == 'Contax', db.getLenses())[0]

distance = 10
focalLength = lens.min_focal
aperture = lens.min_aperture
width, height = 600, 400 # 3:2 aspect ratio
    
plotsPath = 'plots'
if not os.path.exists(plotsPath):
    os.mkdir(plotsPath)

mod = lensfun.Modifier(lens, cam.crop_factor, width, height)
mod.initialize(focalLength, aperture, distance, scale=1.0) # disable auto-scaling

dist = lensDistortionDistance(mod)
drawHeatmap(os.path.join(plotsPath, 'dist_actual_2d.svg'), dist)

distAbs = lensDistortionAbsoluteDistance(mod)
drawHeatmap(os.path.join(plotsPath, 'dist_absolute_2d.svg'), distAbs)

distRel = lensDistortionRelativeDistance(mod)
drawHeatmap(os.path.join(plotsPath, 'dist_relative_2d.svg'), distRel*100)

# get the internal models interpolated for the given focal length
calib = lens.interpolate_distortion(focalLength)
if calib.model == lensfun.DistortionModel.PTLENS:
    a,b,c = calib.terms
    rd = partial(ptlens, a=a, b=b, c=c, order=0)
    rd1 = partial(ptlens, a=a, b=b, c=c, order=1)    
    
elif calib.model == lensfun.DistortionModel.POLY3:
    k1,_,_ = calib.terms
    rd = partial(poly3, k1=k1, order=0)
    rd1 = partial(poly3, k1=k1, order=1)
    
elif calib.model == lensfun.DistortionModel.POLY5:
    k1,k2,_ = calib.terms
    rd = partial(poly5, k1=k1, k2=k2, order=0)
    rd1 = partial(poly5, k1=k1, k2=k2, order=1)
    
else:
    raise NotImplementedError

# calculate the sensor's (half) height, as it is used for scaling within lensfun
# TODO doesn't take into account the aspect ratio yet
wFX = 36
hFX = 24
dFX = sqrt(wFX**2 + hFX**2)
alpha = asin(wFX/dFX)
d = dFX*lens.CropFactor
h = cos(alpha)*d

sensorHalfHeight = h/2
sensorHalfDiagonal = d/2

X = np.linspace(0, sensorHalfDiagonal, 100)
Xscaled = X/sensorHalfHeight

fig, ax = drawLinePlot(X, 
                       (rd(Xscaled)-Xscaled)/Xscaled*100,
                       xlim=[0, sensorHalfDiagonal],
                       xlabel='$h\;(\mathrm{mm})$',
                       ylabel='distortion $D\;(\%)$',
                       )
saveFig(os.path.join(plotsPath, 'dist_relative_1d.svg'), fig)

fig, ax = drawLinePlot(X, 
                       rd1(Xscaled)*sensorHalfHeight,
                       xlim=[0, sensorHalfDiagonal], 
                       xlabel='$h\;(\mathrm{mm})$',
                       ylabel='$dD/dh\;(\mathrm{mm}^{-1})$',
                       )
# shade y>0 and y<0 with colors, to indicate pincushion vs. barrel distortion
alpha = 0.3
ymin, ymax = ax.get_ylim()
ax.autoscale(False)
polyPincushion = poly_between([0,sensorHalfDiagonal], 0, ymax)
ax.fill(*polyPincushion, alpha=alpha, facecolor='orange')
polyBarrel = poly_between([0,sensorHalfDiagonal], ymin, 0)
ax.fill(*polyBarrel, alpha=alpha, facecolor='blue')

saveFig(os.path.join(plotsPath, 'dist_derivative_1d.svg'), fig)

