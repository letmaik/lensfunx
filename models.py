import numpy as np

def ptlens(ru, a, b, c, order=0):
    if order == 0:
        return ru*(a*ru**3 + b*ru**2 + c*ru + 1 - a - b- c)
    else:
        return 3*a*ru**2 + 2*b*ru + c

def poly3(ru, k1, order=0):
    if order == 0:
        # on http://www.imatest.com/docs/distortion/ the formula is slightly
        # different: ru*(k1 + k1*ru**2) why? 
        return ru*(1 - k1 + k1*ru**2)
    else:
        return 2*k1*ru

def poly5(ru, k1, k2, order=0):
    if order == 0:
        return ru*(1 + k1*ru**2 + k2*ru**4)
    elif order == 1:
        return 2*k1*ru + 4*k2*ru**3