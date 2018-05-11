# -*- coding: UTF-8 -*-

"""
Post process the significant SNPs from GWAS results.
"""

import os.path as op
import sys
import pandas as pd
import numpy as np
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header
from subprocess import call
import pandas as pd
import matplotlib.pyplot as plt


def main():
    actions = (
        ('fetchMAF', 'calculate the MAFs of selected SNPs'),
        ('fetchEVs', 'fetch effect sizes of selected SNPs'),
        ('fetchGenes', 'fetch genes and functions of selected SNPs'),
        ('PlotEVs', 'plot histgram of effect sizes'),
        ('PlotMAF', 'plot histgram of maf'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def parseMAF(i):
    j = i.split()
    allele1, allele2 = j[1].split('/')
    genos = ''.join(j[11:])
    a1, a2 = genos.count(allele1), genos.count(allele2)
    maf = a1/float(a1+a2) \
        if a1 <= a2 \
        else a2/float(a1+a2)
    count = len(genos)*maf
    return j[0], maf, count
    

def fetchMAF(args):
    """
    %prog SNPlist hmp
    
    Calculate MAF of SNPs in a file where SNPs are listed row by row. Only first row were considered.
    If there are multiple columns, use space or tab as separators
    """
    p = OptionParser(fetchMAF.__doc__)
    p.add_option('--header', default = 'no', choices=('yes', 'no'),
        help = 'specify if there is a header in your SNP list file')
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    
    SNPlist, hmp = args
    df = pd.read_csv(SNPlist, delim_whitespace=True, header=None) \
        if opts.header == 'no' \
        else pd.read_csv(SNPlist, delim_whitespace=True)
    SNPs = df.iloc[:, 0]
    SNPsfile = SNPs.to_csv('SNPs_list.csv', index=False)
    cmd = 'grep -f SNPs_list.csv %s > Genotypes_list.csv'%hmp
    call(cmd, shell=True)
    f = open('Genotypes_list.csv')
    f1 = open('MAF.%s'%SNPlist, 'w')
    f1.write('SNPs\tMAF\tCount\n')
    for i in f:
        snp, maf, count = parseMAF(i)
        newi = '%s\t%s\t%s\n'%(snp, maf, count)
        f1.write(newi)
    f.close()
    f1.close()

def PlotEVs(args):
    """
    %prog EVlist(FarmCPU result) output_prefix
    plot the histogram of effect sizes 
    """
    p = OptionParser(PlotEVs.__doc__)
    #p.add_option('--header', default = 'no', choices=('yes', 'no'),
    #    help = 'specify if there is a header in your SNP list file')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    EVlist,output_prefix = args
    df = pd.read_csv(EVlist)
    EVs = df.iloc[:,-1]
    xlim = min(max(EVs), abs(min(EVs)))
    ax = EVs.plot(kind='hist', bins=60, grid=True, alpha=0.75, edgecolor='k')
    ax.set_xlim(-xlim, xlim)
    ax.set_xlabel('Effect size')
    ax.set_ylabel('Counts')
    plt.tight_layout()
    plt.savefig('%s.pdf'%output_prefix)
    plt.savefig('%s.png'%output_prefix)

if __name__ == '__main__':
    main()
