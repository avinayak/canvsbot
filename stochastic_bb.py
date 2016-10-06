from PIL import Image
from PIL import ImageDraw
import random
import numpy as np
import time
import flickr_interesting
import cairo
import sys
import copy

U = random.uniform

BORDER_FRACTION = 2
HEIGHT = 100
MAX_HEIGHT = 500
MAX_POPULATION = 200
MAX_THICKNESS=100
MAX_WIDTH = 500
N_CHILD = 9*MAX_POPULATION/10
N_CURVES = 0
WIDTH = 100

MUTATION_CURVE_GAIN_FACTOR = 700
MUTATION_CURVE_LOSS_FACTOR = 1500
MUTATION_CURVE_TRANSLATION_FACTOR = 0
MUTATION_CURVE_COLOR_RED_FACTOR = 0
MUTATION_CURVE_COLOR_BLUE_FACTOR = 0
MUTATION_CURVE_COLOR_GREEN_FACTOR = 0
MUTATION_CURVE_COLOR_ALPHA_FACTOR = 0

surface = None
ctx = None

def won_one_in(N):
    return random.randint(0, N)==1

def draw_curve(points,width,color,ctx):
    try:
        ctx.move_to (points[0][0], points[0][1],)
    except Exception, e:
        print points,"woot"
        exit()
    
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
    def get_image(self):
        return Image.fromarray(self.matrix)
    def mutate(self):
        if won_one_in(MUTATION_CURVE_GAIN_FACTOR):# random.random()<MUTATION_CURVE_GAIN_FACTOR:
            width = np.random.rand(1)*MAX_THICKNESS
            self.width = np.append( self.width,width,axis=0)
            colors = np.asarray([U(0,1),U(0,1),U(0,1),U(.3,.4)])
            self.colors = np.append( self.colors,[colors],axis=0)
            curve = np.random.rand(4*2)
            curve.shape = (1,4,2)
            curve = np.multiply(curve, (1+2/BORDER_FRACTION)*np.asarray([WIDTH,HEIGHT]))
            curve = curve - np.asarray([WIDTH,HEIGHT])/BORDER_FRACTION
            self.curves = np.append( self.curves,curve,axis=0 )
            self.dirty = True
        if won_one_in(MUTATION_CURVE_LOSS_FACTOR):
            if len(self.width) > 2:
                self.curves = np.delete(self.curves, random.randint(0,len(self.curves)-1))
                self.width = np.delete(self.width, random.randint(0,len(self.width)-1))
                self.colors = np.delete(self.colors, random.randint(0,len(self.colors)-1))
                self.dirty = True

    def compute_matrix_fitness(self,truth):
        ctx.set_source_rgb(0,0,0)
        ctx.rectangle(0,0,HEIGHT,WIDTH)
        ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(self.curves.shape[0]):
            draw_curve(self.curves[i], self.width[i], self.colors[i], ctx)
        buf = surface.get_data()
        self.matrix = np.frombuffer(buf, np.uint8)
        self.matrix.shape = (WIDTH, HEIGHT, 4)
        diff=truth-self.matrix
        self.fitness = np.sum(diff*diff)
        # Image.fromarray(self.matrix).save(repr(random.random())+".jpg")
        return self
    def newborn(self,truth):
        self.width = np.random.rand(N_CURVES)*MAX_THICKNESS
        self.colors = np.random.rand(N_CURVES*4).reshape((N_CURVES,4))
        self.curves = np.random.rand(N_CURVES*4*2)
        self.curves.shape = (N_CURVES,4,2)
        self.curves = np.multiply(self.curves, (1+2/BORDER_FRACTION)*np.asarray([WIDTH,HEIGHT]))
        self.curves = self.curves - np.asarray([WIDTH,HEIGHT])/BORDER_FRACTION
        self.compute_matrix_fitness(truth)
        return self

if __name__ == '__main__':
    # flickr_interesting.save_image()
    truth = Image.open('me.jpg').convert('RGB')
    WIDTH,HEIGHT = truth.size
    ratio = min(MAX_WIDTH*1.0/WIDTH, MAX_HEIGHT*1.0/HEIGHT)
    WIDTH = int(WIDTH*ratio)
    HEIGHT = int(HEIGHT * ratio)
    truth.thumbnail((WIDTH,HEIGHT), Image.ANTIALIAS)
    truth = np.asarray(truth)
    WIDTH,HEIGHT,_ = truth.shape
    tffs = np.full(WIDTH*HEIGHT,255)
    tffs.shape = (WIDTH,HEIGHT,1)
    truth = np.uint8(np.concatenate((truth,tffs),axis=2))
    surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, WIDTH,HEIGHT)
    ctx = cairo.Context (surface)
    best_image = CandidateImage().newborn(truth)
    
    while True:
        new_image = copy.deepcopy(best_image)
        new_image.mutate()
        if new_image.dirty:
            new_image.compute_matrix_fitness(truth)
            if new_image.fitness < best_image.fitness:
                best_image = new_image
                best_image.dirty = False
                print best_image,time.asctime()
                best_image.get_image().save("output.png")
        #sys.stdout.write(".")
