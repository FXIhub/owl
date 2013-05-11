from PySide import QtGui, QtCore, QtOpenGL
from matplotlib import colors
from matplotlib import cm
from view import View
from imageloader import ImageLoader
from OpenGL.GL import *
from OpenGL.GLU import *
import OpenGL.GL.ARB.texture_float
import numpy
import math
from shaderprogram import compileProgram, compileShader
import logging
from cache import GLCache
        
class View2D(View,QtOpenGL.QGLWidget):
    needsImage = QtCore.Signal(int)
    #imageSelected = QtCore.Signal(int)
    visibleImgChanged = QtCore.Signal(int,int,int,int)
    translationChanged = QtCore.Signal(int,int)
    stackWidthChanged = QtCore.Signal(int)
    pixelClicked = QtCore.Signal(dict)
    def __init__(self,viewer,parent=None):
        View.__init__(self,parent,"image")
        QtOpenGL.QGLWidget.__init__(self,parent)
        self.logger = logging.getLogger("View2D")
        # If you want to see debug messages change level here
        self.logger.setLevel(logging.WARNING)

        self.viewer = viewer
        self.visibleImg = 0
        # translation in unit of window pixels
        self.translation = [0,0]
        self.zoom = 4.0
        #self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.data = {}
        self.texturesLoading = {}
        
        self.imageTextures = GLCache(0)
        self.maskTextures = {}
        self.texture = {}
        self.parent = parent
        self.setMouseTracking(True)
        self.dragging = False
        # subplot border in unit window pixels (independent of zoom)
        self.subplotBorder = 10
        self.selectedImage = None
        self.lastHoveredViewIndex = None
        self.stackWidth = 1;
        self.has_data = False

        self.loaderThread = ImageLoader(None,self)
        self.needsImage.connect(self.loaderThread.loadImage)
        self.loaderThread.imageLoaded.connect(self.generateTexture)
#        self.clearLoaderThread.connect(self.loaderThread.clear)

        self.imageLoader = QtCore.QThread()
        self.loaderThread.moveToThread(self.imageLoader)    
        self.imageLoader.start()

        self.loadingImageAnimationFrame = 0
        self.loadingImageAnimationTimer = QtCore.QTimer()
        self.loadingImageAnimationTimer.timeout.connect(self.incrementLoadingImageAnimationFrame)
        self.loadingImageAnimationTimer.start(100)

        self.setAcceptDrops(True)
#        self.time1 = time.time()

        self.slideshowTimer = QtCore.QTimer()
        self.slideshowTimer.setInterval(2000)
        self.slideshowTimer.timeout.connect(self.nextSlideRow)

    def stopThreads(self):
        while(self.imageLoader.isRunning()):
            self.imageLoader.quit()
            QtCore.QThread.sleep(1)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if(self.width() and self.height()):
            gluOrtho2D(0.0, self.width(), 0.0, self.height());  
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();

        self.circle_image = QtGui.QImage(100,100,QtGui.QImage.Format_ARGB32_Premultiplied)
        painter = QtGui.QPainter(self.circle_image)
        painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255,255,255)))
        painter.drawEllipse(0,0,100,100)
        painter.end()
        self.circle_texture = self.bindTexture(self.circle_image,GL_TEXTURE_2D,GL_RGBA,QtOpenGL.QGLContext.LinearFilteringBindOption)
        self.initShaders()
        self.initColormapTextures()
        
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        defaultMaskData = numpy.zeros((1,1),dtype=numpy.float32)
        glTexImage2D(GL_TEXTURE_2D, 0, OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB, 1, 1, 0, GL_ALPHA, GL_FLOAT, defaultMaskData);
        self.defaultMaskTexture = texture
    def initShaders(self):
        if not glUseProgram:
            print 'Missing Shader Objects!'
            sys.exit(1)
        self.makeCurrent()
        self.shader = compileProgram(
        compileShader('''
            void main()
            {
                //Transform vertex by modelview and projection matrices
                gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
 
                 // Forward current color and texture coordinates after applying texture matrix
                gl_FrontColor = gl_Color;
                gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
            }
        ''',GL_VERTEX_SHADER),
        compileShader('''
            uniform sampler2D cmap;
            uniform sampler2D data;
            uniform int norm;
            uniform float vmin;
            uniform float vmax;
            uniform float gamma;
            uniform int clamp;
            uniform sampler2D mask;
            uniform float maskedBits;
            void main()
            {
                vec2 uv = gl_TexCoord[0].xy;
                vec4 color = texture2D(data, uv);
                vec4 mcolor = texture2D(mask, uv);
                float scale = (vmax-vmin);
                float offset = vmin;

                // Apply Mask

                // Using a float for the mask will only work up to about 24 bits
                float maskBits = mcolor.a;
                // loop through the first 16 bits
                float bit = 1.0;
                if(maskBits > 0.0){
                    for(int i = 0;i<16;i++){
                        if(floor(mod(maskBits/bit,2.0)) == 1.0 && floor(mod(maskedBits/bit,2.0)) == 1.0){
                            color.a = 0.0;
                            gl_FragColor = color;
                            return;
                        }
                        bit = bit*2.0;
                    }
                }

                
                uv[0] = (color.a-offset);

                // Check for clamping 
                uv[1] = 0.0;
                if(uv[0] < 0.0){
                  if(clamp == 1){
                    uv[0] = 0.0;
                    gl_FragColor = texture2D(cmap,uv);
                    return;
                  }else{
                    color.a = 0.0;
                    gl_FragColor = color;
                    return;
                  }
                }
                if(uv[0] > scale){
                  if(clamp == 1){
                    uv[0] = 1.0;
                    gl_FragColor = texture2D(cmap,uv);
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
                 scale = pow(scale+1.0,gamma)-1.0;
                 uv[0] = (pow(uv[0]+1.0,gamma)-1.0)/scale;
                }
                color = texture2D(cmap,uv);
                gl_FragColor = color;
            }
        ''',GL_FRAGMENT_SHADER),
        )
    def initColormapTextures(self):
        n = 1024
        a = numpy.linspace(0.,1.,n)
        maps=[m for m in cm.datad if not m.endswith("_r")]
        mappable = cm.ScalarMappable()
        mappable.set_norm(colors.Normalize())
        self.colormapTextures = {}
        for m in maps:
            mappable.set_cmap(m)
            a_rgb = numpy.zeros(shape=(n,4),dtype=numpy.uint8)
            temp = mappable.to_rgba(a,None,True)[:,:]
            a_rgb[:,2] = temp[:,2]
            a_rgb[:,1] = temp[:,1]
            a_rgb[:,0] = temp[:,0]
            a_rgb[:,3] = 0xff
            self.colormapTextures[m] = glGenTextures(1)
            # I don't know how much of this I need
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBindTexture(GL_TEXTURE_2D, self.colormapTextures[m])
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, n,1, 0, GL_RGBA, GL_UNSIGNED_BYTE, a_rgb);

    def resizeGL(self, w, h):
        '''
        Resize the GL window 
        '''
        if(self.has_data):
            self.setStackWidth(self.stackWidth)
            self.updateGL()
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if(w and h):
            gluOrtho2D(0.0, w, 0.0, h);              
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity(); 

    def paintSelectedImageBorder(self,img_width,img_height):
        glPushMatrix()
        glShadeModel(GL_FLAT)
        glColor3f(1.0,1.0,1.0);
        glLineWidth(0.5/self.zoom)
        glBegin(GL_LINE_LOOP)
        glVertex3f (0, img_height, 0.0);
        v = 10.0/self.zoom
        vi = 0
        while(v < img_width):
            glVertex3f (v, img_height, 0.0);                            
            if(vi % 2):
                glColor3f(0.0,0.0,0.0);
            else:
                glColor3f(1.0,1.0,1.0);
            vi += 1
            v += 10.0/self.zoom 
        glColor3f(1.0,1.0,1.0);
        glVertex3f (img_width, img_height, 0.0);
        v = 10.0/self.zoom
        vi = 0
        while(v < img_height):
            glVertex3f (img_width, img_height-v, 0.0);                            
            if(vi % 2):
                glColor3f(0.0,0.0,0.0);
            else:
                glColor3f(1.0,1.0,1.0);
            vi += 1
            v += 10.0/self.zoom 
        glColor3f(1.0,1.0,1.0);
        glVertex3f (img_width, 0, 0.0);
        v = 10.0/self.zoom
        vi = 0
        while(v < img_width):
            glVertex3f (img_width-v, 0, 0.0);                            
            if(vi % 2):
                glColor3f(0.0,0.0,0.0);
            else:
                glColor3f(1.0,1.0,1.0);
            vi += 1
            v += 10.0/self.zoom 
        glColor3f(1.0,1.0,1.0);
        glVertex3f (0, 0, 0.0);
        v = 10.0/self.zoom
        vi = 0
        while(v < img_height):
            glVertex3f (0, v, 0.0);                            
            if(vi % 2):
                glColor3f(0.0,0.0,0.0);
            else:
                glColor3f(1.0,1.0,1.0);
            vi += 1
            v += 10.0/self.zoom 
        glEnd ();
        glPopMatrix()
    @QtCore.Slot()
    def incrementLoadingImageAnimationFrame(self):
        self.loadingImageAnimationFrame += 1
        self.updateGL()
    def drawRectangle(self,width,height,filled=True):
        if(filled):
            glBegin(GL_POLYGON)
        else:
            glBegin(GL_LINE_LOOP)
        glVertex3f (0, height, 0.0)
        glVertex3f (width, height, 0.0)
        glVertex3f (width, 0, 0.0)
        glVertex3f (0, 0, 0.0)
        glEnd()
    def drawDisk(self,center,radius,nsides=20,filled=True):
        if(filled):
            glEnable(GL_TEXTURE_2D)
            glBindTexture (GL_TEXTURE_2D, self.circle_texture);
            glBegin (GL_QUADS);
            glTexCoord2f (0.0, 1.0)
            glVertex3f (center[0]-radius, center[1]-radius, 0.0)
            glTexCoord2f (1.0, 1.0)
            glVertex3f (center[0]+radius, center[1]-radius, 0.0)
            glTexCoord2f (1.0, 0.0)
            glVertex3f (center[0]+radius, center[1]+radius, 0.0)
            glTexCoord2f (0.0, 0.0)
            glVertex3f (center[0]-radius, center[1]+radius, 0.0)
            glEnd ();
            glDisable(GL_TEXTURE_2D)
           # glPointSize(2*radius*self.zoom)
           # glEnable(GL_POINT_SMOOTH)
           # glBegin(GL_POINTS)
           # glVertex3f(center[0],center[1],0)
           # glEnd();
        else:
            glBegin(GL_LINE_LOOP)
            for side in range(0,nsides):
                angle = 2*math.pi*side/nsides
                glVertex3f(radius*math.cos(angle)+center[0],radius*math.sin(angle)+center[1],0)
            glEnd()
    def paintLoadingImage(self,img):
        frame = self.loadingImageAnimationFrame%24
        img_width = self.getImgWidth("scene",False)
        img_height = self.getImgHeight("scene",False)
        glPushMatrix()
        (x,y,z) = self.imageToScene(img,imagePos='BottomLeft',withBorder=False)
        glTranslatef(x,y,z)
        # Draw a ball in the center                
        path_radius = min(img_width,img_height)/10.0
        path_center = (img_width/2.0,6*img_height/10.0)
        radius = min(img_width,img_height)/40.0
        ndisks = 8
        for i in range(0,ndisks): 
            angle = math.pi/2.0-2*math.pi*i/ndisks
            if(i > frame/3):
                continue
            elif(i == frame/3):        
                glColor3f((frame%3+1)/4.0,(frame%3+1)/4.0,(frame%3+1)/4.0);
            else:
                glColor3f(3/4.0,3/4.0,3/4.0);
            self.drawDisk((path_center[0]+math.cos(angle)*path_radius,path_center[1]+math.sin(angle)*path_radius),radius,100)
        glColor3f(2/4.0,2/4.0,2/4.0);
        self.drawRectangle(img_width,img_height,filled=False)
        font = QtGui.QFont()
        metrics = QtGui.QFontMetrics(font);
        width = metrics.width("Loading...");
        ratio = (img_width*self.zoom/4.0)/width
        font.setPointSize(font.pointSize()*ratio)
        glColor3f(3/4.0,3/4.0,3/4.0);
        self.renderText(3*img_width/8.0,3*img_height/10.0,0.0,"Loading...",font);
        glPopMatrix()

    def paintImage(self,img):
        img_width = self.getImgWidth("scene",False)
        img_height = self.getImgHeight("scene",False)
        glPushMatrix()

        (x,y,z) = self.imageToScene(img,imagePos='BottomLeft',withBorder=False)
        glTranslatef(x,y,z)

        glUseProgram(self.shader)
        glActiveTexture(GL_TEXTURE0+1)
        data_texture_loc = glGetUniformLocation(self.shader, "data")
        glUniform1i(data_texture_loc,1)
        glBindTexture (GL_TEXTURE_2D, self.imageTextures[img]);

        glActiveTexture(GL_TEXTURE0+2)
        cmap_texture_loc = glGetUniformLocation(self.shader, "cmap")
        glUniform1i(cmap_texture_loc,2)
        glBindTexture (GL_TEXTURE_2D, self.colormapTextures[self.colormapText]);

        glActiveTexture(GL_TEXTURE0+3)
        loc = glGetUniformLocation(self.shader, "mask")
        glUniform1i(loc,3)
        if(img in self.maskTextures.keys()):
            glBindTexture (GL_TEXTURE_2D, self.maskTextures[img]);
        else:
            # If not mask is available load the default mask
            glBindTexture (GL_TEXTURE_2D, self.defaultMaskTexture);

        loc = glGetUniformLocation(self.shader, "vmin")
        glUniform1f(loc,self.normVmin)
        loc = glGetUniformLocation(self.shader, "vmax")
        glUniform1f(loc,self.normVmax)
        loc = glGetUniformLocation(self.shader, "gamma")
        glUniform1f(loc,self.normGamma)
        loc = glGetUniformLocation(self.shader, "norm")
        glUniform1i(loc,self.normScalingValue)
        loc = glGetUniformLocation(self.shader, "clamp")
        glUniform1i(loc,self.normClamp)
        loc = glGetUniformLocation(self.shader, "maskedBits")
        glUniform1f(loc,self.maskOutBits)

        glBegin (GL_QUADS);
        glTexCoord2f (0.0, 0.0);
        glVertex3f (0, img_height, 0.0);
        glTexCoord2f (1.0, 0.0);
        glVertex3f (img_width, img_height, 0.0);
        glTexCoord2f (1.0, 1.0);
        glVertex3f (img_width, 0, 0.0);
        glTexCoord2f (0.0, 1.0);
        glVertex3f (0, 0, 0.0);
        glEnd ();      
        # Activate again the original texture unit
        glActiveTexture(GL_TEXTURE0)  

        glUseProgram(0)
        if(self.indexProjector.imgToIndex(img) == self.lastHoveredViewIndex):
            glPushMatrix()
            glColor3f(1.0,1.0,1.0);
            glLineWidth(0.5/self.zoom)
            glBegin(GL_LINE_LOOP)
            glVertex3f (0, img_height, 0.0);
            glVertex3f (img_width, img_height, 0.0);
            glVertex3f (img_width, 0, 0.0);
            glVertex3f (0, 0, 0.0);
            glEnd ();
            glPopMatrix()
        elif(img == self.selectedImage):
            self.paintSelectedImageBorder(img_width,img_height)
        glPopMatrix()
    def paintGL(self):
        '''
        Drawing routine
        '''
#        self.time2 = time.time()
#        time3 = time.time()
#        print '%s function took %0.3f ms' % ("Non paintGL", (self.time2-self.time1)*1000.0)
        if(not self.isValid() or not self.isVisible()):
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # Set GL origin in the middle of the widget
        glTranslatef(self.width()/2.,self.height()/2.,0)
        # Apply user defined translation
        glTranslatef(self.translation[0],self.translation[1],0)
        # Apply user defined zoom
        glScalef(self.zoom,self.zoom,1.0);
        # Put GL origin on the top left corner of the widget
        glTranslatef(-(self.width()/self.zoom)/2.,(self.height()/self.zoom)/2.,0)
        if(self.has_data):
            if(self.data.getCXIFormat() == 2):
                img_width = self.getImgWidth("scene",False)
                img_height = self.getImgHeight("scene",False)
                visible = self.visibleImages()
                self.updateTextures(visible)
                for i,img in enumerate(set.intersection(set(self.imageTextures.keys()),set(visible),set(self.loaderThread.loadedImages()))):
                    self.paintImage(img)
                for img in (set(visible) - set(self.imageTextures.keys())):
                    self.paintLoadingImage(img)
                if len(visible) > 0:
                    # Set and emit current view index
                    self.visibleImg = self.windowToImage(self.getImgWidth("window",True)/2,self.getImgHeight("window",True)/2,0,False,False)
                    self.visibleImgChanged.emit(self.visibleImg,self.getNImages(),self.indexProjector.imgToIndex(self.visibleImg),self.getNImagesVisible())
#        glFlush()
#        time4 = time.time()
#        print '%s function took %0.3f ms' % ("paintGL", (time4-time3)*1000.0)
#        self.time1 = time.time()
    def addToStack(self,data):
        pass
    def loadStack(self,data):
        self.setData(data)
        self.zoomFromStackWidth()
    def loadImage(self,data):
        if(data.getCXIFormat() == 2):        
            self.setData(data)
            self.stackWidth = 1
            self.setStackWidth(self.stackWidth)
            self.clearTextures()
            self.updateGL()
        else:
            print "3D images not supported."
            sys.exit(-1)
    # will have to be changed when filter is implemented
    def getNImages(self):
        if self.data.isCXIStack():
            return self.data.shape[0]
        else:
            return 1
    def getNImagesVisible(self):
        if not self.data.isCXIStack():
            return 1
        else:
            if self.indexProjector.imgs == None:
                return self.getNImages()
            else:
                return len(self.indexProjector.imgs)
    def getImgHeight(self,reference,border=False):
        imgHeight = self.data.getCXIHeight()
        if border == True:
            imgHeight += self.subplotSceneBorder()
        if reference == "window":
            return imgHeight*self.zoom
        elif reference == "scene":
            return imgHeight 
    def getImgWidth(self,reference,border=False):
        imgWidth = self.data.getCXIWidth()
        if border == True:
            imgWidth += self.subplotSceneBorder()
        if reference == "window":
            return imgWidth*self.zoom
        elif reference == "scene":
            return imgWidth 
    def visibleImages(self):
        visible = []
        if(self.has_data is False):
            return visible

        top_left = self.windowToViewIndex(0,0,0,checkExistance=False,clip=False)
        bottom_right = self.windowToViewIndex(self.width(),self.height(),0,checkExistance=False,clip=False)

        top_left = self.viewIndexToCell(top_left)
        bottom_right = self.viewIndexToCell(bottom_right)
        nImagesVisible = self.getNImagesVisible()
        for x in numpy.arange(0,self.stackWidth):
            for y in numpy.arange(max(0,math.floor(top_left[1])),math.floor(bottom_right[1]+1)):
                viewIndex = y*self.stackWidth+x
                if(viewIndex < nImagesVisible):
                    img = self.indexProjector.indexToImg(viewIndex)
                    visible.append(img)
        return visible
    @QtCore.Slot(int)
    def generateTexture(self,img):
        # strange that this IF is needed for picking up rare events when generateTexture is called without the respective img present in imageData

        # FM: You're gonna have to give an explanation why you think this 
        # can happen. I suspect you're just maskerading another bug.
        # Meanwhile I'm going comment the code below

        # if img not in self.loaderThread.imageData.keys():
        #    return

        # If we already have the texture we just return
        if(img in self.imageTextures):
            return
        self.logger.debug("Generating texture %d"  % (img))
        imageData = self.loaderThread.imageData[img]
        maskData = self.loaderThread.maskData[img]
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB, imageData.shape[1], imageData.shape[0], 0, GL_ALPHA, GL_FLOAT, imageData);
        self.imageTextures[img] = texture

        if(maskData is not None):
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB, imageData.shape[1], imageData.shape[0], 0, GL_ALPHA, GL_FLOAT, maskData);
            self.maskTextures[img] = texture
        self.updateGL()
    def updateTextures(self,images):
        for img in images:
            if(img not in set.intersection(set(self.imageTextures.keys()),set(self.loaderThread.loadedImages()))):
                self.needsImage.emit(img)
            else:
                # Let the cache know we're using these images
                self.loaderThread.imageData.touch(img)

    # positive counts correspond to upwards movement of window / downwards movement of images
    def scrollBy(self,count=1,wrap=False):
        stepSize = 1
        translation = (0,stepSize*count)
        self.translateBy(translation,wrap)
    def scrollTo(self,translationY,wrap=False):
        translation = (0,translationY)
        self.translateTo(translation,wrap)
    def translateBy(self,translationBy,wrap=False):
        self.translateTo([self.translation[0]+translationBy[0],self.translation[1]+translationBy[1]],wrap)
    def translateTo(self,translation,wrap=False):
        self.translation[0] = translation[0]
        self.translation[1] = translation[1]
        self.clipTranslation()
        self.translationChanged.emit(self.translation[0],self.translation[1])
        self.updateGL()
    def clipTranslation(self,wrap=False):
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
    def maximumTranslation(self,withMargin = True):
        margin = self.subplotBorder*3
        img_height = self.getImgHeight("window",True)
        stack_height = math.ceil(float(self.getNImagesVisible())/self.stackWidth)*img_height
        if(withMargin):
            bottom_margin = max(0,stack_height+margin-self.height())
        else:
            bottom_margin = max(0,stack_height-self.height())
        return bottom_margin
    def minimumTranslation(self,withMargin = True):
        margin = self.subplotBorder*3
        if(withMargin):
            return -margin
        else:
            return 0;
        
    def wheelEvent(self, event):    
        settings = QtCore.QSettings()    
        t = -event.delta()*float(settings.value("scrollDirection"))
        self.translateBy([0,t])
        # Do not allow zooming
       # self.scaleZoom(1+(event.delta()/8.0)/360)
    def keyPressEvent(self, event):
        delta = self.width()/20
        img_height =  self.getImgHeight("window",True)
        stack_height = math.ceil(((self.getNImages()-0.0001)/self.stackWidth))*img_height
        if(event.key() == QtCore.Qt.Key_F):
            self.parent.statusBar.showMessage("Flaged "+str(self.indexProjector.indexToImg(self.hoveredViewIndex())),1000)
    def toggleSlideShow(self):
        if self.slideshowTimer.isActive():
            self.slideshowTimer.stop()
        else:
            self.slideshowTimer.start()
    def nextSlideRow(self):
        self.nextRow(wrap=True)
    def nextRow(self,wrap=False):
        self.changeRowBy(count=1,wrap=wrap)
    def previousRow(self,wrap=False):
        self.changeRowBy(count=-1,wrap=wrap)
    def changeRowBy(self,count=1,wrap=False):
        img_height = self.getImgHeight("window",True)
        t = count*img_height
        self.scrollBy(t,wrap)
    def browseToViewIndex(self,index):
        img_height =  self.getImgHeight("window",True)
        self.translateTo([0,img_height*int(numpy.floor(index/self.stackWidth))])
    def mouseReleaseEvent(self, event):
        self.dragging = False
        # Select even when draggin
        #if(event.button() == QtCore.Qt.LeftButton):
        #    self.selectedImage = self.indexProjector.indexToImg(self.lastHoveredViewIndex)
        #    self.imageSelected.emit(self.selectedImage)
        #    self.updateGL()
    def mousePressEvent(self, event):
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        x = pos.x()
        y = pos.y()
        img = self.windowToImage(x,y,0)
        (ix,iy) = self.windowToImageCoordinates(x,y,0)
        info = self.getPixelInfo(img,ix,iy)
        self.selectedImage = info["img"]
        self.pixelClicked.emit(info)
        self.dragStart = event.pos()
        self.dragPos = event.pos()
        self.dragging = True
        self.updateGL()
    def getPixelInfo(self,img,ix,iy):
        info = {}
        info["ix"] = ix
        info["iy"] = iy
        info["img"] = img
        info["viewIndex"] = self.indexProjector.imgToIndex(img)
        info["imageValue"] = self.loaderThread.imageData[img][iy,ix]
        if self.loaderThread.maskData[img] == None:
            info["maskValue"] = None
        else:
            info["maskValue"] = self.loaderThread.maskData[img][iy,ix]
        info["imageMin"] = numpy.min(self.loaderThread.imageData[img])
        info["imageMax"] = numpy.max(self.loaderThread.imageData[img])
        info["imageSum"] = numpy.sum(self.loaderThread.imageData[img])
        info["imageMean"] = numpy.mean(self.loaderThread.imageData[img])
        info["imageStd"] = numpy.std(self.loaderThread.imageData[img])
        return info
    def mouseMoveEvent(self, event):
        if(self.dragging):
            self.translateBy([0,-(event.pos()-self.dragPos).y()])
            self.clipTranslation()
            if(QtGui.QApplication.keyboardModifiers().__and__(QtCore.Qt.ControlModifier)):
               self.translateBy([0,(event.pos()-self.dragPos).x()])
            self.dragPos = event.pos()
            self.updateGL()
        ss = self.hoveredViewIndex()
        if(ss != self.lastHoveredViewIndex):
            self.lastHoveredViewIndex = ss
            self.updateGL()
    def checkSelectedSubplot(self):
        if(self.selectedImage not in self.data.keys()):
            self.selectedImage = None
            self.parent.datasetProp.recalculateSelectedSlice()
    def hoveredViewIndex(self):
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        viewIndex = self.windowToViewIndex(pos.x(),pos.y(),0)
        return viewIndex
    # Returns the scene position of the image corresponding to the index given
    # By default the coordinate of the TopLeft corner of the image is returned
    # By default the border is considered part of the image
    def imageToScene(self,imgIndex,imagePos='TopLeft',withBorder=True):
        img_width = self.getImgWidth("scene",True)
        img_height = self.getImgHeight("scene",True)
        (col,row) = self.imageToCell(imgIndex)
        x = img_width*col
        y = -img_height*row
        z = 0
        if(imagePos == 'TopLeft'):
            if(not withBorder):
                x += self.subplotSceneBorder()/2.
                y -= self.subplotSceneBorder()/2.
        elif(imagePos == 'BottomLeft'):
            y -= img_height
            if(not withBorder):
                x += self.subplotSceneBorder()/2.
                y += self.subplotSceneBorder()/2.
        elif(imagePos == 'BottomRight'):
            x += img_width
            y -= img_height
            if(not withBorder):
                x -= self.subplotSceneBorder()/2.
                y += self.subplotSceneBorder()/2.
        elif(imagePos == 'TopRight'):
            x += img_width
            if(not withBorder):
                x -= self.subplotSceneBorder()/2.
                y -= self.subplotSceneBorder()/2.
        elif(imagePos == 'Center'):
            x += img_width/2.
            y -= img_height/2.
        else:
            raise('Unknown imagePos: %s' % (imagePos))
        return (x,y,z)
    def viewIndexToScene(self,viewIndex,imagePosition="TopLeft",withBorder=True):
        img = self.indexProjector.indexToImg(viewIndex)
        return self.imageToScene(img,imagePosition,withBorder)
    # Returns the window position of the top left corner of the image corresponding to the index given
    def imageToWindow(self,imgIndex,imagePos='TopLeft',withBorder=True):
        (x,y,z) = self.imageToScene(imgIndex,imagePos,withBorder)
        return self.sceneToWindow(x,y,z)
    # Returns the window location of a given point in scene
    def sceneToWindow(self,x,y,z):
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT);
        (x,y,z) =  gluProject(x, y,z , model=modelview, proj=projection, view=viewport)
        return (x,viewport[3]-y,z)
    # Returns the x,y,z position of a particular window position
    def windowToScene(self,x,y,z):
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT);
        (x,y,z) =  gluUnProject(x, viewport[3]-y,z , model=modelview, proj=projection, view=viewport)
        return (x,y,z)
    # Returns pixel corrdinates in image
    def windowToImageCoordinates(self,x,y,z):
        (xw,yw,zw) = self.windowToScene(x,y,z)
        imageWidth = self.getImgWidth("scene",True)
        imageHeight = self.getImgHeight("scene",True)
        border = self.subplotSceneBorder()
        ix = int(round(xw%imageWidth - border/2.))
        iy = int(round(imageHeight - yw%imageHeight))
        return (ix,iy)
    # Returns the view index (index after sorting and filtering) of the image that is at a particular window location
    def windowToViewIndex(self,x,y,z,checkExistance=True, clip=True):
        if(self.has_data > 0):
            shape = (self.data.getCXIHeight(),self.data.getCXIWidth())
            modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT);
            (x,y,z) =  gluUnProject(x, viewport[3]-y,z , model=modelview, proj=projection, view=viewport)
            (x,y) = (int(numpy.floor(x/(self.data.getCXIWidth()+self.subplotSceneBorder()))),int(numpy.floor(-y/(self.data.getCXIHeight()+self.subplotSceneBorder()))))
            if(clip and (x < 0 or x >= self.stackWidth or y < 0)):
                return None            
            if(checkExistance and x + y*self.stackWidth >= self.getNImages()):
                return None
            return x + y*self.stackWidth
    # Returns the index of the image that is at a particular window location
    def windowToImage(self,x,y,z,checkExistance=True, clip=True):
        return self.indexProjector.indexToImg(self.windowToViewIndex(x,y,z,checkExistance,clip))
    # Returns the column and row from an view index
    def viewIndexToCell(self,index):
        if(index is None):
            return index
        else:
            return (index%self.stackWidth,int(index/self.stackWidth))
    # Returns the column and row from an imagex
    def imageToCell(self,img):
        if(img is None):
            return img
        else:
            viewIndex = self.indexProjector.imgToIndex(img)
            return self.viewIndexToCell(viewIndex)

    def scaleZoom(self,ratio):
        self.zoom *= ratio
        self.translation[0] *= ratio
        viewIndex = self.indexProjector.imgToIndex(self.visibleImg)
        self.browseToViewIndex(viewIndex)
    # Calculate the appropriate zoom level such that the windows will exactly fill the viewport widthwise
    def zoomFromStackWidth(self):
        width = self.stackWidth
        # We'll assume all images have the same size and the projection is isometric
        if(self.has_data is not True):
            return 1
        # Calculate the zoom necessary for the given stack width to fill the current viewport width
        new_zoom = float(self.width()-width*self.subplotBorder)/(self.data.getCXIWidth()*width)
        self.scaleZoom(new_zoom/self.zoom)
    def clear(self):
        self.setData()
        self.setMask()
        #self.setSortingIndices()
        self.loaderThread.clear()
#        self.clearLoaderThread.emit(0)
        self.clearTextures()
        self.updateGL()
    def clearTextures(self):
        glDeleteTextures(self.imageTextures.values())
        glDeleteTextures(self.maskTextures.values())
        self.imageTextures = GLCache(1024*1024*
                                     QtCore.QSettings().value("textureCacheSize"))
        self.maskTextures = {}
        self.loaderThread.clear()
#        self.clearLoaderThread.emit(0)
    def setStackWidth(self,width):
        self.stackWidth = width 
        # If there's no data just set the width and return
        if(self.has_data is not True):        
            return
        self.stackWidthChanged.emit(self.stackWidth)
        # Now change the width and zoom to match
        self.zoomFromStackWidth()            
    def stackSceneWidth(self,width):
        return 
    def subplotSceneBorder(self):
        return self.subplotBorder/self.zoom
    def refreshDisplayProp(self,datasetProp):
        if datasetProp != None:
            #self.loaderThread.setNorm(datasetProp["normScaling"],datasetProp["normVmin"],datasetProp["normVmax"],datasetProp["normClip"],datasetProp["normGamma"])
            #self.loaderThread.setColormap(datasetProp["colormapText"])
            self.normScaling = datasetProp["normScaling"]
            if(self.normScaling == 'lin'):
                self.normScalingValue = 0
            elif(self.normScaling == 'log'):
                self.normScalingValue = 1
            elif(self.normScaling == 'pow'):                
                self.normScalingValue = 2
            self.normVmin = datasetProp["normVmin"]
            self.normVmax = datasetProp["normVmax"]
            self.normGamma = datasetProp["normGamma"]
            if(datasetProp["normClamp"] == True):
                self.normClamp = 1
            else:
                self.normClamp = 0
            self.colormapText = datasetProp["colormapText"]
            self.setStackWidth(datasetProp["imageStackSubplotsValue"])
            self.indexProjector.setProjector(datasetProp["sortingDataset"],datasetProp["sortingInverted"],datasetProp["filterMask"])
        self.updateGL()
