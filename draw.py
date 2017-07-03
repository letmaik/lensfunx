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
    