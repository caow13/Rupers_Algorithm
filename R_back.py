import triangle
from triangle.plot import plot
from cgalgo import *
import numpy as np
import matplotlib.pyplot as plt
import time

class Ruper:
    def __init__(self, planar):
        self.vertices = []
        self.segments = {}
        self.segments_type = {}
        for vertex in planar['vertices']:
            self.vertices.append(vertex)
        for segment in planar['segments']:
            self.segments[tuple(sorted((segment[0], segment[1])))] = True
        for segment in planar['segments_type'].keys():
            self.segments_type[tuple(sorted((segment[0], segment[1])))] = planar['segments_type'][segment]

    def Triangulate(self):
        delaunay = triangle.triangulate({'vertices' : self.vertices})
        self.segments_vertices = {}
        self.vertices_segments = {}
        self.delaunay_triangles = {}

        for tri in delaunay['triangles']:
            for ind in range(3):
                a, b, c = tri[ind], tri[(ind + 1) % 3], tri[(ind + 2) % 3]
                self.InsertSegments_Vertices(a, b, c)
                self.InsertVertices_Segments(a, b, c)
        
        for tri in delaunay['triangles']:
            a, b, c = sorted((tri[0], tri[1], tri[2]))
            self.delaunay_triangles[(a, b, c)] = True

    def PointLocation(self, p):
        for tri in self.delaunay_triangles.keys():
            a, b, c = self.vertices[tri[0]], self.vertices[tri[1]], self.vertices[tri[2]]
            if InTriangle(p, a, b, c):
                return tri

    def AddTriangle(self, a, b, c):
        a, b, c = sorted((a, b, c))
        self.delaunay_triangles[(a, b, c)] = True
        tri = (a, b, c)
        for ind in range(3):
            a, b, c = tri[ind], tri[(ind + 1) % 3], tri[(ind + 2) % 3]
            self.InsertSegments_Vertices(a, b, c)
            self.InsertVertices_Segments(a, b, c)

    def DelTriangle(self, a, b, c):
        self.delaunay_triangles.pop(tuple(sorted((a, b, c))))
        tri = (a, b, c)
        for ind in range(3):
            a, b, c = tri[ind], tri[(ind + 1) % 3], tri[(ind + 2) % 3]
            self.RemoveSegments_Vertices(a, b, c)
            self.RemoveVertices_Segments(a, b, c)

    def RightSide(self, p, a, b):
        pair = tuple(sorted((a, b)))
        if self.segments_vertices.has_key(pair) == False or len(self.segments_vertices[pair]) == 0:
            return None
        for u in self.segments_vertices[pair].keys():
            if u != p:
                return u

    def STest(self, p, a, b):
        x = self.RightSide(p, a, b)
        if x == None:
            if sgn(cross(self.vertices[p], self.vertices[a], self.vertices[b])) == 0:
                self.DelTriangle(p, a, b)
            return
#        self.Show()
#        plt.plot(self.vertices[-1][0], self.vertices[-1][1], 'yo')
#        plt.plot(self.vertices[a][0], self.vertices[a][1], 'bo')
#        plt.plot(self.vertices[b][0], self.vertices[b][1], 'bo')
#        plt.plot(self.vertices[x][0], self.vertices[x][1], 'go')
#        plt.show()
#        plt.clf()
        if InCircle(self.vertices[p], self.vertices[a], self.vertices[b], self.vertices[x]):
            self.DelTriangle(p, a, b)
            self.DelTriangle(a, b, x)
            self.AddTriangle(p, a, x)
            self.AddTriangle(p, x, b)
            self.STest(p, a, x)
            self.STest(p, x, b)

    def SwapTest(self, p, a, b, c):
        self.STest(p, a, b)
        self.STest(p, b, c)
        self.STest(p, c, a)

    def UpdateTriangulate(self):
        p = len(self.vertices) - 1
        tri = self.PointLocation(self.vertices[p])
        a, b, c = tri[0], tri[1], tri[2]
        self.DelTriangle(a, b, c)
        self.AddTriangle(p, a, b)
        self.AddTriangle(p, b, c)
        self.AddTriangle(p, c, a)
        self.SwapTest(p, a, b, c)

    def InsertVertices_Segments(self, a, b, c):
        b, c = sorted((b, c))
        if self.vertices_segments.has_key(a) == False:
            self.vertices_segments[a] = {}
        self.vertices_segments[a][(b, c)] = True

    def InsertSegments_Vertices(self, a, b, c):
        a, b = sorted((a, b))
        if self.segments_vertices.has_key((a, b)) == False:
            self.segments_vertices[(a, b)] = {}
        self.segments_vertices[(a, b)][c] = True
        
    def RemoveVertices_Segments(self, a, b, c):
        b, c = sorted((b, c))
        self.vertices_segments[a].pop((b, c))

    def RemoveSegments_Vertices(self, a, b, c):
        a, b = sorted((a, b))
        self.segments_vertices[(a, b)].pop(c)

    def Show(self):
        planar = {'vertices' : np.array(self.vertices), 'segments' : np.array(self.segments.keys())}
        tri = {'vertices' : np.array(self.vertices), 'triangles' : np.array(self.delaunay_triangles.keys())}
        plot(plt.axes(), **planar)
        plot(plt.axes(), **tri)
        plt.show()
        plt.clf()

    def IsEncroached(self, segment):
        a, b = self.vertices[segment[0]], self.vertices[segment[1]]
        pair = tuple(sorted((segment[0], segment[1])))
        if self.segments_vertices.has_key(pair) == False or len(self.segments_vertices[pair]) == 0:
            return True
        mid = (a + b) / 2.0
        r = GetDistance(a, b) * 0.5
        for ind in self.segments_vertices[pair].keys():
            v = self.vertices[ind]
            if sgn(GetDistance(v, mid) - r) < 0:
                return True
        return False

    def SplitSegment(self, segment):
        a = self.vertices[segment[0]]
        b = self.vertices[segment[1]]
        mid = (a + b) / 2
        cnt = len(self.vertices)
        self.vertices.append(np.array(mid))
        self.segments.pop(tuple(sorted((segment[0], segment[1]))))
        self.segments[tuple(sorted((segment[0], cnt)))] = True
        self.segments[tuple(sorted((segment[1], cnt)))] = True
        seg_type = self.segments_type.pop(tuple(sorted((segment[0], segment[1]))))
        self.segments_type[tuple(sorted((segment[0], cnt)))] = seg_type
        self.segments_type[tuple(sorted((segment[1], cnt)))] = seg_type
        self.Show()

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
        change = True
        while change == True:
            change = False
            for ind, segment in enumerate(self.segments):
                if self.IsEncroached(segment) == True:
                    self.SplitSegment(segment)
                    self.delaunay = self.UpdateTriangulate()
                    change = True
                    eliminated = True
                    break

#    def EliminateAngle(self):
#        change = True
#        while change == True:
#            change = False
#            for tri in self.delaunay_triangles:
#                print tri
#                raw_input()
#                a, b, c = self.vertices[tri[0]], self.vertices[tri[1]], self.vertices[tri[2]]
#                if self.IsSkinny(a, b, c) == True:
#                    o = GetCircCenter(a, b, c)
#                    e = self.ConflictSegment(o)
#                    if e == None:
#                        self.InsertPoint(o)
#                        self.delaunay = self.Triangulate(True)
#                        self.EliminateSegment()
#                    else:
#                        self.SplitSegment(e[1], e[0])
#                        self.delaunay = self.Triangulate(True)
#                        self.EliminateSegment()
#                    change = True
#                    eliminated = True
#                    break
#
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
    
    def RemoveOutside(self):
        rmKeys = []
        for ind, tri in enumerate(self.delaunay_triangles):
            a, b, c = self.vertices[tri[0]], self.vertices[tri[1]], self.vertices[tri[2]]
            u = (a + b + c) / 3.0
            rmBool = False
            for delta in [-1e-9, 0, 1e-9]:
                v = np.array([1e5, u[1] + delta])
                count = self.CrossCount(u, v)
                if count != None and count % 2 == 0:
                    rmBool = True
            if rmBool == True:
                rmKeys.append(tuple(sorted((tri[0], tri[1], tri[2]))))
        for rm in rmKeys:
            self.delaunay_triangles.pop(rm)


                    

    def Start(self):
        self.Triangulate()
        self.EliminateSegment()
        self.RemoveOutside()
        self.Show()
#        self.RemoveOutside()
#        self.delaunay = self.Triangulate(rem = True)
#        self.EliminateAngle()


if __name__ == '__main__':
    planar = triangle.get_data('face') 
    planar['segments_type'] = {}
    for segment in planar['segments']:
        a, b = sorted((segment[0], segment[1]))
        planar['segments_type'][(a, b)] = 1
    ruper = Ruper(planar)
#    now = time.time()
    ruper.Start()
#    print time.time() - now
#    ruper.Show()
   
