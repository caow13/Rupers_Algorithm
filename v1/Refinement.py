import triangle
from triangle.plot import plot
from cgalgo import *
import numpy as np
import matplotlib.pyplot as plt
import time

class Ruper:
    def __init__(self, planar):
        self.vertices = planar['vertices']
        self.segments = planar['segments']
        self.segments_type = planar['segments_type']

    def Triangulate(self, rem = False):
        delaunay = triangle.triangulate({'vertices' : self.vertices})
        if rem == True:
            delaunay = self.RemoveOutside(delaunay)
        return delaunay

    def Show(self):
        tri = self.delaunay
        planar = {'vertices' : self.vertices, 'segments' : self.segments}
        plot(plt.axes(), **planar)
        plot(plt.axes(), **tri)
        plt.plot(self.vertices[-1][0], self.vertices[-1][1], 'bo')
        plt.show()
        plt.clf()

    def IsEncroached(self, segment):
        a, b = self.vertices[segment[0]], self.vertices[segment[1]]
        appear = False
        for trigle in self.delaunay['triangles']:
            if (segment[0] in trigle) and (segment[1] in trigle):
                appear = True
        if appear == False:
            return True
        mid = (a + b) / 2.0
        print mid
        r = GetDistance(a, b) * 0.5
        for v in self.vertices:
            if sgn(GetDistance(v, mid) - r) < 0:
                return True
        return False

    def SplitSegment(self, segment, ind):
        a = self.vertices[segment[0]]
        b = self.vertices[segment[1]]
        mid = (a + b) / 2
        cnt = len(self.vertices)
        self.vertices = np.vstack((self.vertices, np.array([mid])))
        self.segments = np.vstack((self.segments[:ind], self.segments[ind + 1:]))
        self.segments = np.vstack((self.segments, np.array([[segment[0], cnt], [segment[1], cnt]])))
        seg_type = self.segments_type.pop((segment[0], segment[1]))
        self.segments_type[(segment[0], cnt)] = seg_type
        self.segments_type[(segment[1], cnt)] = seg_type

    def IsSkinny(self, a, b, c):
        o = GetCircCenter(a, b, c)
        r = GetDistance(a, o)
        d = np.min((GetDistance(a, b), GetDistance(b, c), GetDistance(a, c)))
        if sgn(r / d -  np.sqrt(2)) > 0:
            return True
        return False

    def ConflictSegment(self, o):
        for ind, segment in enumerate(self.segments):
            a, b = self.vertices[segment[0]], self.vertices[segment[1]]
            mid = (a + b) / 2.0
            r = GetDistance(a, b) * 0.5
            if sgn(GetDistance(o, mid) - r) < 0:
                return ind, segment

    def InsertPoint(self, o):
        self.vertices = np.vstack((self.vertices, np.array([o])))

    def EliminateSegment(self):
        eliminated = False
        change = True
        while change == True:
            change = False
            for ind, segment in enumerate(self.segments):
                if segment[0] == 10 and segment[1] == 11:
                    if self.IsEncroached(segment) == True:
                        self.SplitSegment(segment, ind)
                        self.delaunay = self.Triangulate()
                        change = True
                        eliminated = True
                        break
        return eliminated

    def EliminateAngle(self):
        eliminated = False
        change = True
        while change == True:
            change = False
            self.Show()
            for triangle in self.delaunay['triangles']:
                a, b, c = self.vertices[triangle[0]], self.vertices[triangle[1]], self.vertices[triangle[2]]
                if self.IsSkinny(a, b, c) == True:
                    o = GetCircCenter(a, b, c)
                    e = self.ConflictSegment(o)
                    if e == None:
                        self.InsertPoint(o)
                        self.delaunay = self.Triangulate(True)
                    else:
                        self.SplitSegment(e[1], e[0])
                        self.delaunay = self.Triangulate(True)
                        self.EliminateSegment()
                    change = True
                    eliminated = True
                    break
        return eliminated

    def CrossCount(self, u, v):
        count = 0
        for segment in self.segments:
            a, b = self.vertices[segment[0]], self.vertices[segment[1]]
            state = GetSegIntersection(a, b, u, v)
            if state == None:
                return None
            if state == True:
                count += self.segments_type[(segment[0], segment[1])]
        return count
    
    def RemoveOutside(self, delaunay):
        rm = [0] * len(delaunay['triangles'])
        for ind, triangle in enumerate(delaunay['triangles']):
            a, b, c = self.vertices[triangle[0]], self.vertices[triangle[1]], self.vertices[triangle[2]]
            u = (a + b + c) / 3.0
            for delta in [-1e-9, 0, 1e-9]:
                v = np.array([1e5, u[1] + delta])
                count = self.CrossCount(u, v)
                if count != None and count % 2 == 0:
                    rm[ind] = 1
        ind = map(lambda x : x[0], filter(lambda x : x[1] == 0, list(enumerate(rm))))
        delaunay['triangles'] = delaunay['triangles'][ind]
        return delaunay

                    

    def Start(self):
        self.delaunay = self.Triangulate()
        self.EliminateSegment()
        self.delaunay = self.Triangulate(rem = True)
        self.EliminateAngle()


if __name__ == '__main__':
    planar = triangle.get_data('A')
    planar['segments_type'] = {}
    for segment in planar['segments']:
        planar['segments_type'][(segment[0], segment[1])] = 1
    ruper = Ruper(planar)
    ruper.Start()
    ruper.Show()
    
