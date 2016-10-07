from PIL import Image
from PIL import ImageDraw
import random
import numpy as np
import time
import flickr_interesting
import cairo
import sys
import copy
import array

U = random.uniform
I = random.randint

BF = 10 #border fraction
HEIGHT = WIDTH = 0
MAX_DIM = 200
MAX_THICKNESS=100
N_CURVES = 0

OPACITY_BASE = 0.2
OPACITY_OFFSET = 0.2

RED_MIN = 0.0
RED_MAX = 1.0
GREEN_MIN = 0.0
GREEN_MAX = 1.0
BLUE_MIN = 0.0
BLUE_MAX = 1.0

MUTATION_CURVE_GAIN_RATE = 10
MUTATION_CURVE_TRANS_RATE = 700
MUTATION_CURVE_LOSS_RATE = 1500
MUTATION_CURVE_COLOR_RATE = 1500
MUTATION_CURVE_WIDTH_RATE = 1500
MUTATION_POINT_TRANS_RATE = 1500

surface = None
ctx = None

def pil2cairo(im):
    """Transform a PIL Image into a Cairo ImageSurface."""

    assert sys.byteorder == 'little', 'We don\'t support big endian'
    if im.mode != 'RGBA':
        im = im.convert('RGBA')

    s = im.tobytes('raw', 'BGRA')
    a = array.array('B', s)
    dest = cairo.ImageSurface(cairo.FORMAT_ARGB32, im.size[0], im.size[1])
    ctx = cairo.Context(dest)
    non_premult_src_wo_alpha = cairo.ImageSurface.create_for_data(
        a, cairo.FORMAT_RGB24, im.size[0], im.size[1])
    non_premult_src_alpha = cairo.ImageSurface.create_for_data(
        a, cairo.FORMAT_ARGB32, im.size[0], im.size[1])
    ctx.set_source_surface(non_premult_src_wo_alpha)
    ctx.mask_surface(non_premult_src_alpha)
    return dest

def won_one_in(N):
    return random.randint(0, N)==1

def draw_curve(points,width,color,ctx):
    ctx.move_to (points[0][0], points[0][1],)    
    ctx.curve_to (points[1][0], points[1][1],points[2][0], points[2][1],points[3][0], points[3][1]) # Curve(x1, y1, x2, y2, x3, y3)
    ctx.set_line_width (width)
    ctx.set_source_rgba (color[0], color[1], color[2], color[3])
    ctx.stroke ()

class CandidateImage():
    def __init__(self):
        self.fitness = 10E17
        self.dirty = False
    def __repr__(self):
        return "<%d,%d>"%(self.fitness,self.curves.shape[0])
    def get_image(self,filname):
        ctx.set_source_rgb(0,0,0)
        ctx.rectangle(0,0,WIDTH,HEIGHT)
        ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(self.curves.shape[0]):
            draw_curve(self.curves[i], self.width[i], self.colors[i], ctx)
        surface.write_to_png(filname)
    def mutate(self):
        if won_one_in(MUTATION_CURVE_GAIN_RATE):# random.random()<MUTATION_CURVE_GAIN_RATE:
            width = np.random.rand(1)*MAX_THICKNESS
            self.width = np.append( self.width,width,axis=0)
            colors = np.asarray([U(RED_MIN,RED_MAX),U(GREEN_MIN,GREEN_MAX),U(BLUE_MIN,BLUE_MAX),U(OPACITY_BASE,OPACITY_BASE+OPACITY_OFFSET)])
            #colors = np.asarray([U(0,1),U(0,1),U(0,1),U(.1,.2)])#,
            #colors = np.asarray([0,0,1,.1])
            # a = U(0, 1)
            # colors = np.asarray([a,a,a,U(.3,.4)])#,
            self.colors = np.append( self.colors,[colors],axis=0)
            # curve = np.random.rand(4*2)
            # curve.shape = (1,4,2)
            # curve = np.multiply(curve, (1+2/BF)*np.asarray([WIDTH,HEIGHT]))
            # curve = curve - np.asarray([WIDTH,HEIGHT])/BF
            curve = np.asarray([[[U(-WIDTH/BF,WIDTH+WIDTH/BF),U(-HEIGHT/BF,HEIGHT+HEIGHT/BF)] for _ in range(4)]])
            self.curves = np.append( self.curves,curve,axis=0 )
            self.dirty = True
            # sys.stdout.write("+")
            # sys.stdout.flush()
        if won_one_in(MUTATION_CURVE_LOSS_RATE):
            if self.width.shape[0] > 1:
                # print self.curves,"a"
                delete_index  = random.randint(0,len(self.curves)-1)
                self.curves = np.delete(self.curves, delete_index,0 )
                # print self.curves,"b"
                self.width = np.delete(self.width,delete_index ,0)
                self.colors = np.delete(self.colors, delete_index,0 )
                self.dirty = True
                # sys.stdout.write("-")
                # sys.stdout.flush()
        for i in range(self.width.shape[0]):
            for c in range(self.curves[i].shape[0]):
                if won_one_in(MUTATION_POINT_TRANS_RATE):
                    self.curves[i][c]=self.curves[i][c]+[U(-WIDTH/MAX_DIM,WIDTH/MAX_DIM),U(-HEIGHT/MAX_DIM,HEIGHT/MAX_DIM)]
                    self.dirty = True
                if won_one_in(MUTATION_POINT_TRANS_RATE):
                    self.curves[i][c]=self.curves[i][c]+[U(-WIDTH/100,WIDTH/100),U(-HEIGHT/100,HEIGHT/100)]
                    self.dirty = True
                if won_one_in(MUTATION_POINT_TRANS_RATE):
                    self.curves[i][c]=self.curves[i][c]+[U(-WIDTH/10,WIDTH/10),U(-HEIGHT/10,HEIGHT/10)]
                    self.dirty = True
            if won_one_in(MUTATION_CURVE_TRANS_RATE):
                self.curves[i]=self.curves[i]+[U(-WIDTH/MAX_DIM,WIDTH/MAX_DIM),U(-HEIGHT/MAX_DIM,HEIGHT/MAX_DIM)]
                self.dirty = True
            if won_one_in(MUTATION_CURVE_TRANS_RATE):
                self.curves[i]=self.curves[i]+[U(-WIDTH/100,WIDTH/100),U(-HEIGHT/100,HEIGHT/100)]
                self.dirty = True
            if won_one_in(MUTATION_CURVE_TRANS_RATE):
                self.curves[i]=self.curves[i]+[U(-WIDTH/10,WIDTH/10),U(-HEIGHT/10,HEIGHT/10)]
                self.dirty = True
            if won_one_in(MUTATION_CURVE_COLOR_RATE):
                self.colors[i][0] = U(RED_MIN,RED_MAX)
                self.dirty = True
                # sys.stdout.write("R")
                # sys.stdout.flush()
            if won_one_in(MUTATION_CURVE_COLOR_RATE):
                self.colors[i][1] = U(GREEN_MIN,GREEN_MAX)
                self.dirty = True
                # sys.stdout.write("G")
                # sys.stdout.flush()
            if won_one_in(MUTATION_CURVE_COLOR_RATE):
                self.colors[i][2] = U(BLUE_MIN,BLUE_MAX)
                self.dirty = True
                # sys.stdout.write("B")
                # sys.stdout.flush()
            if won_one_in(MUTATION_CURVE_COLOR_RATE):
                self.colors[i][3] = U(OPACITY_BASE,OPACITY_BASE+OPACITY_OFFSET)
                self.dirty = True
                # sys.stdout.write("A")
                # sys.stdout.flush()
            if won_one_in(MUTATION_CURVE_WIDTH_RATE):
                self.width[i] = U(0,1)*MAX_THICKNESS
                self.dirty = True
                # sys.stdout.write("W")
                # sys.stdout.flush()

    def compute_matrix_fitness(self,truth):
        ctx.set_source_rgb(0,0,0)
        ctx.rectangle(0,0,WIDTH,HEIGHT)
        ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(self.curves.shape[0]):
            draw_curve(self.curves[i], self.width[i], self.colors[i], ctx)
        buf = surface.get_data()
        self.matrix = np.frombuffer(buf, np.uint8)
        self.matrix.shape = (HEIGHT, WIDTH, 4)
        diff=truth-self.matrix
        self.fitness = np.sum(diff*diff)
        # Image.fromarray(self.matrix).save(repr(random.random())+".jpg")
        return self
    def newborn(self,truth):
        self.width = np.random.rand(N_CURVES)*MAX_THICKNESS
        self.colors = np.random.rand(N_CURVES*4).reshape((N_CURVES,4))
        self.curves = np.random.rand(N_CURVES*4*2)
        self.curves.shape = (N_CURVES,4,2)
        # self.curves = np.multiply(self.curves, (1+2/BF)*np.asarray([WIDTH,HEIGHT]))
        # self.curves = self.curves - np.asarray([WIDTH,HEIGHT])/BF
        self.compute_matrix_fitness(truth)
        return self

if __name__ == '__main__':
    #flickr_interesting.save_image()

    iteration = generation = mutation = 0

    truth = Image.open(sys.argv[1]).convert('RGB')
    WIDTH,HEIGHT = truth.size
    ratio = min(MAX_DIM*1.0/WIDTH, MAX_DIM*1.0/HEIGHT)
    WIDTH = int(WIDTH*ratio)
    HEIGHT = int(HEIGHT * ratio)
    truth.thumbnail((WIDTH,HEIGHT), Image.ANTIALIAS)
    image_surface = pil2cairo(truth)

    #image_surface = cairo.ImageSurface.create_from_png(".truth.png")
    WIDTH = image_surface.get_width()
    HEIGHT = image_surface.get_height()
    buf = image_surface.get_data()
    truth = np.frombuffer(buf, np.uint8)
    print truth.size,HEIGHT,WIDTH
    truth.shape = ( HEIGHT,WIDTH, 4)
    image_surface.write_to_png("testtruth.png")

    surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, WIDTH,HEIGHT)
    ctx = cairo.Context (surface)
    best_image = CandidateImage().newborn(truth)

    best_image.get_image("out.png")

    print "generation strated"
    print truth[0,0],truth[0,HEIGHT/2],truth[0,HEIGHT-1]
    print best_image.matrix[0,0],best_image.matrix[0,HEIGHT/2],best_image.matrix[0,HEIGHT-1]
    while True:
        iteration+=1
        new_image = copy.deepcopy(best_image)
        new_image.mutate()
        if new_image.dirty:
            mutation += 1
            new_image.compute_matrix_fitness(truth)
            if new_image.fitness < best_image.fitness:
                generation +=1
                best_image = new_image
                best_image.dirty = False
                print "\n","G%d"%generation,best_image,time.asctime(),
                # best_image.matrix = best_image.matrix[:,:,:-1]
                # best_image.matrix = best_image.matrix[:,:,::-1]
                try:
                    best_image.get_image("out.png")
                except Exception, e:
                    pass                
            # if mutation%2000==0:
            #     new_image.get_image().save("sample.png")
                #print truth[0][0],best_image.matrix[0][0]
        #sys.stdout.write(".")
