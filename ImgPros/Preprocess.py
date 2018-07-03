# -*- coding: UTF-8 -*-

"""
Crop RGB images from LemnaTec based on zoom levels using magick.
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob,iglob
from JamesLab.apps.natsort import natsorted
from subprocess import call
from subprocess import Popen
import re
from JamesLab.apps.header import Slurm_header

def main():
    actions = (
        ('crop', 'crop sorghum images based their zoom levels'),
        ('pdf2png', 'convert pdf to png format'),
        ('downsize', 'down size the image'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def crop(args):
    """
    %prog crop image

    crop sorghum images using magick  
    """
    p = OptionParser(crop.__doc__)
    p.add_option('--date', default = '08-09', 
        help = 'specify the first day of zoom level 2. Follow the mm-dd format')

    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    inputImg,= args
    prefix = '.'.join(inputImg.split('.')[0:-1])
    out_img = prefix+'.crop.png'
    y,m,d = re.findall('201[7-9]-[0|1][0-9]-[0-3][0-9]', inputImg)[0].split('-')
    mo, dy = opts.date.split('-')
    if m < mo:
        zoom = 1
    elif m == mo:
        zoom = 1 if d < dy else 2
    else: 
        zoom = 2
   
    cmd = 'magick %s -crop 1700x1600+500+0 %s'%(inputImg, out_img) \
        if zoom ==1 \
        else 'magick %s -crop 900x1443+850+217 %s'%(inputImg, out_img)

    h = Slurm_header
    h += 'module load anaconda\nsource activate MCY\n'
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    slurm = '%s.crop.slurm'%prefix
    f = open(slurm, 'w')
    f.write(header)
    f.close()
    print('slurm file %s has been created'%slurm)

def pdf2png(args):
    """
    %prog pdf2png input_pdf output_png
    
    covnert pdf to png format.
    """
    p = OptionParser(pdf2png.__doc__)
    p.add_option('--dpi', default = '150', choices=('150', '300'),
        help = 'specify the dpi')
    p.add_option('--compression', default = '90', choices=('50', '90', '100'),
        help = 'specify the perfentage of compression, 100 means no compression.')
    #p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    inputpdf,outputpng, = args
    cmd = 'convert -density %s %s -quality %s %s\n'%(opts.dpi, inputpdf, opts.compression, outputpng)
    print('command:\n%s'%cmd)
    
    

def downsize(args):
   """
   %prog downsize image

   downsize sorghum images using amgick
   """


if __name__ == '__main__':
    main()















