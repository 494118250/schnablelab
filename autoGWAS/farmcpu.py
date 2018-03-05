# -*- coding: UTF-8 -*-

"""
Generate the R script file and the slurm job file for performing FarmCPU. Find more details in FarmCPU manual at <http://www.zzlab.net/FarmCPU/FarmCPU_help_document.pdf>
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import SlrumHeader
from JamesLab.apps.header import FarmCPU_header
from JamesLab.apps.natsort import natsorted

def main():
    actions = (
        ('farmcpu', 'Perform GWAS using FarmCPU (muti-loci mixed model)'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def farmcpu(args):
    """
    %prog farmcpu pheno geno_prefix PCA

    Run automated FarmCPU
    """
    p = OptionParser(farmcpu.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())

    pheno, geno_prefix, PCA = args
    mem = '.'.join(pheno.split('.')[0:-1])
    f1 = open('%s.FarmCPU.R'%mem, 'w')
    farmcpu_cmd = FarmCPU_header%(pheno,geno_prefix,geno_prefix,PCA,mem)
    f1.write(farmcpu_cmd)

    f2 = open('%s.farmcpu.slurm'%mem, 'w')
    h = SlrumHeader()
    h.AddModule(['R/3.3'])
    header = h.header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    f2.write(header)
    cmd = 'R CMD BATCH %s.FarmCPU.R'%mem
    f2.write(cmd)
    f1.close()
    f2.close()
    print('R script %s.farmcpu.R and slurm file %s.farmcpu.slurm has been created, you can sbatch your job file.'%(mem, mem))

if __name__ == "__main__":
    main()
