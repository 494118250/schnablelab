# -*- coding: UTF-8 -*-

"""
Crop RGB images from LemnaTec based on zoom levels using magick.
"""

import os.path as op
from pathlib import Path
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob, cutlist
from JamesLab.apps.natsort import natsorted
from subprocess import call
from subprocess import Popen
import re
from JamesLab.apps.header import Slurm_header
import cv2
import numpy as np
import pandas as pd
from skimage.morphology import convex_hull_image
from skimage.util import invert
from scipy import misc
from PIL import Image


def main():
    actions = (
        ('crop', 'crop sorghum images based their zoom levels'),
        ('pdf2png', 'convert pdf to png format'),
        ('downsize', 'down size the image'),
        ('PlantHull', 'detect he convex hull of a image'),
        ('PlantHullBatch', 'run PlantPixels script on all images'),
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def PlantHull(args):
    """
    %prog PlantHull img
    count how many pixels belong to plant part
    """
    p = OptionParser(PlantHull.__doc__)
    p.add_option('--border',
                 help="ignore image part out of boder: up,down,left,right")
    p.add_option('--crop',
                 help="crop image based on hull size")
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    inputImg, = args
    img = cv2.imread(inputImg, 0)
    if opts.border:
        up, bot, lef, rig = [int(i) for i in opts.border.split(',')]
        img[0:up, :] = 255
        img[-bot:, :] = 255
        img[:, 0:lef] = 255
        img[:, -rig] = 255
    _, thresh = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
    thresh_ivt = invert(thresh)
    chull = convex_hull_image(thresh_ivt)
    pos = np.where(chull)
    if opts.crop:
        top, down, left, right = pos[0].min(), pos[0].max(), pos[1].min(), pos[1].max()
        imgrgb = Image.open(inputImg)
        imgrgb_crop = imgrgb.crop((left, top, right, down))
        imgrgb_crop.save(inputImg.replace('.png', '.crp.png'))
    chull_diff = np.where(thresh_ivt == 255, 2, chull)
    misc.imsave('%s.hull.png' % (Path(inputImg).stem), chull_diff)
    PixelCount = np.sum(chull)
    print('%s\t%s' % (inputImg, PixelCount))


def PlantHullBatch(args):
    """
    %prog PlantHullBatch Pattern("*.png") job_n
    generate PlantHull jobs for all image files
    """
    p = OptionParser(PlantHullBatch.__doc__)
    p.set_slurm_opts()
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pattern, jobn, = args
    all_imgs = glob(pattern)
    all_cmds = []
    for img in all_imgs:
        imgpath = Path(img)
        outpre = str(imgpath.stem)
        #cmd = 'python -m JamesLab.ImgPros.Preprocess PlantHull %s --border 80,10,10,0 > %s.ppnum\n' % (img, outpre)
        cmd = 'python -m JamesLab.ImgPros.Preprocess PlantHull %s --crop True> %s.ppnum\n' % (img, outpre)
        all_cmds.append(cmd)
    grps = cutlist(all_cmds, int(jobn))
    for gn, grp in grps:
        header = Slurm_header % (opts.time, opts.memory, outpre, outpre, outpre)
        header += "ml anaconda\nsource activate MCY\n"
        for cmd in grp:
            header += cmd
        jobname = '%s.ppnum.slurm' % (gn)
        jobfile = open(jobname, 'w')
        jobfile.write(header)
        jobfile.close()
        print('%s job file generated!' % jobname)


def crop(args):
    """
    %prog crop image

    crop sorghum images using magick
    """
    p = OptionParser(crop.__doc__)
    p.add_option('--date', default='08-09',
                 help='specify the first day of zoom level 2. Follow the mm-dd format')

    p.set_slurm_opts(jn=True)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    inputImg, = args
    prefix = '.'.join(inputImg.split('.')[0:-1])
    out_img = prefix + '.crop.png'
    y, m, d = re.findall('201[7-9]-[0|1][0-9]-[0-3][0-9]', inputImg)[0].split('-')
    mo, dy = opts.date.split('-')
    if m < mo:
        zoom = 1
    elif m == mo:
        zoom = 1 if d < dy else 2
    else:
        zoom = 2

    cmd = 'magick %s -crop 1700x1600+500+0 %s' % (inputImg, out_img) \
        if zoom == 1 \
        else 'magick %s -crop 900x1443+850+217 %s' % (inputImg, out_img)

    h = Slurm_header
    h += 'module load anaconda\nsource activate MCY\n'
    header = h % (opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    slurm = '%s.crop.slurm' % prefix
    f = open(slurm, 'w')
    f.write(header)
    f.close()
    print('slurm file %s has been created' % slurm)


def pdf2png(args):
    """
    %prog pdf2png input_pdf output_png

    covnert pdf to png format.
    """
    p = OptionParser(pdf2png.__doc__)
    p.add_option('--dpi', default='150', choices=('150', '300'),
                 help='specify the dpi')
    p.add_option('--compression', default='90', choices=('50', '90', '100'),
                 help='specify the perfentage of compression, 100 means no compression.')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    inputpdf, outputpng, = args
    cmd = 'convert -density %s %s -quality %s %s\n' % (opts.dpi, inputpdf, opts.compression, outputpng)
    print('command:\n%s' % cmd)


def downsize(args):
    """
    %prog downsize image

    downsize sorghum images using amgick
    """


if __name__ == '__main__':
    main()
