# -*- coding: UTF-8 -*-

"""
Call peaks using DNase-seq.
"""

import os
import os.path as op
import sys
import pandas as pd
import numpy as np
from schnablelab.apps.base import ActionDispatcher, OptionParser
from schnablelab.apps.header import Slurm_header
from subprocess import call

def main():
    actions = (
        ('RunMACS2', 'run macs2'),
        ('FetchSeqs', 'extract sequences of peak reagions'),
)
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def RunMACS2(args):
    """
    %prog species(bd, si, sb) out_prefix BAMs(separated by comma)
    call peaks using all bam files
    """
    p = OptionParser(RunMACS2.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    species, out_prefix, bams, = args
    all_bams = ' '.join([i for i in bams.split(',')])
    print('BAMS: %s'%all_bams)
    g_dict = {'bd':'2e8', 'si':'3e8', 'sb':'6e8'}
    cmd = 'macs2 callpeak -t %s -n %s --outdir %s -f BAM -q 0.01 -g %s -B --nomodel --shift 37 --extsize 73\n'%(all_bams, out_prefix, out_prefix, g_dict[species])
    header = Slurm_header%(opts.time, opts.memory, out_prefix,out_prefix,out_prefix)
    header += 'module load macs2\n'
    header += cmd
    jobfile = '%s.macs2.slurm'%out_prefix
    f = open(jobfile, 'w')
    f.write(header)
    f.close()
    print('slurm files %s.macs2.slurm has been created, you can sbatch your job file.')
    
def FetchSeqs(args):
    """
    %prog fasta bed out
    fetch sequences using bedtools
    """
    p = OptionParser(FetchSeqs.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    fasta, bed, out, = args 
    cmd1 = 'ml bedtools'
    print(cmd1)
    cmd2 = 'nohup bedtools getfasta -fi %s -bed %s -name > %s &'%(fasta, bed, out)
    print(cmd2)

if __name__ == "__main__":
    main()

