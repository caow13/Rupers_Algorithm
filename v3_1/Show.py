import triangle as triPackage
import numpy as np
from Ruper import Ruper

class Show:
    def Initialize(fileName):
        planar = triPackage.get_data(fileName)
        vertices = []
        segments = []
        segmentsMark = []
        for vertex in planar['vertices']:
            vertices.append((vertex[0], vertex[1]))
        for segment in planar['segments']:
            segments.append((segment[0], segment[1]))
            segmentsMark.append(((segment[0], segment[1]), 1))
        ruper = Ruper(vertices, segments, segmentsMark)

    def Show():
        ruper.InitializeParameter()
        ruper.InitializeDelaunay()

if __name__ == '__main__':
    show = Show()
    show.Initialize('A')
