from PIL import Image
from PIL import ImageDraw
import random
import numpy as np
import time
import flickr_interesting
import cairo
import sys
import copy

BORDER_FRACTION = 2
HEIGHT = 100
MAX_HEIGHT = 500
MAX_POPULATION = 200
MAX_THICKNESS=10
MAX_WIDTH = 500
N_CHILD = 9*MAX_POPULATION/10
N_CURVES = 2
WIDTH = 100

MUTATION_CURVE_GAIN_FACTOR = 0.01
MUTATION_CURVE_LOSS_FACTOR = 0.005
MUTATION_CURVE_TRANSLATION_FACTOR = 0
MUTATION_CURVE_COLOR_RED_FACTOR =0
MUTATION_CURVE_COLOR_BLUE_FACTOR = 0
MUTATION_CURVE_COLOR_GREEN_FACTOR = 0
MUTATION_CURVE_COLOR_ALPHA_FACTOR = 0

pat = cairo.LinearGradient (0.0, 0.0, 0.0, 0.0)
pat.add_color_stop_rgba (1, .5, 0, 0, 1)
surface = None
ctx = None
# scaler_w = np.concatenate((np.full((N_CURVES,4,1),10),np.full((N_CURVES,4,1),12)),axis=2)
# print scaler_w.shape

def monte_carlo_dartboard(pool):
    dartboard = [0]
    sum = 0
    for x in pool:
        sum+=(-1*x.fitness)
        dartboard.append(sum)
    #print dartboard
    return (sum,dartboard)

def try_darts(sum,dartboard):
    pick = random.random()*sum
    i=0
    while pick<dartboard[i]:
        i+=1
    i-=1
    #print i
    return i

def draw_curve(points,width,color,ctx):
	ctx.move_to (points[0][0], points[0][1],)
	ctx.curve_to (points[1][0], points[1][1],points[2][0], points[2][1],points[3][0], points[3][1]) # Curve(x1, y1, x2, y2, x3, y3)
	ctx.set_line_width (width)
	ctx.set_source_rgba (color[0], color[1], color[2], color[3]) # Solid color
	ctx.stroke ()

def cross(c1,c2,truth):
    child = CandidateImage()
    child.curves = np.empty((0,4,2))
    child.width = np.empty((0))
    child.colors = np.empty((0,4))
    curve_count = max(c2.curves.shape[0],c1.curves.shape[0])
    for i in range(curve_count):
    	ch = random.choice([c1,c2])
    	if random.random()>MUTATION_CURVE_LOSS_FACTOR: #skip a gene
	    	if i<ch.curves.shape[0]:
		        child.curves = np.append( child.curves,[ch.curves[i]],axis=0 )
		        child.width = np.append( child.width,[ch.width[i]],axis=0)
		        child.colors = np.append( child.colors,[ch.colors[i]],axis=0)
		elif random.random()<MUTATION_CURVE_TRANSLATION_FACTOR:
			if i<ch.curves.shape[0]:child.curves[i] = child.curves[i]*(1+[random.uniform(-1,2),random.uniform(-1,1)])
		elif random.random()<MUTATION_CURVE_COLOR_RED_FACTOR:
			if i<ch.curves.shape[0]:child.colors[i][0] = random.random()
		elif random.random()<MUTATION_CURVE_COLOR_GREEN_FACTOR:
			if i<ch.curves.shape[0]:child.colors[i][1] = random.random()
		elif random.random()<MUTATION_CURVE_COLOR_BLUE_FACTOR:
			if i<ch.curves.shape[0]:child.colors[i][2] = random.random()
		elif random.random()<MUTATION_CURVE_COLOR_ALPHA_FACTOR:
			if i<ch.curves.shape[0]:child.colors[i][3] = random.random()
		# elif random.random()<MUTATION_CURVE_COLOR_RED_FACTOR:
		# 	if i<ch.curves.shape[0]:ch.
		
    if random.random()<MUTATION_CURVE_GAIN_FACTOR:
    	width = np.random.rand(1)*MAX_THICKNESS
    	child.width = np.append( child.width,width,axis=0)
    	colors = np.random.rand(4)
    	child.colors = np.append( child.colors,[colors],axis=0)
    	curve = np.random.rand(4*2)
    	curve.shape = (1,4,2)
    	curve = np.multiply(curve, (1+2/BORDER_FRACTION)*np.asarray([WIDTH,HEIGHT]))
    	curve = curve - np.asarray([WIDTH,HEIGHT])/BORDER_FRACTION
    	child.curves = np.append( child.curves,curve,axis=0 )
    # child.curves.sort(key=lambda x:xhil, reverse=True)
    child.compute_matrix_fitness(truth)
    return child

class CandidateImage():
	def __init__(self):
		self.fitness = 99999999999999999
	def __repr__(self):
	    return "<%d,%d>"%(self.fitness,self.curves.shape[0])
	def get_image(self):
		return Image.fromarray(self.matrix)
	def compute_matrix_fitness(self,truth):
		ctx.set_source_rgb(1,1,1)
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
	truth = Image.open('image.jpg').convert('RGB')
	WIDTH,HEIGHT = truth.size
	ratio = min(MAX_WIDTH*1.0/WIDTH, MAX_HEIGHT*1.0/HEIGHT)
	WIDTH = int(WIDTH*ratio)
	HEIGHT = int(HEIGHT * ratio)
	truth.thumbnail((WIDTH,HEIGHT), Image.ANTIALIAS)
	truth = np.asarray(truth)
	WIDTH,HEIGHT,_ = truth.shape
	zeroes = np.full(WIDTH*HEIGHT,255)
	zeroes.shape = (WIDTH,HEIGHT,1)
	truth = np.uint8(np.concatenate((truth,zeroes),axis=2))
	surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, HEIGHT, WIDTH)
	ctx = cairo.Context (surface)
	best_image = CandidateImage()
	pool = []
	for _ in range(MAX_POPULATION):
		pool.append(CandidateImage().newborn(truth))
	print "Firstborns are Raised.."
	while True:
	    pool.sort(key=lambda x:x.fitness, reverse=False)
	    original_pool = copy.deepcopy(pool)
	    for i in range(1,N_CHILD+1):
	        sum,dartboard = monte_carlo_dartboard(original_pool)
	        c1 = original_pool[try_darts(sum, dartboard)]
	        c2 = original_pool[try_darts(sum, dartboard)]
	        ch = cross(c1,c2,truth)
	        pool[-i]=ch
	    if pool[0].fitness < best_image.fitness:
	        best_image = pool[0]
	        print best_image,time.asctime()
	        best_image.get_image().save("fout.png")
	    #sys.stdout.write(".")


