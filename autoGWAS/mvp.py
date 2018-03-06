# -*- coding: UTF-8 -*-
"""
Generate MVP slurm job file. Find more details about MVP at <https://github.com/XiaoleiLiuBio/MVP>.
If MVP hasn't be installed. Fllow steps below to install MVP:
$ wget https://raw.githubusercontent.com/XiaoleiLiuBio/MVP/master/packages.zip
$ unzip packages.zip
$ cd packages
$ R
> source("MVPinstall.r")
After installed successfully, MVP can be loaded by typing
> library(MVP)
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import SlrumHeader
from JamesLab.apps.natsort import natsorted

def main():
    actions = (
        ('MLM', 'Perform GWAS using mixed linear model'),
        ('FarmCPU', 'Perform GWAS using FarmCPU'), 
        ('Both', 'Perform GWAS using both mlm and farmcpu'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

class MVP():
    """
    class for generating mvp commands
    """
    def __init__(self):
        self.header = "phe=%s, geno=%s, map=%s, K=%s, \
            perc=1, priority='speed', ncpus=10, vc.method='GEMMA', \
            maxLoop=10, method.bin='FaST-LMM', "

    def add_cutoff_method(self, m):
        if m=='permutation':
            self.header += 'permutation.threshold=TRUE, permutation.rep=100, '
        elif m=='bonferroni':
            self.header += 'threshold=0.05, '
        else:
            print('only permutation and bonferroni allowed')

    def add_models(self, n):
        if n == 1:
            self.header += "method=c('FarmCPU'), nPC.FarmCPU=%s"
        if n == 2:
            self.header += "method=c('MLM'), nPC.MLM=%s"
        elif n ==3:
            self.header += "method=c('FarmCPU','MLM'), nPC.FarmCPU=%s, nPC.MLM=%s"
        else:
            print('only 1, 2, and 3 allowed')

def MLM(args):
    """
    %prog MLM pheno geno_prefix kinship

    Run MVP using mixed linear model
    """
    p = OptionParser(MLM.__doc__)
    p.add_option('--numPCs', default=10,
        help = 'specify the number of PCs used in MLM [default: %default]')
    p.add_option('--testing', default='permutation',choice=('permutation', 'bonferroni')
        help = 'specify the multi-teseting method [default: %default]')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pheno,geno_prefix,kinship= args
    h = MVP()
    h.add_cutoff_method(opts.testing)
    h.add_models(2)
    myheader = h.header%(pheno,geno_prefix+'.numeric', geno_prefix+'.map', kinship,opts.numPCs)
    mem = '.'.join(pheno.split('.')[0:-1])
    f1 = open('%s.MVP.MLM.R'%mem, 'w')
    Rcmd = 'library(MVP)\n'
    Rcmd += 'imMVP <- MVP(%s)\n'%myheader
    f1.write(Rcmd)
    f1.close()
    print(Rcmd)

    f2 = open('%s.MVP.MLM.slurm'%mem, 'w')
    h = SlrumHeader()
    h.AddModule(['R/3.3'])
    header = h.header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    f2.write(header)
    cmd = 'R CMD BATCH %s.MVP.MLM.R'%mem
    f2.write(cmd)
    f2.close()
    print('R script %s.MVP.MLM.R and slurm file %s.MVP.MLM.slurm has been created, you can sbatch your job file.'%(mem, mem))
    
def FarmCPU(args):
    """
    %prog FarmCPU pheno geno_prefix kinship

    Run MVP using farmcpu
    """
    p = OptionParser(FarmCPU.__doc__)
    p.add_option('--numPCs', default=10,
        help = 'specify the number of PCs used in FarmCPU [default: %default]')
    p.add_option('--testing', default='permutation',choice=('permutation', 'bonferroni')
        help = 'specify the multi-testing method [default: %default]')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pheno,geno_prefix,kinship= args
    h = MVP()
    h.add_cutoff_method(opts.testing)
    h.add_models(1)
    myheader = h.header%(pheno,geno_prefix+'.numeric', geno_prefix+'.map', kinship,opts.numPCs)
    mem = '.'.join(pheno.split('.')[0:-1])
    f1 = open('%s.MVP.farmcpu.R'%mem, 'w')
    Rcmd = 'library(MVP)\n'
    Rcmd += 'imMVP <- MVP(%s)\n'%myheader
    f1.write(Rcmd)
    f1.close()
    print(Rcmd)

    f2 = open('%s.MVP.farmcpu.slurm'%mem, 'w')
    h = SlrumHeader()
    h.AddModule(['R/3.3'])
    header = h.header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    f2.write(header)
    cmd = 'R CMD BATCH %s.MVP.farmcpu.R'%mem
    f2.write(cmd)
    f2.close()
    print('R script %s.MVP.farmcpu.R and slurm file %s.MVP.farmcpu.slurm has been created, you can sbatch your job file.'%(mem, mem))

def Both(args):
    """
    %prog Both pheno geno_prefix kinship

    Run MVP using both MLM and farmcpu
    """
    p = OptionParser(Both.__doc__)
    p.add_option('--numPCs', default=10,
        help = 'specify the number of PCs used in MLM and FarmCPU [default: %default]')
    p.add_option('--testing', default='permutation',choice=('permutation', 'bonferroni')
        help = 'specify the multi-testing method [default: %default]')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pheno,geno_prefix,kinship= args
    h = MVP()
    h.add_cutoff_method(opts.testing)
    h.add_models(3)
    myheader = h.header%(pheno,geno_prefix+'.numeric', geno_prefix+'.map', kinship,opts.numPCs)
    mem = '.'.join(pheno.split('.')[0:-1])
    f1 = open('%s.MVP.both.R'%mem, 'w')
    Rcmd = 'library(MVP)\n'
    Rcmd += 'imMVP <- MVP(%s)\n'%myheader
    f1.write(Rcmd)
    f1.close()
    print(Rcmd)

    f2 = open('%s.MVP.both.slurm'%mem, 'w')
    h = SlrumHeader()
    h.AddModule(['R/3.3'])
    header = h.header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    f2.write(header)
    cmd = 'R CMD BATCH %s.MVP.both.R'%mem
    f2.write(cmd)
    f2.close()
    print('R script %s.MVP.both.R and slurm file %s.MVP.both.slurm has been created, you can sbatch your job file.'%(mem, mem))

if __name__ == '__main__':
    main()
