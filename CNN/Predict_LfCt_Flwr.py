# 10/4/18
# chenyong
# predict leaf counts using trained model

"""
Make predictions of Leaf counts using trained models
"""

import os.path as op
import sys
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob
from JamesLab.apps.header import Slurm_header
from JamesLab.apps.natsort import natsorted
from glob import glob
from PIL import Image
import cv2
from pathlib import Path

def main():
    actions = (
        ('Predict', 'using trained model to make prediction'),
        ('PredictBatch', 'generate all slurm jobs of prediction'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def Predict(args):
    """
    %prog model_name img_dir target_size output_prefix
    using your trained model to make predictions. Target size is the input_shape when
    you train your model. an invalid target_size example is 224,224,3
    """
    from keras.models import load_model
    p = OptionParser(Predict.__doc__)
    p.set_slurm_opts()
    p.add_option('--img_num', default='all',
                 help='specify how many images used for prediction in the dir')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    model, img_dir, ts, otp = args

    ts = tuple([int(i) for i in ts.split(',')][:-1])
    print(ts)
    p = Path(img_dir)
    ps = list(p.glob('*.png'))[:int(opts.img_num)] \
        if opts.img_num!='all' \
        else list(p.glob('*.png'))
    imgs = []
    fns = []
    for i in ps:
        print(i.name)
        fns.append(i.name)
        img = cv2.imread(str(i))
        img = cv2.resize(img, ts)
        imgs.append(img)
    imgs_arr = np.asarray(imgs)
    my_model = load_model(model)
    pre_prob = my_model.predict(imgs_arr)
    df = pd.DataFrame(pre_prob)
    clss = df.shape[1]
    headers = ['class_%s'%i for i in range(1, clss+1)]
    df.columns = headers
    df['image'] = fns
    headers.insert(0, 'image')
    df_final = df[headers]
    df_final.to_csv('%s.csv'%otp, sep='\t', index=False)

if __name__ == "__main__":
    main()







