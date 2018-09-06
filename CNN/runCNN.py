# -*- coding: UTF-8 -*-

"""
generate slurm files for machine learning jobs.
"""
import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header, Slurm_gpu_header
from JamesLab.apps.natsort import natsorted
from numpy.random import uniform

vgg_py = op.abspath(op.dirname(__file__))+'/VGG.py'    
LNN_py = op.abspath(op.dirname(__file__))+'/LinearClassifer.py'    

def main():
    actions = (
        ('vgg', 'run vgg model'),
        ('LinearModel', 'run simple linear neural network'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def vgg(args):
    """
    %prog train_dir val_dir num_category model_name_prefix
    
    Run vgg model
    """
    p = OptionParser(vgg.__doc__)
    p.add_option('--lr', default=40,
        help = 'specify number of learing rate to test')
    p.add_option('--epc', default=50,
        help = 'specify epoches')
    p.set_slurm_opts(jn=True, gpu=True)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    train_dir, val_dir, numC, mnp = args #mnp:model name prefix
    n = 1 
    for count in range(int(opts.lr)):
        jobprefix = '%s_%s'%(opts.prefix, n)
        n += 1
        lr = 10**uniform(-2, -7)
        model_name = '%s_%s'%(mnp, lr)
        vgg_cmd = 'python %s %s %s %s %s %s %s'%(vgg_py, train_dir, val_dir, numC, lr, opts.epc, model_name) 
        SlurmHeader = Slurm_gpu_header%(opts.time, opts.memory, jobprefix,jobprefix,jobprefix,opts.gpu)
        SlurmHeader += 'module load anaconda\n'
        SlurmHeader += 'source activate MCY\n'
        SlurmHeader += vgg_cmd
        f = open('%s.vgg.slurm'%model_name, 'w')
        f.write(SlurmHeader)
        f.close()
        print('slurm file %s.vgg.slurm has been created, you can sbatch your job file.'\
%model_name)
    
def LinearModel(args):
    """
    %prog np_predictors np_target cpu_or_gpu
    tune model with different parameters
    """
    p = OptionParser(LinearModel.__doc__)
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
