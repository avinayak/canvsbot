from PIL import Image
from PIL import ImageDraw
import random
import numpy as np
import time
import flickr_interesting
import cairo

WIDTH = 100
HEIGHT = 100
MAX_WIDTH = 500
MAX_HEIGHT = 500
N_CURVES = 100
MAX_POPULATION = 150

pat = cairo.LinearGradient (0.0, 0.0, 0.0, 0.0)
pat.add_color_stop_rgba (1, .5, 0, 0, 1)
surface = None

class CandidateImage():
	curves = []
	fitness = 0
	def __init__(self):
		self.curves=[]
		self.fitness = 0
	def newborn(self,truth):
		self.curves = np.random.rand(N_CURVES*4*2)
		self.curves.shape = (N_CURVES,4,2)
		return self

if __name__ == '__main__':
	#flickr_interesting.save_image()
	truth = Image.open('image.jpg').convert('RGB')
	WIDTH,HEIGHT = truth.size
	ratio = min(MAX_WIDTH*1.0/WIDTH, MAX_HEIGHT*1.0/HEIGHT)
	WIDTH = int(WIDTH*ratio)
	HEIGHT = int(HEIGHT * ratio)
	truth.thumbnail((WIDTH,HEIGHT), Image.ANTIALIAS)
	truth = np.asarray(truth)
	WIDTH,HEIGHT,_ = truth.shape
	zeroes = np.zeros(WIDTH*HEIGHT)
	zeroes.shape = (WIDTH,HEIGHT,1)
	truth = np.concatenate((zeroes,truth),axis=2)

	best_image = CandidateImage()
	pool = []
	for _ in range(MAX_POPULATION):
		pool.append(CandidateImage().newborn(truth))
	print "Firstborns are Raised.."


