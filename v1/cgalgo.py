import numpy as np

eps = 1e-12

def sgn(x):
    return np.int(x > eps) - np.int(x < -eps)

def TurnLeft(v):
    return -v[1], v[0]

def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])

def GetDistance(u, v):
    return np.sqrt(np.dot((u - v).T, (u - v)))

def GetIntersection(lu, lv):
    a, b, c, d = lu[0], lu[1], lv[0], lv[1]
    s1 = cross(a, b, c)
    s2 = cross(a, b, d)
    if sgn(s1 - s2) == 0:
        return None
    return c + (d - c) * s1 / (s1 - s2)

def GetBisector(u, v):
    return (u + v) / 2, (u + v) / 2 + TurnLeft(u - v)

def GetCircCenter(a, b, c):
    return GetIntersection(GetBisector(a, b), GetBisector(b, c))

def GetSegIntersection(a, b, c, d):
    d1, d2, d3, d4 = sgn(cross(a, b, c)), sgn(cross(a, b, d)), sgn(cross(d, c, a)), sgn(cross(d, c, b))
    if d1 == 0 or d2 == 0 or d3 == 0 or d4 == 0:
        return None
    if d1 * d2 < 0 and d3 * d4 < 0:
        return True
    return False

