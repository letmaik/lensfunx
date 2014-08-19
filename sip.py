from __future__ import division
from numpy.testing.utils import assert_almost_equal

# transform lensfun distortion terms into equivalent SIP distortion terms

# WARNING: THE BELOW CODE IS INCORRECT!! THE FORMULAS USED ARE FOR THE
#          OPPOSITE TRANSFORMATION DIRECTION!

def scale(w, h):
    return h/2 if h<w else w/2

def poly3(k1, w, h):
    s = scale(w, h)
    order = 3
    # f(u,v) = -k1*u + k1/s^2*u*v^2 + k1/s^2*u^3
    # g(u,v) = -k1*v + k1/s^2*u^2*v + k1/s^2*v^3
    return {'A_ORDER': order,
            'A_1_0': -k1,
            'A_1_2': k1/s**2,
            'A_3_0': k1/s**2,
            'B_ORDER': order,
            'B_0_1': -k1,
            'B_2_1': k1/s**2,
            'B_0_3': k1/s**2}
    
def poly5(k1, k2, w, h):
    s = scale(w, h)
    order = 5
    # f(u,v) = k1/s^2*u*v^2 + k1/s^2*u^3 + 2*k2/s^4*u^3*v^2 + k2/s^4*u*v^4 + k2/s^4*u^5
    # g(u,v) = k1/s^2*u^2*v + k1/s^2*v^3 + 2*k2/s^4*u^2*v^3 + k2/s^4*u^4*v + k2/s^4*v^5 
    sip = {'A_ORDER': order,
           'A_1_2': k1/s**2,
           'A_3_0': k1/s**2,
           'A_3_2': 2*k2/s**4,
           'A_1_4': k2/s**4,
           'A_5_0': k2/s**4}
    sip.update({'B_ORDER': order,
                'B_2_1': sip['A_1_2'],
                'B_0_3': sip['A_3_0'],
                'B_2_3': sip['A_3_2'],
                'B_4_1': sip['A_1_4'],
                'B_0_5': sip['A_5_0']})
    return sip

def ptlens(a, b, c, w, h):
    # FIXME formula doesn't contain scaling factors yet
    # f(u, v) = - a*u*v^2*sqrt(u^2+v^2) - a*u^3*sqrt(u^2+v^2)
    #           - b*u^3 - b*u*v^2 - c*u*sqrt(u^2+v^2) + a*u + b*u + c*u
    assert a == c == 0, 'SIP only supports the case of a=c=0'
    return poly3(b, w, h)

    # FIXME is ptlens really incompatible to SIP if a or c is not 0??


def testPoly3():
    w = 4256
    h = 2832
    k1 = 0.0124
    sip = poly3(k1, w, h)
        
    def _poly3(x, y):
        s = scale(w, h)
        xn, yn = x/s, y/s
        f = 1 - k1 + k1*(xn*xn+yn*yn)
        return f*xn*s, f*yn*s
    
    def _sip(x, y):
        def f(x, y):
            return sip['A_1_0']*x + sip['A_1_2']*x*y**2 + sip['A_3_0']*x**3
        def g(x, y):
            return sip['B_0_1']*y + sip['B_2_1']*x**2*y + sip['B_0_3']*y**3
        return x + f(x, y), (y + g(x, y))
    
    dX, dY = 1000, 900 # sample distorted location, from image center
    assert_almost_equal(_sip(dX, dY), _poly3(dX, dY))
    
def testPoly5():
    w = 4256
    h = 2832
    k1 = 0.0124
    k2 = -0.053
    sip = poly5(k1, k2, w, h)
    
    def _poly5(x, y):
        s = scale(w, h)
        xn, yn = x/s, y/s
        f = 1 + k1*(xn*xn+yn*yn) + k2*(xn*xn+yn*yn)**2
        return f*xn*s, f*yn*s
    
    def _sip(x, y):
        def f(x, y):
            return sip['A_1_2']*x*y**2 + sip['A_3_0']*x**3 + sip['A_3_2']*x**3*y**2 + sip['A_1_4']*x*y**4 + sip['A_5_0']*x**5
        def g(x, y):
            return sip['B_2_1']*x**2*y + sip['B_0_3']*y**3 + sip['B_2_3']*x**2*y**3 + sip['B_4_1']*x**4*y + sip['B_0_5']*y**5
        return x + f(x, y), y + g(x, y)
        
    dX, dY = 1000, 900 # sample distorted location, from image center
    assert_almost_equal(_sip(dX, dY), _poly5(dX, dY))
    
if __name__ == '__main__':
    testPoly3()
    testPoly5()
    