# -*- coding: UTF-8 -*-

"""
Preprocess files(fasta, fastq, ...) before SNP calling
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob,iglob
from JamesLab.apps.natsort import natsorted
import subprocess
from JamesLab.apps.header import Slurm_header

# the location of linkimpute, beagle executable

def main():
    actions = (
        ('Trim', 'trim fastq files using trimmomatic'),
        ('SplitFa', 'Split Fasta'),
)
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def trim(args):
    """
    %prog splitVCF N vcf
    split vcf to N smaller files with equal size
    """
    p = OptionParser(splitVCF.__doc__)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    N, vcffile, = args
    cmd = \
'java -jar ~/Trimmomatic-0.33/trimmomatic-0.33.jar PE -threads 10 %s %s %s %s %s %s \
ILLUMINACLIP:/share/bioinfo/miaochenyong/center-adapters/adapters.fa:2:30:10 \
TRAILING:20 HEADCROP:%s MINLEN:50'%(fq1, fq2, prefix+'1_paired'+suffix, prefix+'1_unpaired'+suffix, \
prefix+'2_paired'+suffix, prefix+'2_unpaired'+suffix, headcrop)



if __name__ == "__main__":
    main()
