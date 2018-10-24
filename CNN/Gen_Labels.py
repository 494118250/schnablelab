"""
generate labels of training images
"""

import pandas as pd
from pathlib import Path

def genlabel(img_dir):
    img_dir = img_dir
    img_path = Path(img_dir)
    imgs = img_path.glob('*png')
    fns = [i.name for i in imgs]
    lcs = [i.split('_')[0] for i in fns]
    mydf = pd.DataFrame(dict(zip(['fn', 'lc'], [fns, lcs])))
    mydf.to_csv(img_path/'my_labels.csv', index=False, header=False)
    print('Done, check my_labels.csv')

import sys
if len(sys.argv)==2:
    train(*sys.argv[1:])
else:
    print('train_dir')
