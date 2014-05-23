import triangle as triPackage
from triangle.plot import plot
import matplotlib.pyplot as plt
from cgalgo import *
import numpy as np
from collections import deque

class OperationSequence:
    def __init__(self, operation):
        #-1 - Initialization 0 - Add a mid point, 1 - Successfully add a circle center 2 - Unsuccessfully add a circle center 3 - RemoveOutside
        self.operation = operation
        self.flipSequence = []
        self.vertex = None
        self.segment = None
        self.encroachedS = []

    def SplitSegment(self, segment):
        self.segment = segment

    def AddVertex(self, vertex):
        self.vertex = vertex

    def AddEncroachedSegments(self, segmentList):
        self.encroachedS = segmentList

    def AddFlipSequence(self, flip):
        self.flipSequence.append(flip)

class Ruper:
    def __init__(self, vertices, segments, segmentsMark):
        self.vertices = []
        self.segments = {}
        self.segmentsMark = {}
        for vertex in vertices:
            self.AddVertex(vertex)
        for segment in segments:
            self.AddSegment(segment)
        for segmentMark in segmentsMark:
            self.AddSegmentMark(segmentMark[0], segmentMark[1])
        self.InitializeParameter()

    def InitializeParameter(self):
        self.stage = 0
        self.queueS = deque()
        self.queueT = deque()
        self.triangles = {}
        self.svRelation = {}
        self.vsRelation = {}
        self.checkedTriangles = []

    def InitializeDelaunay(self):
        delaunay = triPackage.triangulate({'vertices' : self.vertices}) #the usage of delaunay need pass the vertices
        for triangle in delaunay['triangles']:
            self.AddTriangle(triangle)
        return self.triangles

    def InitializeSegmentQueue(self):
        self.queueS.clear()
        for segment in self.segments:
            if self.IsEncroached(segment):
                self.queueS.append(segment)

    def BruteForcePointLocation(self, vp):
        for triangle in self.triangles:
            va, vb, vc = self.vertices[triangle[0]], self.vertices[triangle[1]], self.vertices[triangle[2]]
            if InTriangle(vp, va, vb, vc):
                return triangle

    def GetSegmentKey(self, segment):
        return tuple(sorted((segment[0], segment[1])))

    def GetTriangleKey(self, triangle):
        return tuple(sorted((triangle[0], triangle[1], triangle[2])))

    def InsertSV(self, segment, vertex):
        segmentKey = self.GetSegmentKey(segment)
        if self.svRelation.has_key(segmentKey) == False:
            self.svRelation[segmentKey] = {}
        self.svRelation[segmentKey][vertex] = True

    def InsertVS(self, vertex, segment):
        segmentKey = self.GetSegmentKey(segment)
        if self.vsRelation.has_key(vertex) == False:
            self.vsRelation[vertex] = {}
        self.vsRelation[vertex][segmentKey] = True

    def RemoveSV(self, segment, vertex):
        segmentKey = self.GetSegmentKey(segment)
        self.svRelation[segmentKey].pop(vertex)

    def RemoveVS(self, vertex, segment):
        segmentKey = self.GetSegmentKey(segment)
        self.vsRelation[vertex].pop(segmentKey)

    def AddVertex(self, vertex):
        self.vertices.append(np.array(vertex))

    def AddSegment(self, segment):
        self.segments[self.GetSegmentKey(segment)] = True

    def AddSegmentMark(self, segment, mark):
        self.segmentsMark[self.GetSegmentKey(segment)] = mark
    
    def AddTriangle(self, triangle):
        triangleKey = self.GetTriangleKey(triangle)
        self.triangles[triangleKey] = True        
        self.checkedTriangles.append((triangle, 1))
        for ind in range(3):
            a, b, c = triangle[ind], triangle[(ind + 1) % 3], triangle[(ind + 2) % 3]
            self.InsertSV((a, b), c)
            self.InsertVS(a, (b, c))

    def DelVertex(self, vertex):
        self.vertices.pop()

    def DelSegment(self, segment):
        self.segments.pop(self.GetSegmentKey(segment))

    def DelSegmentMark(self, segment):
        return self.segmentsMark.pop(self.GetSegmentKey(segment))

    def DelTriangle(self, triangle):
        triangleKey = self.GetTriangleKey(triangle)
        self.triangles.pop(triangleKey)
        self.checkedTriangles.append((triangle, -1))
        for ind in range(3):
            a, b, c = triangle[ind], triangle[(ind + 1) % 3], triangle[(ind + 2) % 3]
            self.RemoveSV((a, b), c)
            self.RemoveVS(a, (b, c))

    def IsEncroached(self, segment):
        segmentKey = self.GetSegmentKey(segment)
        if self.segments.has_key(segmentKey) == False:
            return False
        if self.svRelation.has_key(segmentKey) == False or len(self.svRelation[segmentKey]) == 0:
            return True
        va, vb = self.vertices[segment[0]], self.vertices[segment[1]]
        vm = (va + vb) * 0.5
        r = GetDistance(va, vb) * 0.5
        for ind in self.svRelation[segmentKey].keys():
            v = self.vertices[ind]
            if sgn(GetDistance(v, vm) - r) < 0:
                return True
        return False

    def RightSide(self, p, a, b):
        segmentKey = self.GetSegmentKey((a, b))
        if self.svRelation.has_key(segmentKey) == False or len(self.svRelation[segmentKey]) == 0:
            return None
        for v in self.svRelation[segmentKey].keys():
            if v != p:
                return v

    def STest(self, p, a, b):
        x = self.RightSide(p, a, b)
        vp, va, vb = self.vertices[p], self.vertices[a], self.vertices[b]
        if x == None:
            if sgn(cross(vp, va, vb)) == 0:
                self.DelTriangle((p, a, b))
            return
        vx = self.vertices[x]
        if InCircle(vp, va, vb, vx) == True:
            self.os.AddFlipSequence(((p, a, b, x), 1))
            self.DelTriangle((p, a, b))
            self.DelTriangle((a, b, x))
            self.AddTriangle((p, a, x))
            self.AddTriangle((p, x, b))
            self.STest(p, a, x)
            self.STest(p, x, b)
        else:
            self.os.AddFlipSequence(((p, a, b, x), 0))

    def SwapTest(self, p, a, b, c):
        self.STest(p, a, b)
        self.STest(p, b, c)
        self.STest(p, c, a)

    def UpdateDelaunay(self):
        self.checkedTriangles = []
        p = len(self.vertices) - 1
        triangle = self.BruteForcePointLocation(self.vertices[p])
        a, b, c = triangle[0], triangle[1], triangle[2]
        self.DelTriangle((a, b, c))
        self.AddTriangle((p, a, b))
        self.AddTriangle((p, b, c))
        self.AddTriangle((p, c, a))
        self.SwapTest(p, a, b, c)


    def GetEncroachedS(self, triangeList):
        encroachedS = []
        for triangle in triangeList:
            for ind in range(3):
                a, b = triangle[0][ind], triangle[0][(ind + 1) % 3]
                if self.IsEncroached((a, b)):
                    encroachedS.append((a, b))
        return encroachedS

    def SplitSegment(self, segment):
        va = self.vertices[segment[0]]
        vb = self.vertices[segment[1]]
        vm = (va + vb) * 0.5
        count = len(self.vertices)

        self.AddVertex(vm)

        self.os.AddVertex(vm)

        self.DelSegment(segment)
        self.AddSegment((segment[0], count))
        self.AddSegment((segment[1], count))

        self.os.SplitSegment(segment)

        segmentMark = self.DelSegmentMark(segment)
        self.AddSegmentMark((segment[0], count), segmentMark)
        self.AddSegmentMark((segment[1], count), segmentMark)
        self.UpdateDelaunay()

        encroachedS = self.GetEncroachedS(self.checkedTriangles)

        if self.IsEncroached((segment[0], count)) == True:
            encroachedS.append((segment[0], count))
        if self.IsEncroached((segment[1], count)) == True:
            encroachedS.append((segment[1], count))

        self.os.AddEncroachedSegments(encroachedS)

        for segment in encroachedS:
            self.queueS.append(segment)

    def EliminateSegment(self):
        while len(self.queueS) > 0:
            segment = self.queueS.popleft()
            if self.IsEncroached(segment):
                self.SplitSegment(segment)
                return True
        return False

    def NextStep(self):
        print 'proccessing stage %d' % self.stage
        if self.stage == 0:
            self.os = OperationSequence(-1)
            self.InitializeDelaunay()
            self.InitializeSegmentQueue()
            self.stage += 1        
        elif self.stage == 1:
            self.os = OperationSequence(0)
            if self.EliminateSegment() == False:
                self.stage += 1
        elif self.stage == 2:
            self.os = OperationSequence(
        return self.os
    
    def Show(self):
        planar = {'vertices' : np.array(self.vertices), 'segments' : np.array(self.segments.keys())}
        tri = {'vertices' : np.array(self.vertices), 'triangles' : np.array(self.triangles.keys())}
        plot(plt.axes(), **planar)
        plot(plt.axes(), **tri)
        plt.show()
        plt.clf()


if __name__ == '__main__':
    planar = triPackage.get_data('af2')
    vertices = []
    segments = []
    segmentsMark = []
    for vertex in planar['vertices']:
        vertices.append((vertex[0], vertex[1]))
    for segment in planar['segments']:
        segments.append((segment[0], segment[1]))
        segmentsMark.append(((segment[0], segment[1]), 1))
    ruper = Ruper(vertices, segments, segmentsMark)
    while ruper.stage != 2:
        os = ruper.NextStep()
    
