from __future__ import division

import numpy as np
import numpy.ma as ma

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import brewer2mpl

blue_red = brewer2mpl.get_map('RdBu', 'Diverging', 11, reverse=True).mpl_colormap

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