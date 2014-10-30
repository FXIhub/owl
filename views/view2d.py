import sys
from PySide import QtGui, QtCore, QtOpenGL
from matplotlib import colors
from matplotlib import cm
from views.view import View
from cxi.imageloader import ImageLoader
from OpenGL import GL, GLU
import OpenGL.GL.ARB.texture_float
import numpy
import math
from views.shaderprogram import compileProgram, compileShader
import logging
import time
from cxi.cache import GLCache
import fit

class View2D(View, QtOpenGL.QGLWidget):
    needDataImage = QtCore.Signal(int)
    needDataPatterson = QtCore.Signal(int)
    centralImgChanged = QtCore.Signal(int, int, int, int)
    translationChanged = QtCore.Signal(int, int)
    stackWidthChanged = QtCore.Signal(int)
    pixelClicked = QtCore.Signal(dict)
    dataItemChanged = QtCore.Signal(object, object)
    def __init__(self, parent, viewer, indexProjector):
        View.__init__(self, parent, indexProjector, "image")
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.autoLast = False
        self.logger = logging.getLogger("View2D")
        # If you want to see debug messages change level here
        self.logger.setLevel(logging.WARNING)

        self.viewer = viewer
        self.centralImg = 0
        #self.targetCentralImg = None
        # translation in unit of window pixels
        self.translation = [0, 0]
        self.zoom = 4.0
        #self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.data = None
        self.mask = None
        self.ix = 0
        self.iy = 0
        self.texturesLoading = {}

        self.imageTextures = GLCache(0)
        self.maskTextures = GLCache(0)
        self.pattersonTexture = None
        self.pattersonTextureImg = -1
        self.texture = {}
        self.parent = parent
        self.setMouseTracking(True)
        self.dragging = False
        # subplot border in unit window pixels (independent of zoom)
        self.subplotBorder = 10
        self.selectedImage = None
        self.lastHoveredViewIndex = None
        self.stackWidth = 1
        self.has_data = False
        self.remainSet = []

        self.loaderThread = ImageLoader(None, self)
        self.needDataImage.connect(self.loaderThread.loadImage)
        self.needDataPatterson.connect(self.loaderThread.loadPatterson)
        self.loaderThread.imageLoaded.connect(self.generateTexture)

#        self.clearLoaderThread.connect(self.loaderThread.clear)

        self.imageLoader = QtCore.QThread()
        self.loaderThread.moveToThread(self.imageLoader)
        self.imageLoader.start()

        self.loadingImageAnimationFrame = 0
        self.loadingImageAnimationTimer = QtCore.QTimer()
        self.loadingImageAnimationTimer.timeout.connect(self._incrementLoadingImageAnimationFrame)
        self.loadingImageAnimationTimer.setSingleShot(True)
        self.loadingImageAnimationTimer.setInterval(100)

        self.setAcceptDrops(True)

        self.slideshowTimer = QtCore.QTimer()
        self.slideshowTimer.setInterval(2000)
        self.slideshowTimer.timeout.connect(self._nextSlideRow)

        settings = QtCore.QSettings()
        self.PNGOutputPath = settings.value("PNGOutputPath")
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.tagView = True
        self.modelView = False
        self.pattersonView = False
        self.hoveredPixel = None

    def _setData(self, dataItem=None):
        """Sets the currently displayed dataItem

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages what's currently being viewed.
        """
        if self.data is not None:
            self.data.deselectStack()
        self.data = dataItem
        if self.data is not None:
            self.data.selectStack()
            self.has_data = True
        else:
            self.has_data = False
        self.dataItemChanged.emit(self.data, self.mask)

    def setMask(self, dataItem=None):
        """Sets the currently applied maskItem

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages what's currently being viewed.
        """
        if self.mask is not None:
            self.mask.deselectStack()
        self.mask = dataItem
        if self.mask is not None:
            self.mask.selectStack()
        self.dataItemChanged.emit(self.data, self.mask)

    def setMaskOutBits(self, maskOutBits=0):
        """Sets the masked out bits in the current mask

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages what's currently being viewed.
        """
        self.maskOutBits = maskOutBits

    def getMask(self, img=0):
        """Returns the mask of the given img

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages what's currently being viewed.
        """
        if self.mask is None:
            return None
        elif self.mask.isStack:
            #if self.integrationMode is None:
            #print self.mask.shape()
            return self.mask.data(img=img)
            #else:
            #return numpy.zeros(shape=(self.data.shape()[-2], self.data.shape()[-1]))
        else:
            return self.mask.data()

    def getData(self, img=None):
        """Returns the given slice of the current imageItem

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages what's currently being viewed.
        """
        return self.data.data(img=img)

    def getPhase(self, img=None):
        """Returns the phases of the given slice of the current imageItem

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages what's currently being viewed.
        """
        return self.data.data(img=img, complex_mode="phase")

    def getPatterson(self):
        """Returns patterson of the current imageItem

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages what's currently being viewed.
        """
        return self.data.pattersonItem.patterson
    def stopThreads(self):
        """Stops the imageLoader thread

        TODO FM: The view2D should only display stuff, not maintain state.
        As such this kind of functions should be moved to some other place
        which manages file access.
        """
        while(self.imageLoader.isRunning()):
            self.imageLoader.quit()
            QtCore.QThread.sleep(1)
    def initializeGL(self):
        """Called once before the first call to paintGL() or resizeGL() to
        setup the scene.

        Reimplemented from QGLWidget """
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClearDepth(1.0)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        if(self.width() and self.height()):
            GLU.gluOrtho2D(0.0, self.width(), 0.0, self.height())
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        self.circle_image = QtGui.QImage(100, 100,
                                         QtGui.QImage.Format_ARGB32_Premultiplied)
        painter = QtGui.QPainter(self.circle_image)
        painter.setRenderHints(QtGui.QPainter.Antialiasing |
                               QtGui.QPainter.SmoothPixmapTransform)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
        painter.drawEllipse(0, 0, 100, 100)
        painter.end()
        self.circle_texture = self.bindTexture(self.circle_image, GL.GL_TEXTURE_2D, GL.GL_RGBA,
                                               QtOpenGL.QGLContext.LinearFilteringBindOption)
        self._initShaders()
        self._initColormapTextures()

        texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        defaultMaskData = numpy.zeros((1, 1), dtype=numpy.float32)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB,
                        1, 1, 0, GL.GL_ALPHA, GL.GL_FLOAT, defaultMaskData)
        self.defaultMaskTexture = texture

    def _initShaders(self):
        if not GL.glUseProgram:
            print 'Missing Shader Objects!'
            sys.exit(1)
        self.makeCurrent()
        self.shader = compileProgram(compileShader('''
            void main()
            {
                //Transform vertex by modelview and projection matrices
                gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

                 // Forward current color and texture coordinates after applying texture matrix
                gl_FrontColor = gl_Color;
                gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
            }
        ''', GL.GL_VERTEX_SHADER), compileShader('''
            uniform sampler2D cmap;
            uniform sampler2D data;
            uniform int norm;
            uniform float vmin;
            uniform float vmax;
            uniform float gamma;
            uniform int do_clamp;
            uniform sampler2D mask;
            uniform float maskedBits;
            uniform float modelCenterX;
            uniform float modelCenterY;
            uniform float modelSize;
            uniform float modelScale;
            uniform int showModel;
            uniform float imageShapeX;
            uniform float imageShapeY;
            uniform float modelVisibility;
            void main()
            {
                vec2 uv = gl_TexCoord[0].xy;
                vec4 color = texture2D(data, uv);
                vec4 mcolor = texture2D(mask, uv);
                float scale = (vmax-vmin);
                float offset = vmin;


                // Apply Model
                if((showModel == 1) && (uv[0] > modelVisibility)){
                        //float s = modelSize*sqrt((uv[0]-modelCenterX)*(uv[0]-modelCenterX)+(uv[1]-modelCenterX)*(uv[1]-modelCenterX));
                        float s = modelSize*sqrt((uv[0]-modelCenterX)*(uv[0]-modelCenterX)*(imageShapeX-1.)*(imageShapeX-1.)+(uv[1]-modelCenterY)*(uv[1]-modelCenterY)*(imageShapeY-1.)*(imageShapeY-1.));
                        color.a = 3.0*(sin(s)-s*cos(s))/(s*s*s);
                        color.a *= color.a * modelScale;

                }else{

                // Apply Mask

                // Using a float for the mask will only work up to about 24 bits
                float maskBits = mcolor.a;
                // loop through the first 16 bits
                float bit = 1.0;
                if(maskBits > 0.0){
                    for(int i = 0;i<16;i++){
                        if(floor(mod(maskBits/bit, 2.0)) == 1.0 && floor(mod(maskedBits/bit, 2.0)) == 1.0){
                            color.a = 0.0;
                            gl_FragColor = color;
                            return;
                        }
                        bit = bit*2.0;
                    }
                }
                }


                uv[0] = (color.a-offset);

                // Check for clamping
                uv[1] = 0.0;
                if(uv[0] < 0.0){
                  if(do_clamp == 1){
                    uv[0] = 0.0;
                    gl_FragColor = texture2D(cmap, uv);
                    return;
                  }else{
                    color.a = 0.0;
                    gl_FragColor = color;
                    return;
                  }
                }
                if(uv[0] > scale){
                  if(do_clamp == 1){
                    uv[0] = 1.0;
                    gl_FragColor = texture2D(cmap, uv);
                    return;
                  }else{
                    color.a = 0.0;
                    gl_FragColor = color;
                    return;
                  }
                }
                // Apply Colormap
                if(norm == 0){
                 // linear
                  uv[0] /= scale;
                }else if(norm == 1){
                 // log
                 scale = log(scale+1.0);
                 uv[0] = log(uv[0]+1.0)/scale;
                }else if(norm == 2){
                  // power
                 scale = pow(scale+1.0, gamma)-1.0;
                 uv[0] = (pow(uv[0]+1.0, gamma)-1.0)/scale;
                }
                color = texture2D(cmap, uv);
                gl_FragColor = color;
            }
        ''', GL.GL_FRAGMENT_SHADER), )
        self.vminLoc = GL.glGetUniformLocation(self.shader, "vmin")
        self.vmaxLoc = GL.glGetUniformLocation(self.shader, "vmax")
        self.gammaLoc = GL.glGetUniformLocation(self.shader, "gamma")
        self.normLoc = GL.glGetUniformLocation(self.shader, "norm")
        self.clampLoc = GL.glGetUniformLocation(self.shader, "do_clamp")
        self.maskedBitsLoc = GL.glGetUniformLocation(self.shader, "maskedBits")
        self.modelCenterXLoc = GL.glGetUniformLocation(self.shader, "modelCenterX")
        self.modelCenterYLoc = GL.glGetUniformLocation(self.shader, "modelCenterY")
        self.modelSizeLoc = GL.glGetUniformLocation(self.shader, "modelSize")
        self.modelScaleLoc = GL.glGetUniformLocation(self.shader, "modelScale")
        self.showModelLoc = GL.glGetUniformLocation(self.shader, "showModel")
        self.imageShapeXLoc = GL.glGetUniformLocation(self.shader, "imageShapeX")
        self.imageShapeYLoc = GL.glGetUniformLocation(self.shader, "imageShapeY")
        self.modelVisibilityLoc = GL.glGetUniformLocation(self.shader, "modelVisibility")

    def _initColormapTextures(self):
        n = 1024
        a = numpy.linspace(0., 1., n)
        maps = [m for m in cm.datad if not m.endswith("_r")]
        mappable = cm.ScalarMappable()
        mappable.set_norm(colors.Normalize())
        self.colormapTextures = {}
        for m in maps:
            mappable.set_cmap(m)
            a_rgb = numpy.zeros(shape=(n, 4), dtype=numpy.uint8)
            temp = mappable.to_rgba(a, None, True)[:, :]
            a_rgb[:, 2] = temp[:, 2]
            a_rgb[:, 1] = temp[:, 1]
            a_rgb[:, 0] = temp[:, 0]
            a_rgb[:, 3] = 0xff
            self.colormapTextures[m] = GL.glGenTextures(1)
            # I don't know how much of this I need
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.colormapTextures[m])
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, n, 1, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, a_rgb)

    def resizeGL(self, w, h):
        """Resize the OpenGL window

        Reimplemented from QGLWidget
        """
        if(self.has_data):
            self._setStackWidth(self.stackWidth)
            self.updateGL()
        GL.glViewport(0, 0, w, h)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        if(w and h):
            GLU.gluOrtho2D(0.0, w, 0.0, h)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

    def _paintSelectedImageBorder(self, img_width, img_height):
        GL.glPushMatrix()
        GL.glColor3f(1.0, 1.0, 1.0)
        GL.glLineWidth(0.5)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex3f(0, img_height, 0.0)
        GL.glVertex3f(img_width, img_height, 0.0)
        GL.glVertex3f(img_width, 0, 0.0)
        GL.glVertex3f(0, 0, 0.0)
        GL.glEnd()
        GL.glPopMatrix()

    def _paintImageProperties(self, img):
        img_width = self._getImgWidth("scene", False)
        img_height = self.getImgHeight("scene", False)
        GL.glPushMatrix()

        font = QtGui.QFont("Courier")
        font.setPointSize(15-self.stackWidth*2)
        metrics = QtGui.QFontMetrics(font)
        GL.glColor3f(1.0, 1.0, 1.0)
        text = []
        if(self.indexProjector.indexToImg(self.lastHoveredViewIndex) == img):
            ix = self.hoveredPixel[0]
            iy = self.hoveredPixel[1]
            if self.loaderThread.maskData[img] is not None:
                text.append("Mask: %5.3g" % (self.loaderThread.maskData[img][iy, ix]))
            text.append("Value: %5.3g" % (self.loaderThread.imageData[img][iy, ix]))
            text.append("Pixel: (%d, %d)" % (ix, iy))

        text.append("Std Dev: %-5.3g" % numpy.std(self.loaderThread.imageData[img]))
        text.append("Mean: %-5.3g" % numpy.mean(self.loaderThread.imageData[img]))
        text.append("Sum: %-5.3g" % numpy.sum(self.loaderThread.imageData[img]))
        text.append("Max: %-5.3g" % numpy.max(self.loaderThread.imageData[img]))
        text.append("Min: %-5.3g" % numpy.min(self.loaderThread.imageData[img]))
        text.append("Index: %d" % self.indexProjector.imgToIndex(img))
        text.append("Image: %d" % img)
        max_width = 0
        height = 0

        for i in range(0, len(text)):
            max_width = max(metrics.width(text[i]), max_width)
        pad = img_width*0.02
        border = img_width*0.015

        height = metrics.height()*len(text)

        GL.glTranslate(border, border, 0)
        GL.glColor4f(0.1, 0.1, 0.1, 0.8)
        GL.glLineWidth(0.5)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex3f(0, 0, 0.0)
        GL.glVertex3f(2*pad+max_width/self.zoom, 0, 0.0)
        GL.glVertex3f(2*pad+max_width/self.zoom, 2*pad+height/self.zoom, 0.0)
        GL.glVertex3f(0, 2*pad+height/self.zoom, 0.0)
        GL.glEnd()

        height = 0.0
        GL.glColor3f(0.9, 0.9, 0.9)
        for i in range(0, len(text)):
#            self.renderText(float(img_width - max_width), height, 0.0, text[i], font)
            self.renderText(pad, pad+height/self.zoom, 0.0, text[i], font)
            height += metrics.height()

        GL.glPopMatrix()


    def _paintFitModelMinima(self):
        GL.glPushMatrix()
        GL.glShadeModel(GL.GL_FLAT)
        GL.glColor3f(0.5, 0.5, 0.5)
        GL.glLineWidth(1./self.zoom)
        imgWidth = self._getImgWidth("window", False)
        imgHeight = self.getImgHeight("window", False)
        cx = self.centerX
        cy = self.centerY
        sides = 200
        qr_approx = [4.49, 7.725, 10.904, 14.135, 17.26, 20.43, 23.56, 26.71] # These are approcimations to tan(qr) = qr
        for a in qr_approx:
            radius = a/(self.modelSize + numpy.finfo("float64").eps)
            for i in range(sides):
                if not i % 4: GL.glBegin(GL.GL_LINE_LOOP)
                x = radius * numpy.cos(i*2*numpy.pi/sides) + cx*imgWidth/self.zoom
                y = radius * numpy.sin(i*2*numpy.pi/sides) + (1-cy)*imgHeight/self.zoom
                if (x > 0) and (x < imgWidth/self.zoom) and (y > 0) and (y < imgHeight/self.zoom):
                    GL.glVertex2f(x, y)
                if not (i + 3) % 4: GL.glEnd()
        GL.glPopMatrix()


    def _paintCircleFitMask(self):
        GL.glPushMatrix()
        GL.glShadeModel(GL.GL_FLAT)
        GL.glColor3f(1.0, 1.0, 1.0)
        GL.glLineWidth(0.5/self.zoom)
        imgWidth = self._getImgWidth("window", False)
        imgHeight = self.getImgHeight("window", False)
        cx = self.centerX
        cy = self.centerY
        sides = 200
        radius = self.maskRadius
        GL.glBegin(GL.GL_LINE_LOOP)
        for i in range(sides):
            x = radius * numpy.cos(i*2*numpy.pi/sides) + cx*imgWidth/self.zoom
            y = radius * numpy.sin(i*2*numpy.pi/sides) + (1-cy)*imgHeight/self.zoom
            x = max(0, min(x, imgWidth/self.zoom))
            y = max(0, min(y, imgHeight/self.zoom))
            GL.glVertex2f(x, y)
        GL.glEnd()
        GL.glPopMatrix()

    @QtCore.Slot()
    def _incrementLoadingImageAnimationFrame(self):
        self.loadingImageAnimationFrame += 1
        self.updateGL()

    def _drawRectangle(self, width, height, filled=True):
        if(filled):
            GL.glBegin(GL.GL_POLYGON)
        else:
            GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex3f(0, height, 0.0)
        GL.glVertex3f(width, height, 0.0)
        GL.glVertex3f(width, 0, 0.0)
        GL.glVertex3f(0, 0, 0.0)
        GL.glEnd()
    def _drawDisk(self, center, radius, nsides=20, filled=True):
        if(filled):
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.circle_texture)
            GL.glBegin(GL.GL_QUADS)
            GL.glTexCoord2f(0.0, 1.0)
            GL.glVertex3f(center[0]-radius, center[1]-radius, 0.0)
            GL.glTexCoord2f(1.0, 1.0)
            GL.glVertex3f(center[0]+radius, center[1]-radius, 0.0)
            GL.glTexCoord2f(1.0, 0.0)
            GL.glVertex3f(center[0]+radius, center[1]+radius, 0.0)
            GL.glTexCoord2f(0.0, 0.0)
            GL.glVertex3f(center[0]-radius, center[1]+radius, 0.0)
            GL.glEnd()
            GL.glDisable(GL.GL_TEXTURE_2D)
           # glPointSize(2*radius*self.zoom)
           # glEnable(GL_POINT_SMOOTH)
           # glBegin(GL_POINTS)
           # glVertex3f(center[0], center[1], 0)
           # glEnd()
        else:
            GL.glBegin(GL.GL_LINE_LOOP)
            for side in range(0, nsides):
                angle = 2*math.pi*side/nsides
                GL.glVertex3f(radius*math.cos(angle)+center[0],
                              radius*math.sin(angle)+center[1], 0)
            GL.glEnd()

    def _paintLoadingImage(self, img):
        frame = self.loadingImageAnimationFrame%24
        img_width = self._getImgWidth("scene", False)
        img_height = self.getImgHeight("scene", False)
        GL.glPushMatrix()
        (x, y, z) = self._imageToScene(img, imagePos='BottomLeft', withBorder=False)
        GL.glTranslatef(x, y, z)
        # Draw a ball in the center
        path_radius = min(img_width, img_height)/10.0
        path_center = (img_width/2.0, 6*img_height/10.0)
        radius = min(img_width, img_height)/40.0
        ndisks = 8
        for i in range(0, ndisks):
            angle = math.pi/2.0-2*math.pi*i/ndisks
            if(i > frame/3):
                continue
            elif(i == frame/3):
                GL.glColor3f((frame%3+1)/4.0, (frame%3+1)/4.0, (frame%3+1)/4.0)
            else:
                GL.glColor3f(3/4.0, 3/4.0, 3/4.0)
            self._drawDisk((path_center[0]+math.cos(angle)*path_radius,
                            path_center[1]+math.sin(angle)*path_radius),
                           radius, 100)
        GL.glColor3f(2/4.0, 2/4.0, 2/4.0)
        self._drawRectangle(img_width, img_height, filled=False)
        font = QtGui.QFont()
        metrics = QtGui.QFontMetrics(font)
        width = metrics.width("Loading...")
        ratio = (img_width*self.zoom/4.0)/width
        font.setPointSize(font.pointSize()*ratio)
        GL.glColor3f(3/4.0, 3/4.0, 3/4.0)
        self.renderText(3*img_width/8.0, 3*img_height/10.0, 0.0, "Loading...", font)
        GL.glPopMatrix()

    def _paintImage(self, img):
        # TODO FM: This should be broken in small functions
        img_width = self._getImgWidth("scene", False)
        img_height = self.getImgHeight("scene", False)
        GL.glPushMatrix()
        (x, y, z) = self._imageToScene(img, imagePos='BottomLeft', withBorder=False)
        GL.glTranslatef(x, y, z)

        GL.glUseProgram(self.shader)
        GL.glActiveTexture(GL.GL_TEXTURE0+1)
        data_texture_loc = GL.glGetUniformLocation(self.shader, "data")
        GL.glUniform1i(data_texture_loc, 1)
        pattersonParams = self.data.pattersonItem.getParams(img)
        pattersonEnabled = ((img == pattersonParams["_pattersonImg"]) and (img == self.selectedImage) and
                            self.pattersonView and (img == self.pattersonTextureImg))
        if not pattersonEnabled:
            imageTexture = self.imageTextures[img]
            imageData = self.loaderThread.imageData[img]
        else:
            imageTexture = self.pattersonTexture
            imageData = self.loaderThread.pattersonData
        GL.glBindTexture(GL.GL_TEXTURE_2D, imageTexture)

        GL.glActiveTexture(GL.GL_TEXTURE0+2)
        cmap_texture_loc = GL.glGetUniformLocation(self.shader, "cmap")
        GL.glUniform1i(cmap_texture_loc, 2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.colormapTextures[self.colormapText])

        GL.glActiveTexture(GL.GL_TEXTURE0+3)
        loc = GL.glGetUniformLocation(self.shader, "mask")
        GL.glUniform1i(loc, 3)
        if (img in self.maskTextures.keys()) and not pattersonEnabled:
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.maskTextures[img])
        else:
            # If not mask is available load the default mask
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.defaultMaskTexture)

        if self.autorange:
            GL.glUniform1f(self.vminLoc, imageData.min())
            GL.glUniform1f(self.vmaxLoc, imageData.max())
        elif pattersonEnabled:
            GL.glUniform1f(self.vminLoc, 0.)
            GL.glUniform1f(self.vmaxLoc, 1.)
        else:
            GL.glUniform1f(self.vminLoc, self.normVmin)
            GL.glUniform1f(self.vmaxLoc, self.normVmax)
        if not pattersonEnabled:
            GL.glUniform1f(self.gammaLoc, self.normGamma)
            GL.glUniform1i(self.normLoc, self.normScalingValue)
            GL.glUniform1i(self.clampLoc, self.normClamp)
            GL.glUniform1f(self.maskedBitsLoc, self.maskOutBits)
        else:
            GL.glUniform1f(self.gammaLoc, self.normGamma)
            GL.glUniform1i(self.normLoc, 0)
            GL.glUniform1i(self.clampLoc, self.normClamp)
            GL.glUniform1f(self.maskedBitsLoc, self.maskOutBits)

        GL.glUniform1i(self.showModelLoc, self.modelView)

        # Model related variables
        if(self.modelView):
            # TODO FM: All this physics knowledge should not be here.
            # It has to be moved out of here, possibly even out of owl
            params = self.data.modelItem.getParams(img)
            s = imageData.shape
            self.centerX = ((s[1]-1)/2.+params["offCenterX"])/(s[1]-1)
            self.centerY = ((s[0]-1)/2.+params["offCenterY"])/(s[0]-1)
            GL.glUniform1f(self.modelCenterXLoc, self.centerX)
            GL.glUniform1f(self.modelCenterYLoc, self.centerY)
            p = params["detectorPixelSizeUM"]*1.E-6
            D = params["detectorDistanceMM"]*1.E-3
            wl = params["photonWavelengthNM"]*1.E-9
            h = fit.DICT_physical_constants['h']
            c = fit.DICT_physical_constants['c']
            qe = fit.DICT_physical_constants['e']
            ey_J = h*c/wl
            r = params["diameterNM"]*1.E-9/2.
            V = 4/3.*numpy.pi*r**3
            I_0 = params["intensityMJUM2"]*1.E-3/ey_J*1.E12
            rho_e = fit.Material(material_type=params["materialType"]).get_electron_density()
            QE = params["detectorQuantumEfficiency"]
            ADUP = params["detectorADUPhoton"]
            # k = 2 pi / wavelength
            # q = coordinate * (k p / D)
            # s = q modelRadius = coordinate * modelSize
            # modelSize = q modelRadius / coordinate = modelRadius * k p / D
            k = 2*numpy.pi/wl
            self.modelSize = r*k*p/D
            GL.glUniform1f(self.modelSizeLoc, self.modelSize)
            # scale = K * QE * ADUP
            # K = I_0 (rho_e p/D r_0 V)^2
            K = I_0*(rho_e*p/D*fit.DICT_physical_constants["re"]*V)**2
            scale = K * QE * ADUP

            GL.glUniform1f(self.modelScaleLoc, scale)
            GL.glUniform1f(self.imageShapeXLoc, imageData.shape[1])
            GL.glUniform1f(self.imageShapeYLoc, imageData.shape[0])
            GL.glUniform1f(self.modelVisibilityLoc, params["_visibility"])
            self.maskRadius = params["maskRadius"]

        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(0, img_height, 0.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(img_width, img_height, 0.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(img_width, 0, 0.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(0, 0, 0.0)
        GL.glEnd()
        # Activate again the original texture unit
        GL.glActiveTexture(GL.GL_TEXTURE0)

        GL.glUseProgram(0)
        if(self.modelView):
            self._paintCircleFitMask()
            self._paintFitModelMinima()

        if(img == self.selectedImage):
            self._paintSelectedImageBorder(img_width, img_height)
            self._paintImageProperties(img)

        if(self.data and self.tagView and self.data.tagsItem.tags and self.data.tagsItem.tags != []):
            tag_size = self._tagSize()
            tag_pad = self._tagPad()
            tag_distance = self._tagDistance()
            for i in range(0, len(self.data.tagsItem.tags)):
                GL.glPushMatrix()
                color = self.data.tagsItem.tags[i][1]
                GL.glColor3f(color.redF(), color.greenF(), color.blueF())
                GL.glLineWidth(0.5)
                if(self.data.tagsItem.tagMembers[i][img]):
                    GL.glBegin(GL.GL_QUADS)
                else:
                    GL.glBegin(GL.GL_LINE_LOOP)
                GL.glVertex3f(tag_pad, img_height-(tag_pad+tag_size+tag_distance*i), 0.0)
                GL.glVertex3f(tag_pad+tag_size, img_height-(tag_pad+tag_size+tag_distance*i), 0.0)
                GL.glVertex3f(tag_pad+tag_size, img_height-(tag_pad+tag_distance*i), 0.0)
                GL.glVertex3f(tag_pad, img_height-(tag_pad+tag_distance*i), 0.0)
                GL.glEnd()
                GL.glPopMatrix()

        GL.glPopMatrix()


    def paintGL(self):
        """Main drawing routine

        Reimplemented from QGLWidget
        """
#        self.time2 = time.time()
        time3 = time.time()
#        print '%s function took %0.3f ms' % ("Non paintGL", (self.time2-self.time1)*1000.0)
        if(not self.isValid() or not self.isVisible()):
            return
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glLoadIdentity()
        # Set GL origin in the middle of the widget
        GL.glTranslatef(self.width()/2., self.height()/2., 0)
        # Apply user defined translation
        GL.glTranslatef(self.translation[0], self.translation[1], 0)
        # Apply user defined zoom
        GL.glScalef(self.zoom, self.zoom, 1.0)
        # Put GL origin on the top left corner of the widget
        GL.glTranslatef(-(self.width()/self.zoom)/2., (self.height()/self.zoom)/2., 0)
        startTimer = False
        if(self.has_data):
            if(self.data.format == 2):
                img_width = self._getImgWidth("scene", False)  #deprecated?
                img_height = self.getImgHeight("scene", False) #deprecated?
                visible = self._visibleImages()
                self._updateTextures(visible)
                for i, img in enumerate(set.intersection(set(self.imageTextures.keys()),
                                                         set(visible), set(self.loaderThread.loadedImages()))):
                    self._paintImage(img)
                remainset = (set(visible) - set(self.imageTextures.keys()))
                self.remainSet = remainset
                if len(remainset) > 0:
                    for img in remainset:
                        self._paintLoadingImage(img)
                    startTimer = True
                else:
                    self.loadingImageAnimationFrame = 0
                    if self.loadingImageAnimationTimer.isActive():
                        self.loadingImageAnimationTimer.stop()

                if len(visible) > 0:
                    # Set and emit current view index
                    newVal = self._windowToImage(self._getImgWidth("window", True)/2,
                                                 self.getImgHeight("window", True)/2, 0, False, False)
                    if self.centralImg != newVal:
                        self.centralImg = self._windowToImage(self._getImgWidth("window", True)/2,
                                                              self.getImgHeight("window", True)/2, 0, False, False)
                        self.centralImgChanged.emit(self.centralImg, self._getNImages(),
                                                    self.indexProjector.imgToIndex(self.centralImg),
                                                    self._getNImagesVisible())
        if startTimer:
            # If we are slow-drawing, please wait more before drawing again...
            time4 = time.time()
            self.loadingImageAnimationTimer.setInterval(int((time4-time3)*1000 + 100))
            self.loadingImageAnimationTimer.start()
#        glFlush()
#        print '%s function took %0.3f ms' % ("paintGL", (time4-time3)*1000.0)
#        self.time1 = time.time()

    def loadStack(self, data):
        """Load a given stack dataset"""
        self._setData(data)
        if data.isStack:
            data.isSelectedStack = True
        self._zoomFromStackWidth()


    def _getNImages(self):
        """Return number of images in dataset"""
        # will have to be changed when filter is implemented
        if self.data.isStack:
            return self.data.shape()[0]
        else:
            return 1

    def _getNImagesVisible(self):
        """Return number of images which are not filtered out"""
        if not self.data.isStack:
            return 1
        else:
            if self.indexProjector.imgs is None:
                return self._getNImages()
            else:
                return len(self.indexProjector.imgs)

    def getImgHeight(self, reference, border=False):
        """Returns the height of an image in the given reference

        TODO FM: Called once from view2DScrollWidget. Why?
        """
        if self.data is not None:
            imgHeight = self.data.height()
            if border == True:
                imgHeight += self._subplotSceneBorder()
        else:
            imgHeight = 1000
        if reference == "window":
            return imgHeight*self.zoom
        elif reference == "scene":
            return imgHeight

    def _getImgWidth(self, reference, border=False):
        """Returns the width of an image in the given reference"""
        imgWidth = self.data.width()
        if border == True:
            imgWidth += self._subplotSceneBorder()
        if reference == "window":
            return imgWidth*self.zoom
        elif reference == "scene":
            return imgWidth

    def _visibleImages(self):
        """Returns the images that are currently visible in the display"""
        visible = []
        if(self.has_data is False):
            return visible

        top_left = self._windowToViewIndex(0, 0, 0, checkExistance=False, clip=False)
        bottom_right = self._windowToViewIndex(self.width(), self.height(), 0, checkExistance=False, clip=False)

        top_left = self._viewIndexToCell(top_left)
        bottom_right = self._viewIndexToCell(bottom_right)
        nImagesVisible = self._getNImagesVisible()
        for x in numpy.arange(0, self.stackWidth):
            for y in numpy.arange(max(0, math.floor(top_left[1])), math.floor(bottom_right[1]+1)):
                viewIndex = y*self.stackWidth+x
                if(viewIndex < nImagesVisible):
                    img = self.indexProjector.indexToImg(viewIndex)
                    visible.append(img)
        return visible

    @QtCore.Slot(int)
    def generateTexture(self, img):
        """Generates a texture, used for display, for the given image.

        Called after the imageLoader has finished loading an image."""
        if img not in self.loaderThread.imageData.keys():
            # in the moment of changing datasets we can end up here
            # no reason to panic, just return
            return

        # If we already have the texture we just return
        if not (img in self.imageTextures):
            self.logger.debug("Generating image texture %d"  % (img))
            imageData = self.loaderThread.imageData[img]
            maskData = self.loaderThread.maskData[img]
            texture = GL.glGenTextures(1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB,
                            imageData.shape[1], imageData.shape[0], 0, GL.GL_ALPHA, GL.GL_FLOAT, imageData)
            self.imageTextures[img] = texture

            if(maskData is not None):
                self.logger.debug("Generating mask texture %d"  % (img))
                texture = GL.glGenTextures(1)
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
                GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
                GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
                GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB,
                                imageData.shape[1], imageData.shape[0], 0, GL.GL_ALPHA, GL.GL_FLOAT, maskData)
                self.maskTextures[img] = texture

            self.remainSet = set.difference(self.remainSet, [img])
            if len(self.remainSet) == 0:
                self.updateGL()

        if self.pattersonView:
            pattersonParams = self.data.pattersonItem.getParams(img)
            if(self.pattersonView and (img == self.selectedImage) and
               (pattersonParams["_pattersonImg"] == img) and not self.data.pattersonItem.textureLoaded):
                #print "generate patterson texture"
                temp = abs(self.loaderThread.pattersonData)
                P = numpy.ones(temp.shape, dtype=numpy.float32)
                P[:] = temp[:]
                texture = GL.glGenTextures(1)
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
                GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
                GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
                GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB,
                                P.shape[1], P.shape[0], 0, GL.GL_ALPHA, GL.GL_FLOAT, P)
                self.pattersonTexture = texture
                self.pattersonTextureImg = img
                self.data.pattersonItem.textureLoaded = True
                self.updateGL()

    def _updateTextures(self, images):
        for img in images:
            if(img not in set.intersection(set(self.imageTextures.keys()), set(self.loaderThread.loadedImages()))):
                self.needDataImage.emit(img)
            else:
                # Let the cache know we're using these images
                self.loaderThread.imageData.touch(img)
            if self.pattersonView:
                pattersonParams = self.data.pattersonItem.getParams(img)
                if((pattersonParams["_pattersonImg"] == img) and (self.selectedImage == img)
                   and not self.data.pattersonItem.textureLoaded):
                    self.needDataPatterson.emit(img)

    def _scrollBy(self, count=1, wrap=False):
        # positive counts correspond to upwards movement of window / downwards movement of images
        stepSize = 1
        translation = (0, stepSize*count)
        self._translateBy(translation, wrap)

    def scrollTo(self, translationY, wrap=False):
        """Scroll to a given y position."""
        translation = (0, translationY)
        self._translateTo(translation, wrap)

    def _translateBy(self, translationBy, wrap=False):
        self._translateTo([self.translation[0]+translationBy[0], self.translation[1]+translationBy[1]], wrap)

    def _translateTo(self, translation, wrap=False):
        self.translation[0] = translation[0]
        self.translation[1] = translation[1]
        self._clipTranslation()
        self.translationChanged.emit(self.translation[0], self.translation[1])
        self.updateGL()

    def _clipTranslation(self, wrap=False):
        # Translation is bounded by top_margin < translation < bottom_margin
        if(self.has_data):
            top_margin = self.minimumTranslation()
            if(self.translation[1] < top_margin):
                self.translation[1] = top_margin
            bottom_margin = self.maximumTranslation()
            if(self.translation[1] > bottom_margin):
                if not wrap:
                    self.translation[1] = bottom_margin
                else:
                    self.translation[1] = 0

    def maximumTranslation(self, withMargin=True):
        """Returns the maximum y translation possible for an image"""
        margin = self.subplotBorder*3
        img_height = self.getImgHeight("window", True)
        stack_height = math.ceil(float(self._getNImagesVisible())/self.stackWidth)*img_height
        if(withMargin):
            bottom_margin = max(0, stack_height+margin-self.height())
        else:
            bottom_margin = max(0, stack_height-self.height())
        return bottom_margin

    def minimumTranslation(self, withMargin=True):
        """Returns the minimum y translation possible for an image"""
        margin = self.subplotBorder*3
        if(withMargin):
            return -margin
        else:
            return 0

    def wheelEvent(self, event):
        """Handles mouse wheel events

        Reimplemented from QWidget"""
        settings = QtCore.QSettings()
        t = -event.delta()*float(settings.value("scrollDirection"))
        self._translateBy([0, t])

    def toggleSlideShow(self):
        """Toggles the timer that runs the slide show"""
        if self.slideshowTimer.isActive():
            self.slideshowTimer.stop()
        else:
            self.slideshowTimer.start()

    def _nextSlideRow(self):
        self.nextRow(wrap=True)
        info = self._getPixelInfo(self.centralImg, self.ix, self.iy)
        if info is None:
            return
        self.selectedImage = info["img"]
        self.pixelClicked.emit(info)

    def nextRow(self, wrap=False):
        """Scroll display by one row down"""
        self._changeRowBy(count=1, wrap=wrap)

    def previousRow(self, wrap=False):
        """Scroll display by one row up"""
        self._changeRowBy(count=-1, wrap=wrap)

    def _changeRowBy(self, count=1, wrap=False):
        """Scroll display by the given number of rows"""
        img_height = self.getImgHeight("window", True)
        t = count*img_height
        self._scrollBy(t, wrap)

    def browseToViewIndex(self, index):
        """Scroll to a certain display position"""
        img_height = self.getImgHeight("window", True)
        self._translateTo([0, img_height*int(numpy.floor(index/self.stackWidth))])

    def _browseToLastIfAuto(self):
        """Scroll to the last position if autoLast is true"""
        if self.autoLast:
            if self.data is not None:
                self.browseToViewIndex(self.indexProjector.getNViewIndices()-1)

    def mouseReleaseEvent(self, event):
        """Handle mouse releases

        Reimplemented from QWidget"""
        self.dragging = False
        # Select even when draggin
        #if(event.button() == QtCore.Qt.LeftButton):
        #    self.selectedImage = self.indexProjector.indexToImg(self.lastHoveredViewIndex)
        #    self.imageSelected.emit(self.selectedImage)
        #    self.updateGL()

    def mousePressEvent(self, event):
        """Handle mouse presses

        Reimplemented from QWidget"""
        self.dragStart = event.pos()
        self.dragPos = event.pos()
        self.dragging = True
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        x = pos.x()
        y = pos.y()
        img = self._windowToImage(x, y, 0)
        if img in self.loaderThread.imageData.keys():
            (self.ix, self.iy) = self._windowToImageCoordinates(x, y, 0)
            info = self._getPixelInfo(img, self.ix, self.iy)
            if info is None:
                return
            self.selectedImage = info["img"]
            self.pixelClicked.emit(info)
            self.updateGL()

    def _getPixelInfo(self, img, ix, iy):
        info = {}
        info["ix"] = ix
        info["iy"] = iy
        if(ix >= self.loaderThread.imageData[img].shape[1] or iy >= self.loaderThread.imageData[img].shape[0]
           or ix < 0 or iy < 0):
            return None
        info["img"] = img
        info["viewIndex"] = self.indexProjector.imgToIndex(img)
        info["imageValue"] = self.loaderThread.imageData[img][iy, ix]
        if self.loaderThread.maskData[img] is None:
            info["maskValue"] = None
        else:
            info["maskValue"] = self.loaderThread.maskData[img][iy, ix]
        info["imageMin"] = numpy.min(self.loaderThread.imageData[img])
        info["imageMax"] = numpy.max(self.loaderThread.imageData[img])
        info["imageSum"] = numpy.sum(self.loaderThread.imageData[img])
        info["imageMean"] = numpy.mean(self.loaderThread.imageData[img])
        info["imageStd"] = numpy.std(self.loaderThread.imageData[img])
        img_height = self.getImgHeight("scene", False)
        info["tagClicked"] = -1
        if(self.tagView):
            if(ix >= self._tagPad() and ix < self._tagDistance()):
                if(iy/self._tagDistance() < len(self.data.tagsItem.tags)):
                    if(iy%self._tagDistance() >= self._tagPad()):
                        info["tagClicked"] = int(iy/self._tagDistance())
        return info

    def mouseMoveEvent(self, event):
        """Handle mouse moves

        Reimplemented from QWidget"""
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        x = pos.x()
        y = pos.y()
        img = self._windowToImage(x, y, 0)
        if img in self.loaderThread.imageData.keys():
            (ix, iy) = self._windowToImageCoordinates(x, y, 0)
            if(ix < self.loaderThread.imageData[img].shape[1] and
               iy < self.loaderThread.imageData[img].shape[0] and
               ix >= 0 and iy >= 0):
                self.hoveredPixel = [ix, iy]
                self.updateGL()
        if(self.dragging):
            self._translateBy([0, -(event.pos()-self.dragPos).y()])
            self._clipTranslation()
            if(QtGui.QApplication.keyboardModifiers().__and__(QtCore.Qt.ControlModifier)):
                self._translateBy([0, (event.pos()-self.dragPos).x()])
            self.dragPos = event.pos()
            self.updateGL()
        ss = self._hoveredViewIndex()
        if(ss != self.lastHoveredViewIndex):
            self.lastHoveredViewIndex = ss
            self.updateGL()

    def _hoveredViewIndex(self):
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        viewIndex = self._windowToViewIndex(pos.x(), pos.y(), 0)
        return viewIndex

    def _imageToScene(self, imgIndex, imagePos='TopLeft', withBorder=True):
        """Returns the scene position of the image corresponding to the index given

        By default the coordinate of the TopLeft corner of the image is returned
        By default the border is considered part of the image"""

        img_width = self._getImgWidth("scene", True)
        img_height = self.getImgHeight("scene", True)
        (col, row) = self._imageToCell(imgIndex)
        x = img_width*col
        y = -img_height*row
        z = 0
        if(imagePos == 'TopLeft'):
            if(not withBorder):
                x += self._subplotSceneBorder()/2.
                y -= self._subplotSceneBorder()/2.
        elif(imagePos == 'BottomLeft'):
            y -= img_height
            if(not withBorder):
                x += self._subplotSceneBorder()/2.
                y += self._subplotSceneBorder()/2.
        elif(imagePos == 'BottomRight'):
            x += img_width
            y -= img_height
            if(not withBorder):
                x -= self._subplotSceneBorder()/2.
                y += self._subplotSceneBorder()/2.
        elif(imagePos == 'TopRight'):
            x += img_width
            if(not withBorder):
                x -= self._subplotSceneBorder()/2.
                y -= self._subplotSceneBorder()/2.
        elif(imagePos == 'Center'):
            x += img_width/2.
            y -= img_height/2.
        else:
            raise('Unknown imagePos: %s' % (imagePos))
        return (x, y, z)

    def _imageToWindow(self, imgIndex, imagePos='TopLeft', withBorder=True):
        """Returns the window position of the top left corner of the image corresponding to the index given"""
        (x, y, z) = self._imageToScene(imgIndex, imagePos, withBorder)
        return self._sceneToWindow(x, y, z)

    def _sceneToWindow(self, x, y, z):
        """Returns the window location of a given point in scene"""
        modelview = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
        projection = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
        viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        (x, y, z) = GLU.gluProject(x, y, z, model=modelview, proj=projection, view=viewport)
        return (x, y, z)

    def _windowToScene(self, x, y, z):
        """Returns the x, y, z position of a particular window position"""
        modelview = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
        projection = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
        viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        (x, y, z) = GLU.gluUnProject(x, viewport[3]-y, z, model=modelview, proj=projection, view=viewport)
        return (x, y, z)

    def _windowToImageCoordinates(self, x, y, z):
        """Returns pixel corrdinates in image"""
        (xw, yw, zw) = self._windowToScene(x, y, z)
        imageWidth = self._getImgWidth("scene", True)
        imageHeight = self.getImgHeight("scene", True)
        border = self._subplotSceneBorder()
        ix = int(round(xw%imageWidth - border/2. - 1))
        iy = int(round(imageHeight - yw%imageHeight - border/2.0 - 1))
        return (ix, iy)

    def _windowToViewIndex(self, x, y, z, checkExistance=True, clip=True):
        """Returns the view index (index after sorting and filtering) of the image that is at a particular window location"""
        if(self.has_data is True):
            shape = (self.data.height(), self.data.width())
            modelview = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
            projection = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            (x, y, z) = GLU.gluUnProject(x, viewport[3]-y, z, model=modelview, proj=projection, view=viewport)
            #print x, y
            (x, y) = (int(numpy.floor(x/(self.data.width()+self._subplotSceneBorder()))),
                      int(numpy.floor(-y/(self.data.height()+self._subplotSceneBorder()))))
            if(clip and (x < 0 or x >= self.stackWidth or y < 0)):
                return None
            if(checkExistance and x + y*self.stackWidth >= self._getNImages()):
                return None
            return x + y*self.stackWidth

    def _windowToImage(self, x, y, z, checkExistance=True, clip=True):
        """Returns the index of the image that is at a particular window location"""
        return self.indexProjector.indexToImg(self._windowToViewIndex(x, y, z, checkExistance, clip))

    def _viewIndexToCell(self, index):
        """Returns the column and row from an view index"""
        if(index is None):
            return index
        else:
            return (index%self.stackWidth, int(index/self.stackWidth))

    def _imageToCell(self, img):
        """Returns the column and row from an imagex"""
        if(img is None):
            return img
        else:
            viewIndex = self.indexProjector.imgToIndex(img)
            return self._viewIndexToCell(viewIndex)

    def _scaleZoom(self, ratio):
        self.zoom *= ratio
        self.translation[0] *= ratio
        viewIndex = self.indexProjector.imgToIndex(self.centralImg)
        self.browseToViewIndex(viewIndex)

    def _zoomFromStackWidth(self):
        """Calculate the appropriate zoom level such that the windows will exactly fill the viewport widthwise"""
        width = self.stackWidth
        # We'll assume all images have the same size and the projection is isometric
        if(self.has_data is not True):
            return 1
        # Calculate the zoom necessary for the given stack width to fill the current viewport width
        new_zoom = float(self.width()-width*self.subplotBorder)/(self.data.width()*width)
        self._scaleZoom(new_zoom/self.zoom)

    def clear(self):
        """Clear the view"""
        self.clearView()
        QtCore.QCoreApplication.sendPostedEvents()
        QtCore.QCoreApplication.processEvents()
        self._setData()
        self.setMask()
        self.setMaskOutBits()
        self.clearTextures()
        self.updateGL()

    def clearTextures(self):
        """Clears the OpenGL and cached textures"""
        GL.glDeleteTextures(self.imageTextures.values())
        GL.glDeleteTextures(self.maskTextures.values())
        self.imageTextures = GLCache(1024*1024*int(QtCore.QSettings().value("textureCacheSize")))
        self.maskTextures = GLCache(1024*1024*int(QtCore.QSettings().value("textureCacheSize")))
        self.loaderThread.clear()
        self.pattersonTexture = None
        self.pattersonTextureImg = -1

    def _setStackWidth(self, width):
        """Change the number of images displayed side by side"""
        self.stackWidth = width
        # If there's no data just set the width and return
        if(self.has_data is not True):
            return
        self.stackWidthChanged.emit(self.stackWidth)
        # Now change the width and zoom to match
        self._zoomFromStackWidth()

    def _subplotSceneBorder(self):
        """Returns the size of the image border in pixels"""
        return self.subplotBorder/self.zoom

    def refreshDisplayProp(self, prop):
        """Redraws the image properties hovering display"""
        if prop is not None:
            self.normScaling = prop["normScaling"]
            if(self.normScaling == 'lin'):
                self.normScalingValue = 0
            elif(self.normScaling == 'log'):
                self.normScalingValue = 1
            elif(self.normScaling == 'pow'):
                self.normScalingValue = 2
            self.normVmin = prop["normVmin"]
            self.normVmax = prop["normVmax"]
            self.autorange = prop["autorange"]
            self.normGamma = prop["normGamma"]
            if(prop["normClamp"] == True):
                self.normClamp = 1
            else:
                self.normClamp = 0
            if not hasattr(self, 'colormapText') or self.colormapText != prop["colormapText"]:
                self.colormapText = prop["colormapText"]
            self._setStackWidth(prop["imageStackSubplotsValue"])
            self.indexProjector.setProjector(prop["sortingDataItem"], prop["sortingInverted"])
            #self.imageStackN = prop["N"]
        self.updateGL()

    def saveToPNG(self):
        """Save central image to PNG"""
        try:
            import Image
        except:
            self.logger.warning("Cannot import PIL (Python Image Library). Saving to PNG failed.")
            return
        self.browseToViewIndex(self.indexProjector.imgToIndex(self.centralImg))
        self.updateGL()
        (x, y, z) = self._imageToWindow(self.centralImg, 'TopLeft', False)
        y = int(round(y))
        x = int(round(x))
        width = int(self._getImgWidth("window"))
        height = int(self.getImgHeight("window"))
        buffer = GL.glReadPixels(x, y-height, width, height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
        image = Image.fromstring(mode="RGBA", size=(width, height),
                                 data=buffer)
        filename = "%s/%s_%s_%i.png" % (self.PNGOutputPath, (self.viewer.filename.split("/")[-1])[:-4],
                                        self.data.name, self.centralImg)
        image.save(filename)
        self.viewer.statusBar.showMessage("Saving image %i to %s" % (self.centralImg, filename), 1000)

    def toggleAutoLast(self):
        """Toogles moving to the last image in the stack automatically"""
        self.autoLast = not self.autoLast
        self._browseToLastIfAuto()

    # DATA
    def onStackSizeChanged(self, newStackSize):
        """Triggered when the size of the stack changes"""
        # not sure if this is needed
        if self.data is not None:
            self.has_data = True
        else:
            self.has_data = False
        self._browseToLastIfAuto()

    def _tagSize(self):
        """Returns the size of the side of the square representing each tag"""
        imageWidth = self._getImgWidth("scene", True)
        return 0.05*imageWidth

    def _tagPad(self):
        """Returns the padding between the squares the tags"""
        imageWidth = self._getImgWidth("scene", True)
        return 0.01*imageWidth

    def _tagDistance(self):
        """Returns the distance between the center of the squares representing consecutive tags"""
        return self._tagSize()+self._tagPad()

    def moveSelectionBy(self, x, y):
        """Moves current selection"""
        if(abs(x) > 1 or abs(y) > 1):
            raise AssertionError('moveSelection only supports moves <= 1 in x and y')
        if(self.selectedImage is None):
            return
        viewIndex = self.indexProjector.imgToIndex(self.selectedImage)
        img = self.indexProjector.indexToImg(viewIndex+x+y*self.stackWidth)
        rowChange = y
        if(x == 1):
            if((viewIndex+x) % self.stackWidth == 0):
                rowChange += 1
        elif(x == -1):
            if((viewIndex) % self.stackWidth == 0):
                rowChange -= 1
        self._changeRowBy(rowChange)

        self.selectedImage = img
        if img in self.loaderThread.imageData.keys():
            info = self._getPixelInfo(img, 0, 0)
            if info is None:
                return
            self.pixelClicked.emit(info)

        self.updateGL()

    def toggleTagView(self):
        """Toggle the visibility of the squares representing the tags"""
        self.tagView = not self.tagView
        self.updateGL()

    def toggleModelView(self):
        """Toggle the visibility of the model overlay"""
        self.modelView = not self.modelView
        self.updateGL()

    def togglePattersonView(self):
        """Toggle the visibility of the patterson"""
        self.pattersonView = not self.pattersonView
        self.updateGL()
