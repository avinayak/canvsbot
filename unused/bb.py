from PIL import Image
from PIL import ImageDraw
import random
import numpy as np
import bezier
import time
import flickr_interesting

BORDER_FRAC = 200
COLORSET = 256
HEIGHT = 1000
MAX_BEZIER_ORDER = 2
MAX_CURVE_RADIUS = 100
MAX_POPULATION = 150
MAX_THICKNESS = 7
MUTATION_FACTOR = 0.01
N_CHILD = 9*MAX_POPULATION/10
N_COLORS = 100
N_CURVES = 2000
WIDTH = 1000

MAX_WIDTH = 500
MAX_HEIGHT = 500

def draw_bezier(xyz,thick,col,draw):
    if len(xyz)>2:
        ts = [t/100.0 for t in range(101)]
        bz = bezier.make_bezier(xyz)
        points = bz(ts)
        for p in range(len(points)-1):
            draw.line([points[p],points[p+1]],fill=col,width=thick)
    else:
        draw.line([xyz[0],xyz[1]],fill=col,width=thick)

def monte_carlo_dartboard(pool):
    dartboard = [0]
    sum = 0
    for x in pool:
        sum+=x.fitness
        dartboard.append(sum)
    return (sum,dartboard)

def try_darts(sum,dartboard):
    pick = random.random()*sum
    i=0
    while pick>dartboard[i]:
        i+=1
    i-=1
    return i

def cross(c1,c2,truth):
    child = CandidateImage()
    for i in range(N_CURVES):
        if random.random()>MUTATION_FACTOR:
            child.curves.append(random.choice([c1,c2]).curves[i])
        else:
            curve={}
            max_len=random.randrange(2,MAX_CURVE_RADIUS)
            curve["points"] = []
            origin = (random.randrange(-WIDTH/BORDER_FRAC,WIDTH+WIDTH/BORDER_FRAC),random.randrange(-HEIGHT/BORDER_FRAC,HEIGHT+HEIGHT/BORDER_FRAC))
            for j in range(random.randrange(1,MAX_BEZIER_ORDER)):
                end = (origin[0]+random.uniform(-MAX_CURVE_RADIUS,MAX_CURVE_RADIUS),origin[1]+random.uniform(-MAX_CURVE_RADIUS,MAX_CURVE_RADIUS))
                curve["points"].append(end)
            curve["points"].append(origin)
            #curve["points"] = [(random.randrange(-WIDTH/BORDER_FRAC,WIDTH+WIDTH/BORDER_FRAC),random.randrange(-HEIGHT/BORDER_FRAC,HEIGHT+HEIGHT/BORDER_FRAC)) for _ in range(random.randrange(2,MAX_BEZIER_ORDER))]
            curve["width"] = random.randrange(1,MAX_THICKNESS)
            curve["color"] = int((COLORSET/N_COLORS+1)*random.randrange(0,N_COLORS))
            child.curves.append(curve)
    child.curves.sort(key=lambda x:x["width"], reverse=True)
    child.fitness = child.get_fitness(truth)
    return child

class CandidateImage():
    curves = []
    fitness = 0
    def __init__(self):
        self.curves=[]
        self.fitness = 0
    def get_image(self):
        im = Image.new('L', (WIDTH, HEIGHT),(255))
        for i in range(N_CURVES):
            draw = ImageDraw.Draw(im)
            draw_bezier(self.curves[i]["points"],self.curves[i]["width"],self.curves[i]["color"], draw)
        return im

    def random(self,truth):
        for _ in range(N_CURVES):
            curve={}
            max_len=random.randrange(2,MAX_CURVE_RADIUS)
            curve["points"] = []
            origin = (random.randrange(-WIDTH/BORDER_FRAC,WIDTH+WIDTH/BORDER_FRAC),random.randrange(-HEIGHT/BORDER_FRAC,HEIGHT+HEIGHT/BORDER_FRAC))
            for j in range(random.randrange(1,MAX_BEZIER_ORDER)):
                end = (origin[0]+random.uniform(-MAX_CURVE_RADIUS,MAX_CURVE_RADIUS),origin[1]+random.uniform(-MAX_CURVE_RADIUS,MAX_CURVE_RADIUS))
                curve["points"].append(end)
            curve["points"].append(origin)
            #curve["points"] = [(random.randrange(-WIDTH/BORDER_FRAC,WIDTH+WIDTH/BORDER_FRAC),random.randrange(-HEIGHT/BORDER_FRAC,HEIGHT+HEIGHT/BORDER_FRAC)) for _ in range(random.randrange(2,MAX_BEZIER_ORDER))]
            curve["width"] = random.randrange(1,MAX_THICKNESS)
            curve["color"] = int((COLORSET/N_COLORS+1)*random.randrange(0,N_COLORS))
            self.curves.append(curve)
        self.curves.sort(key=lambda x:x["width"], reverse=True)
        self.fitness = self.get_fitness(truth)
        return self

    def get_fitness(self,truth):
        np_candidate = np.asarray(self.get_image())
        np_truth = np.asarray(truth)
        return (np.sum(np.absolute(np_truth-np_candidate))/(WIDTH*HEIGHT*255.0))

    def __repr__(self):
        return "<%2.10f>"%self.fitness

if __name__ == '__main__':
    flickr_interesting.save_image()
    truth = Image.open('image.jpg').convert('L')
    WIDTH,HEIGHT = truth.size
    ratio = min(MAX_WIDTH*1.0/WIDTH, MAX_HEIGHT*1.0/HEIGHT)
    WIDTH = int(WIDTH*ratio)
    HEIGHT = int(HEIGHT * ratio)
    truth.thumbnail((WIDTH,HEIGHT), Image.ANTIALIAS)
    best_image = CandidateImage()
    pool = []
    for _ in range(MAX_POPULATION):
        pool.append(CandidateImage().random(truth))
    print "Firstborns are Raised.."
    while True:
        pool.sort(key=lambda x:x.fitness, reverse=True)
        for i in range(N_CHILD):
            sum,dartboard = monte_carlo_dartboard(pool)
            c1 = pool[try_darts(sum, dartboard)]
            c2 = pool[try_darts(sum, dartboard)]
            ch = cross(c1,c2,truth)
            pool[-i]=ch
        if pool[0].fitness > best_image.fitness:
            best_image = pool[0]
            print best_image,time.asctime()
            best_image.get_image().save("out.png")
            #best_image.get_image().save("GA"+repr(best_image.fitness)[2:10]+".png")
            # if p<4:
            #     p+=1
            # else:
            #     exit()
    #fitnesses = list(map((lambda x:x.get_fitness(truth)),pool))
    # print pool
    # cim.save('out.png')
