# 8/13/18
# chenyong
# call plant height

"""
call plant height from predicted images
"""
import os
import sys
import cv2
import numpy as np
import pandas as pd
import os.path as op
import scipy.misc as sm
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import rcParams
from PIL import Image
from math import hypot
from JamesLab.apps.natsort import natsorted
from JamesLab.apps.header import Slurm_header
from sklearn.linear_model import LinearRegression
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob

def main():
    actions = (
        ('Polish', 'Polish the predicted images'),
        ('PolishBatch', 'generate all slurm jobs of polish'),
        ('CallHeight', 'call height from polished image'),
        ('CallHeightBatch', 'generate all slurm jobs of plant height calling'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def CallPart(fn, part='stem'):
    img = Image.open(fn)
    crp_box = (25, 0, 300, 481) # crop: left, upper, right, and lower pixel coordinate
    img_crp = np.array(img.crop(crp_box)) 
    crp_shape2d = img_crp.shape[0:2]
    if part =='stem':
        r, g, b = 251, 129, 14
    elif part == 'panicle':
        r, g, b = 126, 94, 169
    elif part == 'leaf':
        r, g, b = 0, 147, 0
    else:
        sys.exit('only support stem, panicle, and leaf')
    p1 = np.full(crp_shape2d,r)
    p2 = np.full(crp_shape2d,g)
    p3 = np.full(crp_shape2d,b)
    p123 = np.stack([p1, p2, p3], axis=2)
    pRGB = np.where(img_crp==p123, img_crp, 255)
    return pRGB

def FilterPixels(arr3d, d=0):
    rgb_img = Image.fromarray(arr3d)
    gray_img = rgb_img.convert(mode='L')
    gray_blur_arr = cv2.GaussianBlur(np.array(gray_img), (3,3), 0)
    cutoff = pd.Series(gray_blur_arr.flatten()).value_counts().index.sort_values()[d]
    arr2d = np.where(gray_blur_arr<=cutoff, 0, 255) 
    return arr2d

def gray2rgb(arr2d, part="stem"):
    cond_k = arr2d==0
    if part =='stem':
        r, g, b = 251, 129, 14
    elif part == 'panicle':
        r, g, b = 126, 94, 169
    elif part == 'leaf':
        r, g, b = 0, 147, 0
    else:
        sys.exit('only support stem, panicle, and leaf')
    pr = np.where(cond_k, r, 255)
    pg = np.where(cond_k, g, 255)
    pb = np.where(cond_k, b, 255)
    pRGB = np.stack([pr, pg, pb], axis=2)
    return pRGB

def Polish(args):
    """
    %prog image_in image_out_prefix
    Using opencv blur function to filter noise pixles for each plant component
    """
    p = OptionParser(Polish.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    imgIn, imgOut = args
    
    stemRGBraw = CallPart(imgIn, 'stem')
    stem = FilterPixels(stemRGBraw)
    stemRGB = gray2rgb(stem, 'stem')
    panicleRGBraw = CallPart(imgIn, 'panicle')
    panicle = FilterPixels(panicleRGBraw, d=4)
    panicleRGB = gray2rgb(panicle, 'panicle')
    leafRGBraw = CallPart(imgIn, 'leaf')
    leaf = FilterPixels(leafRGBraw, d=4)
    leafRGB = gray2rgb(leaf, 'leaf')
    spRGB = np.where(stemRGB==255, panicleRGB, stemRGB)
    splRGB = np.where(spRGB==255, leafRGB, spRGB)
    sm.imsave('%s.polish.png'%imgOut, splRGB)

def PolishBatch(args):
    """
    %prog imagePattern("CM*.png")
    generate polish jobs for all image files
    """
    p = OptionParser(PolishBatch.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pattern, = args
    all_pngs = glob(pattern)
    for i in all_pngs:
        out_prefix = i.split('/')[-1].split('.png')[0]
        jobname = out_prefix + '.polish'
        cmd = 'python -m JamesLab.CNN.CallHeight Polish %s %s\n'%(i, out_prefix)
        header = Slurm_header%(opts.time, opts.memory, jobname, jobname, jobname)
        header += "ml anaconda\nsource activate %s\n"%opts.env
        header += cmd
        jobfile = open('%s.polish.slurm'%out_prefix, 'w')
        jobfile.write(header)
        jobfile.close()
        print('%s.slurm polish job file generated!'%jobname)

def CallHeight(args):
    """
    %prog image_in output_prefix
    call height from polished image
    """
    p = OptionParser(CallHeight.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    imageIn, outPrefix = args
    
    # get stem and panicle pixels
    sRGB = CallPart(imageIn, 'stem')
    sRGB_img = Image.fromarray(sRGB)
    sgray = np.array(sRGB_img.convert(mode='L'))
    pRGB = CallPart(imageIn, 'panicle')
    pRGB_img = Image.fromarray(pRGB)
    pgray = np.array(pRGB_img.convert(mode='L'))
    spgray = np.where(sgray==255, pgray, sgray)
    # fit model
    X = np.where(spgray< 255)[1]
    Y = np.where(spgray< 255)[0]*-1+spgray.shape[0]
    model = LinearRegression()
    model.fit(X.reshape(-1,1), Y)
    # regression line
    getx = lambda y: (y-model.intercept_)/model.coef_
    ymax = Y.max()
    a = np.absolute(getx(0)-getx(ymax))
    b = ymax
    c = hypot(a, b)
    f1 = open('%s.Height.csv'%outPrefix, 'w')
    f1.write('%s'%c)
    f1.close()
    # plot
    plt.switch_backend('agg')
    ylim, xlim = spgray.shape 
    rcParams['figure.figsize'] = xlim*0.015, ylim*0.015
    fig, ax = plt.subplots()
    ax.scatter(X, Y, s=0.1, color='k', alpha=0.7)
    ax.plot([getx(0), getx(ymax)], [0, ymax], c='r', linewidth=1)
    ax.text(100, 100, "%.2f"%c, fontsize=12)
    ax.set_xlim([0,xlim])
    ax.set_ylim([0,ylim])
    plt.tight_layout()
    plt.savefig('%s.Height.png'%outPrefix)

def CallHeightBatch(args):
    """
    %prog imagePattern("CM*.polish.png")
    generate height call jobs for all polished image files
    """
    p = OptionParser(CallHeightBatch.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pattern, = args
    all_pngs = glob(pattern)
    for i in all_pngs:
        out_prefix = i.split('/')[-1].split('.polish.png')[0]
        jobname = out_prefix + '.Height'
        cmd = 'python -m JamesLab.CNN.CallHeight CallHeight %s %s\n'%(i, out_prefix)
        header = Slurm_header%(opts.time, opts.memory, jobname, jobname, jobname)
        header += "ml anaconda\nsource activate %s\n"%opts.env
        header += cmd
        jobfile = open('%s.CallHeight.slurm'%out_prefix, 'w')
        jobfile.write(header)
        jobfile.close()
        print('%s.CallHeight.slurm call height job file generated!'%jobname)

if __name__ == "__main__":
    main()
















