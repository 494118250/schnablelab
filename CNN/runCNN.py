# -*- coding: UTF-8 -*-

"""
train cnn based on vgg structure.
"""
import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_gpu_header
from JamesLab.apps.natsort import natsorted

vgg_py = op.abspath(op.dirname(__file__))+'/VGG.py'    

def main():
    actions = (
        ('vgg', 'run vgg model'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def vgg(args):
    """
    %prog train_dir val_dir model_name
    
    Run vgg model
    """
    p = OptionParser(vgg.__doc__)
    p.add_option('--lr', default=1e-5,
        help = 'specify the learing rate')
    p.add_option('--epc', default=30,
        help = 'specify epoches')
    p.set_slurm_opts(array=True)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    train_dir, val_dir, model_name = args
    
    vgg_cmd = 'python %s %s %s %s %s %s'%(vgg_py, train_dir, val_dir, opts.lr, opts.epc, model_name) 
    SlurmHeader = Slurm_gpu_header%(opts.prefix,opts.prefix,opts.prefix,opts.gpu)
    SlurmHeader += 'module load anaconda\n'
    SlurmHeader += 'source activate MCY\n'
    SlurmHeader += vgg_cmd
    f = open('%s.vgg.slurm'%opts.prefix, 'w')
    f.write(SlurmHeader)
    f.close()
    print('slurm file %s.vgg.slurm has been created, you can sbatch your job file.'\
%opts.prefix)
    
def inception():
    pass

def resnet():
    pass

 
if __name__ == "__main__":
    main()
