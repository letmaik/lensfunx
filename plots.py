from __future__ import division

import os
from functools import partial
from math import asin, sqrt, cos
import numpy as np
import lensfun
from draw import drawHeatmap, drawLinePlot, poly_between, saveFig

def ptlens(ru, a, b, c, order=0):
    if order == 0:
        return ru*(a*ru**3 + b*ru**2 + c*ru + 1 - a - b- c)
    else:
        return 3*a*ru**2 + 2*b*ru + c

def poly3(ru, k1, order=0):
    if order == 0:
        return ru*(1 - k1 + k1*ru**2)
    else:
        return 2*k1*ru

def poly5(ru, k1, k2, order=0):
    if order == 0:
        return ru*(1 + k1*ru**2 + k2*ru**4)
    elif order == 1:
        return 2*k1*ru + 4*k2*ru**3

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
cam = db.findCameras(camMaker, camModel)[0]
#lens = db.findLenses(cam, lensMaker, lensModel)[0]
lens = filter(lambda l: l.Maker == 'Contax', db.getLenses())[0]

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
drawHeatmap(os.path.join(plotsPath, 'dist_actual_2d.svg'), dist)

distAbs = lensDistortionAbsoluteDistance(mod)
drawHeatmap(os.path.join(plotsPath, 'dist_absolute_2d.svg'), distAbs)

distRel = lensDistortionRelativeDistance(mod)
drawHeatmap(os.path.join(plotsPath, 'dist_relative_2d.svg'), distRel*100)

# get the internal models interpolated for the given focal length
calib = lens.interpolateDistortion(focalLength)
if calib.Model == lensfun.DistortionModel.PTLENS:
    a, b, c = calib.Terms
    rd = partial(ptlens, a=a, b=b, c=c, order=0)
    rd1 = partial(ptlens, a=a, b=b, c=c, order=1)    
    
elif calib.Model == lensfun.DistortionModel.POLY3:
    k1, = calib.Terms
    rd = partial(poly3, k1=k1, order=0)
    rd1 = partial(poly3, k1=k1, order=1)
    
elif calib.Model == lensfun.DistortionModel.POLY5:
    k1, k2, = calib.Terms
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

fig, ax = drawLinePlot(X, 
                       [(rd(x/sensorHalfHeight)-x/sensorHalfHeight)/(x/sensorHalfHeight)*100 for x in X],
                       xlim=[0, sensorHalfDiagonal],
                       xlabel='$h\;(\mathrm{mm})$',
                       ylabel='distortion $D\;(\%)$',
                       )
saveFig(os.path.join(plotsPath, 'dist_relative_1d.svg'), fig)

fig, ax = drawLinePlot(X, 
                       [rd1(x/sensorHalfHeight)*sensorHalfHeight for x in X],
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

