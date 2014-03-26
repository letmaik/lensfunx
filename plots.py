from __future__ import division

from functools import partial
import os
from math import asin, sqrt, cos
import numpy as np
import numpy.ma as ma
import lensfun

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import brewer2mpl

blue_red = brewer2mpl.get_map('RdBu', 'Diverging', 11, reverse=True).mpl_colormap

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

def lensDistortionRelativeDistance2(mod):
    '''

    :rtype: ndarray of shape (h,w)
    '''
    distance, _, hUndist = lensDistortionDistance(mod, retH=True)
    hUndistCorner = sqrt(hUndist.shape[0]**2 + hUndist.shape[1]**2)/2
    distanceRelative = distance / hUndistCorner
    # TODO make this more clever
    distanceRelative[distanceRelative < -0.99] = np.nan
    distanceRelative[distanceRelative > 0.99] = np.nan

    return distanceRelative

def drawHeatmap(path, data):
    data = ma.masked_invalid(data, copy=False)
    fig, ax = plt.subplots()
    im = ax.imshow(data, cmap=blue_red)
    fig.colorbar(im)
    fig.savefig(path)
    plt.close(fig)
    
def drawLinePlot(x, y, xlim=None, ylim=None, xlabel=None, ylabel=None, grid=True):
    fig,ax = plt.subplots()
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.plot(x, y, color='black')
    if grid:
        ax.grid()
    return fig, ax

def saveFig(path, fig):
    fig.savefig(path)
    plt.close(fig)
    
def poly_between(x, ylower, yupper):
    """
    given a sequence of x, ylower and yupper, return the polygon that
    fills the regions between them.  ylower or yupper can be scalar or
    iterable.  If they are iterable, they must be equal in length to x

    return value is x, y arrays for use with Axes.fill
    """
    Nx = len(x)
    if not np.iterable(ylower):
        ylower = ylower*np.ones(Nx)

    if not np.iterable(yupper):
        yupper = yupper*np.ones(Nx)

    x = np.concatenate( (x, x[::-1]) )
    y = np.concatenate( (yupper, ylower[::-1]) )
    return x,y 
    
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
drawHeatmap(os.path.join(plotsPath, 'dist.svg'), dist)

distRel = lensDistortionRelativeDistance(mod)
drawHeatmap(os.path.join(plotsPath, 'dist_rel.svg'), distRel*100)

distRel2 = lensDistortionRelativeDistance2(mod)
drawHeatmap(os.path.join(plotsPath, 'dist_rel_corner.svg'), distRel2*100)

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
saveFig(os.path.join(plotsPath, 'dist_rel_2.svg'), fig)

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

saveFig(os.path.join(plotsPath, 'deriv.svg'), fig)
