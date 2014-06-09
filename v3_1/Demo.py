from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *
from OpenGL.GL import *
import numpy
import threading
import time
import math
import copy

from Ruper import *
from Generate import *

class DisplayWidget(QGLWidget):
    ANIMATION_ROUNDS = 40
    ANIMATION_ROUNDS_HALF = ANIMATION_ROUNDS / 2
    ANIMATION_ROUNDS_QUARTER = ANIMATION_ROUNDS / 4
    ANIMATION_TIME = 0.1
    
    TRIANGLE_COLOR_VALUE = 0.3
    SEGMENT_COLOR = [0.0, 0.0, 1.0, 1.0]
    EDGE_COLOR = [1.0, 1.0, 1.0, 1.0]
    POINT_COLOR = [1.0, 0.0, 0.0, 1.0]
    HIGHLIGHT_POINT_COLOR = POINT_COLOR
    HIGHLIGHT_SEGMENT_COLOR = EDGE_COLOR
    ENCROACHED_SEGMENT_COLOR = [0.0, 1.0, 1.0, 1.0]

    FILL_SCREEN_RATIO = 0.8

    POINT_SIZE = 10.0
    SEGMENT_LINE_WIDTH = 7.0
    EDGE_LINE_WIDTH = 1.0
    MAX_POINT_SIZE = 30.0
    MAX_LINE_WIDTH = 30.0

    def __init__(self, parent):
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(500, 500)

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.tmp_offset_x = 0.0
        self.tmp_offset_y = 0.0
        self.scale = 1.0

        self.data_lock = threading.RLock()
        self.vertices = None
        self.segments = None
        self.triangles = None
        self.round = -1

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, """
#version 120
attribute vec2 position;
uniform float w, h, scale, offset_x, offset_y;
void main()
{
    float x, y;
    if (w > h) {
        x = (position.x + offset_x) * scale * h / w;
        y = (position.y + offset_y) * scale;
    } else {
        x = (position.x + offset_x) * scale;
        y = (position.y + offset_y) * scale * w / h;
    }
    gl_Position = vec4(x, y, 0., 1.);
}
""")
        glCompileShader(vs)
        result = glGetShaderiv(vs, GL_COMPILE_STATUS)
        if not(result):
            raise RuntimeError(glGetShaderInfoLog(vs))

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, """
#version 120
uniform vec4 color;
void main()
{
    gl_FragColor = color;
}
""")
        glCompileShader(fs)
        result = glGetShaderiv(fs, GL_COMPILE_STATUS)
        if not(result):
            raise RuntimeError(glGetShaderInfoLog(fs))

        self.program = glCreateProgram()
        glAttachShader(self.program, vs)
        glAttachShader(self.program, fs)
        glLinkProgram(self.program)
        result = glGetProgramiv(self.program, GL_LINK_STATUS)
        if not(result):
            raise RuntimeError(glGetProgramInfoLog(self.program))

        self.attrib = glGetAttribLocation(self.program, "position")
        self.uniform_scale = glGetUniformLocation(self.program, "scale")
        self.uniform_offset_x = glGetUniformLocation(self.program, "offset_x")
        self.uniform_offset_y = glGetUniformLocation(self.program, "offset_y")
        self.uniform_w = glGetUniformLocation(self.program, "w")
        self.uniform_h = glGetUniformLocation(self.program, "h")
        self.uniform_color = glGetUniformLocation(self.program, "color")

        self.vbo = glGenBuffers(1)
        self.vbo2 = glGenBuffers(1)
        self.vbo3 = glGenBuffers(1)
        self.vbo4 = glGenBuffers(1)

        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

        self.w = w
        self.h = h

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Fill with black
        glClearColor(0.0, 0.0, 0.0, 1.0)

        if self.vertices != None:
            glUseProgram(self.program)

            glUniform1f(self.uniform_scale, self.scale)
            glUniform1f(self.uniform_w, self.w)
            glUniform1f(self.uniform_h, self.h)
            glUniform1f(self.uniform_offset_x, self.offset_x + self.tmp_offset_x)
            glUniform1f(self.uniform_offset_y, self.offset_y + self.tmp_offset_y)

            # Common data: vertices
            data = np.array(self.vertices, dtype='float32')
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, 8 * len(data), data, GL_STATIC_DRAW)
            glEnableVertexAttribArray(self.attrib)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

            # Triangles
            glUniform4f(self.uniform_color, DisplayWidget.TRIANGLE_COLOR_VALUE, DisplayWidget.TRIANGLE_COLOR_VALUE, DisplayWidget.TRIANGLE_COLOR_VALUE, 1.0)
            data4 = np.array(self.triangles.keys(), dtype='uint32')
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo4)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, 12 * len(data4), data4, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo4)
            glDrawElements(GL_TRIANGLES, 3 * len(data4), GL_UNSIGNED_INT, None)

            # Segments
            glLineWidth(DisplayWidget.SEGMENT_LINE_WIDTH)
            glUniform4fv(self.uniform_color, 1, DisplayWidget.SEGMENT_COLOR)
            data2 = np.array(self.segments.keys(), dtype='uint32')
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo2)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, 8 * len(data2), data2, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo2)
            glDrawElements(GL_LINES, 2 * len(data2), GL_UNSIGNED_INT, None)

            # Triangle edges
            glLineWidth(DisplayWidget.EDGE_LINE_WIDTH)
            glUniform4fv(self.uniform_color, 1, DisplayWidget.EDGE_COLOR)
            data3 = np.zeros((3 * len(self.triangles.keys()), 2), dtype='uint32')
            i = 0
            for t in self.triangles.keys():
                data3[3 * i][0] = t[0]
                data3[3 * i][1] = t[1]
                data3[3 * i + 1][0] = t[1]
                data3[3 * i + 1][1] = t[2]
                data3[3 * i + 2][0] = t[2]
                data3[3 * i + 2][1] = t[0]
                i = i + 1
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, 8 * len(data3), data3, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
            glDrawElements(GL_LINES, 2 * len(data3), GL_UNSIGNED_INT, None)

            # Points
            glPointSize(DisplayWidget.POINT_SIZE)
            glUniform4fv(self.uniform_color, 1, DisplayWidget.POINT_COLOR)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glDrawArrays(GL_POINTS, 0, len(data))

            if self.round != -1:
                if self.round < DisplayWidget.ANIMATION_ROUNDS:
                    if self.stepType == 2:
                        # Highlight segment
                        lw = DisplayWidget.MAX_LINE_WIDTH / DisplayWidget.ANIMATION_ROUNDS_QUARTER * (DisplayWidget.ANIMATION_ROUNDS_QUARTER - abs(DisplayWidget.ANIMATION_ROUNDS_QUARTER - (self.round % DisplayWidget.ANIMATION_ROUNDS_HALF)))
                        if lw == 0.0:
                            lw = 1.0
                        glLineWidth(lw)
                        glUniform4fv(self.uniform_color, 1, DisplayWidget.HIGHLIGHT_SEGMENT_COLOR)
                        data5 = np.zeros((1, 2), dtype='uint32')
                        data5[0][0] = self.step2Segment[0]
                        data5[0][1] = self.step2Segment[1]
                        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 8 * len(data5), data5, GL_STATIC_DRAW)
                        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                        glDrawElements(GL_LINES, 2 * len(data5), GL_UNSIGNED_INT, None)

                        # Highlight point
                        ps = DisplayWidget.MAX_POINT_SIZE / DisplayWidget.ANIMATION_ROUNDS_QUARTER * (DisplayWidget.ANIMATION_ROUNDS_QUARTER - abs(DisplayWidget.ANIMATION_ROUNDS_QUARTER - (self.round % DisplayWidget.ANIMATION_ROUNDS_HALF)))
                        if ps == 0.0:
                            ps = 1.0
                        glPointSize(ps)
                        glUniform4fv(self.uniform_color, 1, DisplayWidget.HIGHLIGHT_POINT_COLOR)
                        data6 = np.zeros((1, 2), dtype='float32')
                        data6[0][0] = self.step2Vertex[0]
                        data6[0][1] = self.step2Vertex[1]
                        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                        glBufferData(GL_ARRAY_BUFFER, 8 * len(data6), data6, GL_STATIC_DRAW)
                        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                        glDrawArrays(GL_POINTS, 0, len(data6))

                        if self.round == DisplayWidget.ANIMATION_ROUNDS - 1:
                            # Add point, 2 segments, 3 triangles
                            # Delete segment, triangle
                            self.vertices.append(self.step2Vertex)
                            self.segments[Ruper.GetSegmentKey(self.step2AddedSegments[0])] = True
                            self.segments[Ruper.GetSegmentKey(self.step2AddedSegments[1])] = True
                            self.triangles[Ruper.GetTriangleKey(self.step2AddedTriangles[0])] = True
                            self.triangles[Ruper.GetTriangleKey(self.step2AddedTriangles[1])] = True
                            self.triangles[Ruper.GetTriangleKey(self.step2AddedTriangles[2])] = True
                            del self.segments[Ruper.GetSegmentKey(self.step2Segment)]
                            del self.triangles[Ruper.GetTriangleKey(self.step2DeletedTriangle)]
                    else:
                        # Highlight triangle
                        gray = DisplayWidget.TRIANGLE_COLOR_VALUE + (1.0 - DisplayWidget.TRIANGLE_COLOR_VALUE) / DisplayWidget.ANIMATION_ROUNDS_QUARTER * (DisplayWidget.ANIMATION_ROUNDS_QUARTER - abs(DisplayWidget.ANIMATION_ROUNDS_QUARTER - (self.round % DisplayWidget.ANIMATION_ROUNDS_HALF)))
                        glUniform4f(self.uniform_color, gray, gray, gray, 1.0)
                        data5 = np.array(self.step4Triangle, dtype='uint32')
                        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 4 * len(data5), data5, GL_STATIC_DRAW)
                        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                        glDrawElements(GL_TRIANGLES, len(data5), GL_UNSIGNED_INT, None)

                        # Highlight new point
                        ps = DisplayWidget.MAX_POINT_SIZE / DisplayWidget.ANIMATION_ROUNDS_QUARTER * (DisplayWidget.ANIMATION_ROUNDS_QUARTER - abs(DisplayWidget.ANIMATION_ROUNDS_QUARTER - (self.round % DisplayWidget.ANIMATION_ROUNDS_HALF)))
                        if ps == 0.0:
                            ps = 1.0
                        glPointSize(ps)
                        glUniform4fv(self.uniform_color, 1, DisplayWidget.HIGHLIGHT_POINT_COLOR)
                        data6 = np.zeros((1, 2), dtype='float32')
                        data6[0][0] = self.step4Vertex[0]
                        data6[0][1] = self.step4Vertex[1]
                        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                        glBufferData(GL_ARRAY_BUFFER, 8 * len(data6), data6, GL_STATIC_DRAW)
                        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
                        glDrawArrays(GL_POINTS, 0, len(data6))

                        if self.round == DisplayWidget.ANIMATION_ROUNDS - 1:
                            # Add point, 3 triangles
                            # Delete triangle
                            self.vertices.append(self.step4Vertex)
                            self.triangles[Ruper.GetTriangleKey(self.step4AddedTriangles[0])] = True
                            self.triangles[Ruper.GetTriangleKey(self.step4AddedTriangles[1])] = True
                            self.triangles[Ruper.GetTriangleKey(self.step4AddedTriangles[2])] = True
                            del self.triangles[Ruper.GetTriangleKey(self.step4DeletedTriangle)]
                elif self.round < DisplayWidget.ANIMATION_ROUNDS * (1 + len(self.FlipSequence)):
                    # Highlight flip sequence
                    flip_seq_id = self.round / DisplayWidget.ANIMATION_ROUNDS - 1

                    # 4 points
                    ps = DisplayWidget.MAX_POINT_SIZE / DisplayWidget.ANIMATION_ROUNDS_QUARTER * (DisplayWidget.ANIMATION_ROUNDS_QUARTER - abs(DisplayWidget.ANIMATION_ROUNDS_QUARTER - (self.round % DisplayWidget.ANIMATION_ROUNDS_HALF)))
                    if ps == 0.0:
                        ps = 1.0
                    glPointSize(ps)
                    glUniform4fv(self.uniform_color, 1, DisplayWidget.HIGHLIGHT_POINT_COLOR)
                    data6 = np.array(self.FlipSequence[flip_seq_id][0], dtype='uint32')
                    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                    glBufferData(GL_ELEMENT_ARRAY_BUFFER, 8 * len(data6), data6, GL_STATIC_DRAW)
                    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                    glDrawElements(GL_POINTS, len(data6), GL_UNSIGNED_INT, None)

                    # Edge flipped?
                    lw = DisplayWidget.MAX_LINE_WIDTH / DisplayWidget.ANIMATION_ROUNDS_QUARTER * (DisplayWidget.ANIMATION_ROUNDS_QUARTER - abs(DisplayWidget.ANIMATION_ROUNDS_QUARTER - (self.round % DisplayWidget.ANIMATION_ROUNDS_HALF)))
                    if lw == 0.0:
                        lw = 1.0
                    glLineWidth(lw)
                    glUniform4fv(self.uniform_color, 1, DisplayWidget.HIGHLIGHT_SEGMENT_COLOR)
                    data5 = np.zeros((1, 2), dtype='uint32')
                    if self.FlipSequence[flip_seq_id][1] == 0 or self.round % DisplayWidget.ANIMATION_ROUNDS < DisplayWidget.ANIMATION_ROUNDS_HALF:
                        data5[0][0] = self.FlipSequence[flip_seq_id][0][1]
                        data5[0][1] = self.FlipSequence[flip_seq_id][0][2]
                    else:
                        data5[0][0] = self.FlipSequence[flip_seq_id][0][0]
                        data5[0][1] = self.FlipSequence[flip_seq_id][0][3]
                    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                    glBufferData(GL_ELEMENT_ARRAY_BUFFER, 8 * len(data5), data5, GL_STATIC_DRAW)
                    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo3)
                    glDrawElements(GL_LINES, 2 * len(data5), GL_UNSIGNED_INT, None)

                    if self.round % DisplayWidget.ANIMATION_ROUNDS == DisplayWidget.ANIMATION_ROUNDS_HALF:
                        if self.FlipSequence[flip_seq_id][1] != 0:
                            points = self.FlipSequence[flip_seq_id][0]
                            del self.triangles[Ruper.GetTriangleKey((points[0], points[1], points[2]))]
                            del self.triangles[Ruper.GetTriangleKey((points[1], points[2], points[3]))]
                            self.triangles[Ruper.GetTriangleKey((points[0], points[1], points[3]))] = True
                            self.triangles[Ruper.GetTriangleKey((points[0], points[2], points[3]))] = True
                else:
                    # Highlight encroached segments
                    lw = DisplayWidget.MAX_LINE_WIDTH / DisplayWidget.ANIMATION_ROUNDS_QUARTER * (DisplayWidget.ANIMATION_ROUNDS_QUARTER - abs(DisplayWidget.ANIMATION_ROUNDS_QUARTER - (self.round % DisplayWidget.ANIMATION_ROUNDS_HALF)))
                    if lw == 0.0:
                        lw = 1.0
                    glLineWidth(lw)
                    glUniform4fv(self.uniform_color, 1, DisplayWidget.ENCROACHED_SEGMENT_COLOR)
                    data2 = np.array(self.EncroachedSegments, dtype='uint32')
                    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo2)
                    glBufferData(GL_ELEMENT_ARRAY_BUFFER, 8 * len(data2), data2, GL_STATIC_DRAW)
                    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo2)
                    glDrawElements(GL_LINES, 2 * len(data2), GL_UNSIGNED_INT, None)

    def updateStep2Single(self, step2Vertex, step2Segment, step2AddedSegments, step2DeletedTriangle, step2AddedTriangles, EncroachedSegments, FlipSequence, vertices, segments, triangles):
        self.stepType = 2
        self.step2Vertex = step2Vertex
        self.step2Segment = step2Segment
        self.step2AddedSegments = step2AddedSegments
        self.step2DeletedTriangle = step2DeletedTriangle
        self.step2AddedTriangles = step2AddedTriangles
        self.EncroachedSegments = EncroachedSegments
        self.FlipSequence = FlipSequence
        thread = threading.Thread(target=self.updateStep2SingleThread, args=(vertices, segments, triangles, self.parent()))
        thread.start()
    def updateStep2SingleThread(self, vertices, segments, triangles, widget):
        rounds = 1 + len(self.FlipSequence)
        if len(self.EncroachedSegments) > 0:
            rounds = rounds + 1
        for self.round in range(0, DisplayWidget.ANIMATION_ROUNDS * rounds):
            self.update()
            time.sleep(DisplayWidget.ANIMATION_TIME)
        self.round = -1
        self.setData(vertices, segments, triangles)
        self.update()

        widget.animationEnd()

    def updateStep4Single(self, step4Vertex, step4Triangle, step4DeletedTriangle, step4AddedTriangles, EncroachedSegments, FlipSequence, vertices, segments, triangles):
        self.stepType = 4
        self.step4Vertex = step4Vertex
        self.step4Triangle = step4Triangle
        self.step4DeletedTriangle = step4DeletedTriangle
        self.step4AddedTriangles = step4AddedTriangles
        self.EncroachedSegments = EncroachedSegments
        self.FlipSequence = FlipSequence
        thread = threading.Thread(target=self.updateStep4SingleThread, args=(vertices, segments, triangles, self.parent()))
        thread.start()
    def updateStep4SingleThread(self, vertices, segments, triangles, widget):
        rounds = 1 + len(self.FlipSequence)
        if len(self.EncroachedSegments) > 0:
            rounds = rounds + 1
        for self.round in range(0, DisplayWidget.ANIMATION_ROUNDS * rounds):
            self.update()
            time.sleep(DisplayWidget.ANIMATION_TIME)
        self.round = -1
        self.setData(vertices, segments, triangles)
        self.update()

        widget.animationEnd()

    def wheelEvent(self, event):
        self.scale *= math.exp(0.0 - float(event.angleDelta().y()) / 400.0)

        self.update()

    def mousePressEvent(self, event):
        self.start_x = event.x()
        self.start_y = event.y()

    def mouseMoveEvent(self, event):
        delta_x = event.x() - self.start_x
        delta_y = event.y() - self.start_y

        if self.w < self.h:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.w / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.w / self.scale
        else:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.h / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.h / self.scale

        self.update()

    def mouseReleaseEvent(self, event):
        delta_x = event.x() - self.start_x
        delta_y = event.y() - self.start_y

        if self.w < self.h:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.w / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.w / self.scale
        else:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.h / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.h / self.scale

        self.offset_x += self.tmp_offset_x
        self.offset_y += self.tmp_offset_y
        self.tmp_offset_x = 0.0
        self.tmp_offset_y = 0.0

        self.update()

    def setData(self, vertices, segments, triangles):
        self.data_lock.acquire()

        if vertices == None:
            self.vertices = None
        else:
            self.vertices = copy.deepcopy(vertices)
        if segments == None:
            self.segments = None
        else:
            self.segments = copy.deepcopy(segments)
        if triangles == None:
            self.triangles = None
        else:
            self.triangles = copy.deepcopy(triangles)

        self.data_lock.release()

    def autoWrap(self):
        if len(self.vertices) == 0:
            return

        x_min = self.vertices[0][0]
        x_max = self.vertices[0][0]
        y_min = self.vertices[0][1]
        y_max = self.vertices[0][1]
        for vertex in self.vertices:
            if vertex[0] < x_min:
                x_min = vertex[0]
            elif vertex[0] > x_max:
                x_max = vertex[0]
            if vertex[1] < y_min:
                y_min = vertex[1]
            elif vertex[1] > y_max:
                y_max = vertex[1]

        self.offset_x = 0.0 - (x_min + x_max) / 2
        self.tmp_offset_x = 0.0
        self.offset_y = 0.0 - (y_min + y_max) / 2
        self.tmp_offset_y = 0.0
        self.scale = 2.0 * DisplayWidget.FILL_SCREEN_RATIO / max(x_max - x_min, y_max - y_min)

class Form(QWidget):
    STATE_INIT = 0
    STATE_LOADED = 1
    STATE_STEP1_DONE = 2
    STATE_STEP2_DONE = 3
    STATE_STEP3_DONE = 4
    STATE_STEP4_DONE = 5

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.buttonGenerate = QPushButton("Create new model")
        self.buttonGenerate.clicked.connect(self.generate)
        self.buttonReset = QPushButton("Reset")
        self.buttonReset.clicked.connect(self.reset)
        self.lineeditModelname = QLineEdit(self)
        self.buttonLoad = QPushButton("Load from file")
        self.buttonLoad.clicked.connect(self.load)
        self.buttonStep1 = QPushButton("Step1")
        self.buttonStep1.clicked.connect(self.step1)
        self.buttonStep2Single = QPushButton("Step2 Single")
        self.buttonStep2Single.clicked.connect(self.step2Single)
        self.buttonStep2 = QPushButton("Step2")
        self.buttonStep2.clicked.connect(self.step2)
        self.buttonStep3 = QPushButton("Step3")
        self.buttonStep3.clicked.connect(self.step3)
        self.buttonStep4 = QPushButton("Step4")
        self.buttonStep4.clicked.connect(self.step4)
        self.buttonStep4Single = QPushButton("Step4 Single")
        self.buttonStep4Single.clicked.connect(self.step4Single)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.buttonGenerate)
        buttonLayout.addWidget(self.buttonReset)
        buttonLayout.addWidget(QLabel('Model name:'))
        buttonLayout.addWidget(self.lineeditModelname)
        buttonLayout.addWidget(self.buttonLoad)
        buttonLayout.addWidget(self.buttonStep1)
        buttonLayout.addWidget(self.buttonStep2Single)
        buttonLayout.addWidget(self.buttonStep2)
        buttonLayout.addWidget(self.buttonStep3)
        buttonLayout.addWidget(self.buttonStep4Single)
        buttonLayout.addWidget(self.buttonStep4)

        self.displayWidget = DisplayWidget(self)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(self.displayWidget)

        self.setLayout(mainLayout)
        self.setWindowTitle("Demo")

        self.in_animation = False
        self.setState(Form.STATE_INIT)

    def animationEnd(self):
        self.in_animation = False
        self.setState(self.state)
        self.update()

    def setState(self, state):
        self.state = state
        if self.in_animation:
            self.buttonGenerate.setEnabled(False)
            self.buttonReset.setEnabled(False)
            self.buttonLoad.setEnabled(False)
            self.buttonStep1.setEnabled(False)
            self.buttonStep2.setEnabled(False)
            self.buttonStep2Single.setEnabled(False)
            self.buttonStep3.setEnabled(False)
            self.buttonStep4.setEnabled(False)
            self.buttonStep4Single.setEnabled(False)
        else:
            self.buttonGenerate.setEnabled(True)
            self.buttonReset.setEnabled(True)
            self.buttonLoad.setEnabled(state == Form.STATE_INIT)
            self.buttonStep1.setEnabled(state == Form.STATE_LOADED)
            self.buttonStep2.setEnabled(state == Form.STATE_STEP1_DONE)
            self.buttonStep2Single.setEnabled(state == Form.STATE_STEP1_DONE)
            self.buttonStep3.setEnabled(state == Form.STATE_STEP2_DONE)
            self.buttonStep4.setEnabled(state == Form.STATE_STEP3_DONE)
            self.buttonStep4Single.setEnabled(state == Form.STATE_STEP3_DONE)

    def generate(self):
        self.form2 = Form2()
        self.form2.show()

    def reset(self):
        self.ruper = None

        self.displayWidget.setData(None, None, None)
        self.displayWidget.update()

        self.setState(Form.STATE_INIT)

    def load(self):
        planar = triPackage.load('.', self.lineeditModelname.text())
        vertices = []
        segments = []
        segmentsMark = []
        for vertex in planar['vertices']:
            vertices.append((vertex[0], vertex[1]))
        for segment in planar['segments']:
            segments.append((segment[0], segment[1]))
            segmentsMark.append(((segment[0], segment[1]), 1))
        self.ruper = Ruper(vertices, segments, segmentsMark)

        self.displayWidget.setData(self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
        self.displayWidget.autoWrap()
        self.displayWidget.update()

        self.setState(Form.STATE_LOADED)

        self.update()

    def step1(self):
        while self.ruper.stage != 1:
            self.ruper.NextStep()

        self.displayWidget.setData(self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
        self.displayWidget.update()

        self.setState(Form.STATE_STEP1_DONE)

    def step2Single(self):
        result = self.ruper.NextStep()

        if result != None:
            self.displayWidget.updateStep2Single(result.vertex, result.segment, result.addedSegments, result.deletedTriangle, result.addedTriangles, result.encroachedS, result.flipSequence, self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
        
        self.in_animation = True
        if self.ruper.stage == 2:   
            self.setState(Form.STATE_STEP2_DONE)
        else:
            self.setState(Form.STATE_STEP1_DONE)

    def step2(self):
        while self.ruper.stage != 2:
            self.ruper.NextStep()

        self.displayWidget.setData(self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
        self.displayWidget.update()
            
        self.setState(Form.STATE_STEP2_DONE)

    def step3(self):
        while self.ruper.stage != 3:
            self.ruper.NextStep()

        self.displayWidget.setData(self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
        self.displayWidget.update()
            
        self.setState(Form.STATE_STEP3_DONE)

    def step4Single(self):
        result = self.ruper.NextStep()

        if result != None:
            if result.operation == 'split':
                self.displayWidget.updateStep2Single(result.vertex, result.segment, result.addedSegments, result.deletedTriangle, result.addedTriangles, result.encroachedS, result.flipSequence, self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
            elif result.operation == 'insert':
                self.displayWidget.updateStep4Single(result.vertex, result.triangle, result.deletedTriangle, result.addedTriangles, result.encroachedS, result.flipSequence, self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
            else:
                self.displayWidget.update()

        self.in_animation = True
        if self.ruper.stage == 4:    
            self.setState(Form.STATE_STEP4_DONE)
        else:
            self.setState(Form.STATE_STEP3_DONE)

    def step4(self):
        while self.ruper.stage != 4:
            self.ruper.NextStep()

        self.displayWidget.setData(self.ruper.vertices, self.ruper.segments, self.ruper.triangles)
        self.displayWidget.update()
            
        self.setState(Form.STATE_STEP4_DONE)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    form = Form()
    form.show()

    sys.exit(app.exec_())