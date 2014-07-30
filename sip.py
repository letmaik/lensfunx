from __future__ import division

# transform lensfun distortion terms into equivalent SIP distortion terms

def scale(w, h):
    return h/2 if h<w else w/2

def scaled(w, h, *px):
    s = scale(w, h)
    return [p*s for p in px]
    
def poly3(k1, w, h):
    # f(u,v) = k1*u - k1*u*v^2 - k1*u^3
    # g(u,v) = k1*v - k1*u^2*v - k1*v^3
    k1 = scaled(w, h, k1)[0]
    order = 3
    return {'A_ORDER': order,
            'A_1_0': k1,
            'A_1_2': -k1,
            'A_3_0': -k1,
            'B_ORDER': order,
            'B_0_1': k1,
            'B_2_1': -k1,
            'B_0_3': -k1}
    
def poly5(k1, k2, w, h):
    # f(u,v) = -k1*u*v^2 - k1*u^3 - 2*k1*u^3*v^2 - k2*u*v^4 - k2*u^5
    # g(u,v) = -k1*u^2*v - k1*v^3 - 2*k1*u^2*v^3 - k2*u^4*v - k2*v^5 
    k1, k2 = scaled(w, h, k1, k2)
    order = 5
    sip = {'A_ORDER': order,
           'A_1_2': -k1,
           'A_3_0': -k1,
           'A_3_2': -2*k1,
           'A_1_4': -k2,
           'A_5_0': -k2}
    sip.update({'B_ORDER': order,
                'B_2_1': sip['A_1_2'],
                'B_0_3': sip['A_3_0'],
                'B_2_3': sip['A_3_2'],
                'B_4_1': sip['A_1_4'],
                'B_0_5': sip['A_5_0']})
    return sip

def ptlens(a, b, c, w, h):
    # f(u, v) = - a*u*v^2*sqrt(u^2+v^2) - a*u^3*sqrt(u^2+v^2)
    #           - b*u^3 - b*u*v^2 - c*u*sqrt(u^2+v^2) + a*u + b*u + c*u
    assert a == c == 0, 'SIP only supports the case of a=c=0'
    return poly3(b, w, h)

    # FIXME is ptlens really incompatible to SIP if a or c is not 0??
    