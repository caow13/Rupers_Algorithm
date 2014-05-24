from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import triangle as triPackage
import numpy as np
import Ruper

def Scale(x, mid_x, span):
    return (x - mid_x) / span

class Show:
    def __init__(self, fileName):
        self.LoadData(fileName)
        self.os = None

    def LoadData(self, fileName):
        planar = triPackage.get_data(fileName)
        vertices = []
        segments = []
        segmentsMark = []
        for vertex in planar['vertices']:
            vertices.append((vertex[0], vertex[1]))
        for segment in planar['segments']:
            segments.append((segment[0], segment[1]))
            segmentsMark.append(((segment[0], segment[1]), 1))
        self.ruper = Ruper.Ruper(vertices, segments, segmentsMark)

    def Show(self):
        glutInit()
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
        glutInitWindowPosition(100, 100)
        glutInitWindowSize(400, 400)
        glutCreateWindow("Ruper")
        glutDisplayFunc(self.drawFunc)
        glutKeyboardFunc(self.KeyBoard)
        glutMainLoop()

    def KeyBoard(self, key, x, y):
        if key == 27:
            exit(0)
        else:
            if self.os == None:
                self.os = self.ruper.NextStep()
            else:
                if len(self.os.flipSequence) == 0:
                    self.encroachedS = self.os.encroachedS
                    glutPostRedisplay()
                else:
                    self.flip = self.os.flipSequence[0]
                    glutPostRedisplay()

    def drawFunc(self):
        max_x = reduce(lambda u, v : u if u[0] > v[0] else v, self.ruper.vertices)[0]
        min_x = reduce(lambda u, v : u if u[0] < v[0] else v, self.ruper.vertices)[0]
        max_y = reduce(lambda u, v : u if u[1] > v[1] else v, self.ruper.vertices)[1]
        min_y = reduce(lambda u, v : u if u[1] < v[1] else v, self.ruper.vertices)[1]
        mid_x = (max_x + min_x) * 0.5
        mid_y = (max_y + min_y) * 0.5
        span = 0.5 * np.max((max_x - min_x, max_y - min_y)) + 0.1
        glClear(GL_COLOR_BUFFER_BIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glPointSize(3)
        glColor3f(1.0, 1.0, 0.5)
        glBegin(GL_POINTS)
        for vertex in self.ruper.vertices:
            x = Scale(vertex[0], mid_x, span)
            y = Scale(vertex[1], mid_y, span)
            glVertex2f(x, y)
        glEnd()
        glColor3f(1.0, 0.0, 0.0)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        for segment in self.ruper.segments:
            for ind in range(2):
                x, y = Scale(self.ruper.vertices[segment[ind]][0], mid_x, span), Scale(self.ruper.vertices[segment[ind]][1], mid_y, span)
                glVertex2f(x, y)
        glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
        glLineWidth(1.0)
        glBegin(GL_TRIANGLES)
        glColor3f(0.0, 0.0, 0.0)
        for triangle in self.ruper.triangles:
            va, vb, vc = self.ruper.vertices[triangle[0]], self.ruper.vertices[triangle[1]], self.ruper.vertices[triangle[2]]
            glVertex2f(Scale(va[0], mid_x, span), Scale(va[1], mid_y, span))
            glVertex2f(Scale(vb[0], mid_x, span), Scale(vb[1], mid_y, span))
            glVertex2f(Scale(vc[0], mid_x, span), Scale(vc[1], mid_y, span))
        glEnd()
        if self.os != None and self.os.operation == 'split':
            if self.os.vertex == None:
                self.os = None
                return
            glPointSize(5)
            glColor3f(1.0, 0.0, 1.0)
            glBegin(GL_POINTS)
            x, y = self.os.vertex[0], self.os.vertex[1]
            glVertex2f(Scale(x, mid_x, span), Scale(y, mid_y, span))
            glEnd()
            if len(self.os.flipSequence) > 0:
                p, a, b, x = self.flip[0]
                vp, va, vb, vx = self.ruper.vertices[p], self.ruper.vertices[a], self.ruper.vertices[b], self.ruper.vertices[x]
                glColor3f(124.0 / 255.0, 252.0 / 255.0, 0.0)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
                glBegin(GL_TRIANGLES)
                glVertex2f(Scale(vp[0], mid_x, span), Scale(vp[1], mid_y, span))
                glVertex2f(Scale(va[0], mid_x, span), Scale(va[1], mid_y, span))
                glVertex2f(Scale(vb[0], mid_x, span), Scale(vb[1], mid_y, span))
                glEnd()
                glColor3f(0.0, 206.0 / 255.0 , 209.0 / 255.0)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
                glBegin(GL_TRIANGLES)
                glVertex2f(Scale(vx[0], mid_x, span), Scale(vx[1], mid_y, span))
                glVertex2f(Scale(va[0], mid_x, span), Scale(va[1], mid_y, span))
                glVertex2f(Scale(vb[0], mid_x, span), Scale(vb[1], mid_y, span))
                glEnd()
            else:
                print 'in'
                glColor3f(0.0, 255.0, 0.0)
                glLineWidth(3.0)
                glBegin(GL_LINES)
                for segment in self.encroachedS:
                    print segment
                    for ind in range(2):
                        x, y = Scale(self.ruper.vertices[segment[ind]][0], mid_x, span), Scale(self.ruper.vertices[segment[ind]][1], mid_y, span)
                        glVertex2f(x, y)
                glEnd()
                        
        if self.os != None:
            if len(self.os.flipSequence) > 0:
                self.os.flipSequence = self.os.flipSequence[1:]
            else:
                self.os = None
        
        glFlush()

if __name__ == '__main__':
    show = Show('layers')
    show.Show()
