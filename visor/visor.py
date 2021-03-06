#! /usr/local/bin/python3

import sys
import os
import time
import cv2 # install cv3, python3:  http://seeb0h.github.io/howto/howto-install-homebrew-python-opencv-osx-el-capitan/
# add to profile: export PYTHONPATH=$PYTHONPATH:/usr/local/Cellar/opencv3/3.2.0/lib/python3.6/site-packages/
import numpy as np
import argparse
import torch
import torch.nn as nn
import torchvision.models as models 
import torchvision.transforms as transforms

def define_and_parse_args():
    # argument Checking
    parser = argparse.ArgumentParser(description="Visor Demo")
    # parser.add_argument('network', help='CNN model file')
    parser.add_argument('categories', help='text file with categories')
    parser.add_argument('-i', '--input',  type=int, default='0', help='camera device index or file name, default 0')
    parser.add_argument('-s', '--size', type=int, default=224, help='network input size')
    # parser.add_argument('-S', '--stat', help='stat.txt file')
    return parser.parse_args()

def cat_file():
    # load classes file
    categories = []
    if hasattr(args, 'categories') and args.categories:
        try:
            f = open(args.categories, 'r')
            for line in f:
                cat = line.split(',')[0].split('\n')[0]
                if cat != 'classes':
                    categories.append(cat)
            f.close()
            print('Number of categories:', len(categories))
        except:
            print('Error opening file ' + args.categories)
            quit()
    return categories


print("Visor demo e-Lab")
xres = 640
yres = 480
args = define_and_parse_args()
categories = cat_file() # load category file
font = cv2.FONT_HERSHEY_SIMPLEX

# setup camera input:
cam = cv2.VideoCapture(args.input)
cam.set(3, xres)
cam.set(4, yres)

# load CNN model:
# model = torch.load(args.network)
model = models.resnet18(pretrained=True)
model.eval()
# print model
softMax = nn.Softmax() # to get probabilities out of CNN

# image pre-processing functions:
transformsImage = transforms.Compose([
        # transforms.ToPILImage(),
        # transforms.Scale(256),
        # transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]) # needed for pythorch ZOO models on ImageNet (stats)
    ])

while True:
    startt = time.time()
    ret, frame = cam.read()
    if not ret:
        break

    if xres > yres:
        frame = frame[:,int((xres - yres)/2):int((xres+yres)/2),:]
    else:
        frame = frame[int((yres - xres)/2):int((yres+xres)/2),:,:]
    
    pframe = cv2.resize(frame, dsize=(args.size, args.size))
    
    # prepare and normalize frame for processing:
    pframe = np.swapaxes(pframe, 0, 2)
    pframe = np.expand_dims(pframe, axis=0)
    pframe = transformsImage(pframe)
    pframe = torch.autograd.Variable(pframe) # turn Tensor to variable required for pytorch processing
    
    # process via CNN model:
    output = model(pframe)
    if output is None:
        print('no output from CNN model file')
        break

    output = softMax(output) # convert CNN output to probabilities
    output = output.data.numpy()[0] # get data from pytorch Variable, [0] = get vector from array
    
    # process output and print results:
    order = output.argsort()
    last = len(categories)-1
    text = ''
    for i in range(min(5, last+1)):
        text += categories[order[last-i]] + ' (' + '{0:.2f}'.format(output[order[last-i]]*100) + '%) '

    # overlay on GUI frame
    cv2.putText(frame, text, (10, yres-20), font, 0.5, (255, 255, 255), 1)
    cv2.imshow('win', frame)

    endt = time.time()
    # sys.stdout.write("\r"+text+"fps: "+'{0:.2f}'.format(1/(endt-startt))) # text output 
    sys.stdout.write("\rfps: "+'{0:.2f}'.format(1/(endt-startt)))
    sys.stdout.flush()
    
    if cv2.waitKey(1) == 27: # ESC to stop
        break

# end program:
cam.release()
cv2.destroyAllWindows()
