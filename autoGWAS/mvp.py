# -*- coding: UTF-8 -*-
"""
Generate MVP slurm job file. Find more details about MVP at <https://github.com/XiaoleiLiuBio/MVP>.
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header, MVP_header
from JamesLab.apps.natsort import natsorted

def main():
    actions = (
        ('mvp', 'Perform GWAS using mvp'),
        ('plot', 'plot GWAS results using MVP.Reoport() function'), 
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def mvp(args):
    """
    %prog mvp geno_hmp pheno out_prefix

    Run MVP using mixed linear model
    """
    p = OptionParser(mvp.__doc__)
    p.add_option('--model', default='MLM', choices=('MLM', 'FarmCPU'),
        help = 'specify GWAS model [default: %default]')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    geno, pheno, op, = args # op: output prefix

    farmUniq = '''maxLoop=10,method.bin="FaST-LMM"'''
    f1 = open('%s.%s.R'%(op,opts.model), 'w')
    header = MVP_header%(geno, pheno, op, op,op,op,op,op,opts.model,'',opts.model)\
        if opts.model == 'MLM'\
        else MVP_header%(geno, pheno, op, op,op,op,op,op,opts.model,farmUniq,opts.model)
    f1.write(header)
    f1.close()
    
    f2 = open('%s.%s.slurm'%(op, opts.model), 'w')
    h = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    h += 'module load R\n'
    h += 'R CMD BATCH %s.%s.R\n'%(op, opts.model)
    f2.write(h)
    f2.close()
    print('R script %s.%s.R and slurm file %s.%s.slurm has been created, you can submit now.'%(op, opts.model, op, opts.model))

def plot(args):
    """
    %prog plot gwas_out

    plt MVP results using Report function
    """
    pass

if __name__ == '__main__':
    main()
