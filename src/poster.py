from chord import Guitar
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
from PIL import Image
guitar = Guitar()

def get_shape(n):
    if n == 1:
        return 1,1
    elif n == 2:
        return 1,2
    elif n < 5:
        return 2,2
    elif n < 7:
        return 2,3
    elif n < 10:
        return 3,3
    else:
        return int(np.ceil(n/4)), 4 if n >=4 else n

for folder in os.listdir('figs'):
    folder_path = os.path.join('figs', folder)
    if os.path.isdir(folder_path) and folder != 'posters':
        n = 0
        for fig in os.listdir(folder_path):
            fig_path = os.path.join(folder_path, fig)
            if os.path.isfile(fig_path):
                if fig_path[-4:] == '.png':
                    n += 1
        
        rows, cols = get_shape(n)
        
        img = np.zeros((1200*rows, 1200*cols, 4))
        i = 0
        for fig in os.listdir(folder_path):
            fig_path = os.path.join(folder_path, fig)
            if os.path.isfile(fig_path):
                if fig_path[-4:] == '.png':
                    r = i // cols
                    c = i % cols
                    img[r*1200:(r+1)*1200, c*1200:(c+1)*1200, :] = plt.imread(fig_path)
                    i += 1
        #print((img * 255).astype(np.uint8))
        im = Image.fromarray((img * 255).astype(np.uint8))
        im.save('figs/posters/' + folder + '.png')