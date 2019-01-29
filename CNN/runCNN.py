# -*- coding: UTF-8 -*-

"""
Train CNN for leaf counting, panicle emergence detection, and hyper segmentation
"""
import os
import sys
import os.path as op

from pathlib import Path
from numpy.random import uniform
from schnablelab.apps.Tools import eprint
from schnablelab.apps.natsort import natsorted
from schnablelab.apps.base import ActionDispatcher, OptionParser
from schnablelab.apps.header import Slurm_header, Slurm_gpu_header

def main():
    actions = (
        ('keras_cnn', 'train vgg model'),
        ('keras_snn', 'train simple neural network'),
        ('dpp', 'train dpp model'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

class fns(object):
    def __init__(self, model_name, tb_dir=None, n=1):
        self.lrs = [0.001] if n==1 else [10**uniform(-2, -6) for i in range(n)]
        self.model_name = ['{}_{}'.format(model_name, i) for i in self.lrs]
        if tb_dir:
            self.tb_dirs = ['{}_{}'.format(tb_dir, i) for i in self.lrs]
 
def dpp(args):
    '''
    %prog training_data_dir label_fn model_results_dir

    Run dpp regression model
    '''
    p = OptionParser(dpp.__doc__)
    p.add_option('--problem_type', default='classification',choices=('classification', 'regression'),
        help = 'specify your problem type')
    p.add_option('--tensorboard', default='infer',
        help = 'tensorboard dir name')
    p.add_option('--epoch', default=500,
        help = 'number of epoches. set to 500 for leaf couting problem')
    p.add_option('--split_ratio', default=0.2,
        help = 'the ratio of training dataset used for testing')
    p.add_option('--lr_n', default=1, type='int',
        help = 'train model with differnt learning rates. if n=1: set lr to 0.001. if n>1: try differnt lr from 1e-2 to 1e-5 n times')
    p.set_slurm_opts(gpu=True)
    opts, args = p.parse_args(args)

    if len(args) != 3:
        sys.exit(not p.print_help())

    training_dir, label_fn, model_name, = args
    tb_dir_name = 'tensorboard_{}'.format(model_name) if opts.tensorboard == 'infer' else opts.tensorboard
    out_fns = fns(model_name, tb_dir=tb_dir_name, n=opts.lr_n)
    for i in range(opts.lr_n):
        try:
            os.mkdir(out_fns.model_name[i])
        except FileExistsError:
            eprint("ERROR: Filename collision. The future output file `{}` exists".format(out_fns.model_name[i]))
            sys.exit(1)
        cmd = 'python -m schnablelab.CNN.dpp_%s %s %s %s %s %s %s %s'%\
            (opts.problem_type, training_dir, label_fn, out_fns.model_name[i], out_fns.tb_dirs[i], opts.epoch, opts.split_ratio, out_fns.lrs[i])
        SlurmHeader = Slurm_gpu_header%(opts.time, opts.memory, out_fns.model_name[i], out_fns.model_name[i], out_fns.model_name[i])
        SlurmHeader += 'module load anaconda\nsource activate MCY\n'
        SlurmHeader += cmd

        f = open('%s.slurm'%out_fns.model_name[i], 'w')
        f.write(SlurmHeader)
        f.close()
        print('slurm file %s.slurm has been created, now you can sbatch your job file.'%out_fns.model_name[i]) 

def keras_cnn(args):
    """
    %prog train_dir val_dir num_category model_name_prefix
    
    Run vgg model
    """
    p = OptionParser(keras_cnn.__doc__)
    p.add_option('--epoch', default=500, help = 'number of epoches')
    p.add_option('--lr_n', default=1, type='int',
        help = 'train model with differnt learning rates. if n=1: set lr to 0.001. if n>1: try differnt lr from 1e-2 to 1e-5 n times')
    p.set_slurm_opts(gpu=True)
    opts, args = p.parse_args(args)

    if len(args) != 4:
        sys.exit(not p.print_help())

    train_dir, val_dir, numC, mnp = args #mnp:model name prefix
    out_fns = fns(mnp, n=opts.lr_n)
    for i in range(int(opts.lr_n)):
        cmd = 'python -m schnablelab.CNN.keras_vgg %s %s %s %s %s %s'%(train_dir, val_dir, numC, out_fns.lrs[i], opts.epoch, out_fns.model_name[i]) 
        SlurmHeader = Slurm_gpu_header%(opts.time, opts.memory, out_fns.model_name[i], out_fns.model_name[i], out_fns.model_name[i])
        SlurmHeader += 'module load anaconda\nsource activate MCY\n'
        SlurmHeader += cmd
        f = open('%s.slurm'%out_fns.model_name[i], 'w')
        f.write(SlurmHeader)
        f.close()
        print('slurm file %s.slurm has been created, you can sbatch your job file.'%out_fns.model_name[i])
    
def keras_snn(args):
    """
    %prog np_predictors np_target cpu_or_gpu
    tune model with different parameters
    """
    p = OptionParser(keras_snn.__doc__)
    p.add_option('--lr', default=40,
        help = 'specify the number of learing rate in (1e-2, 1e-6)')
    p.add_option('--layer', default='4', choices=['2','3','4'],
        help = 'specify the number of hidden layers')
    #p.add_option('--epc', default=30,
    #    help = 'specify epoches')
    p.set_slurm_opts(array=True)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    np_x,np_y,CorG = args

# find the good structure capacity(from low/simple to high/complex) and learning rate .
# You will observe a relatively deep curve but it continous to go down.
# loss function(tell how bad your weight is): also try 'mean_squared_error'?
# optimizer(the process to choose minimum bad value of your weight): also try 'adam'

    units = [50, 100, 150, 200, 250, 300, 350, 400]
    #gpu = ['p100', 'p100', 'k40', 'k40', 'k40', 'k20', 'k20', 'k20']
    
    lyr = int(opts.layer)
    print('the hidden layers: %s'%lyr)
    for unit in units:
        for count in range(int(opts.lr)):
            lr = 10**uniform(-2, -6)
            cmd = 'python %s %s %s %s %s %s\n'%(LNN_py, np_x, np_y, lyr, unit, lr)
            prefix = 'lyr%s_uni%s_lr%s'%(lyr, unit, lr)
            SlurmHeader = Slurm_gpu_header%(opts.memory, prefix,prefix,prefix,opts.gpu)\
                if CorG == 'gpu' \
                else Slurm_header%(opts.time, opts.memory, prefix,prefix,prefix) 
            SlurmHeader += 'module load anaconda\n'
            SlurmHeader += 'source activate MCY\n' \
                if CorG == 'gpu' \
                else 'source activate Py3KerasTensorCPU\n'
            SlurmHeader += cmd
            f = open('LNN_%s_%s_%s.slurm'%(lyr,unit,lr), 'w')
            f.write(SlurmHeader)
            f.close()
    print('slurms have been created, you can sbatch your job file.')

if __name__ == "__main__":
    main()
