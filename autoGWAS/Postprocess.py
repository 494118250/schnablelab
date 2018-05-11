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
import numpy as np
import matplotlib.pyplot as plt

# the location of plink executale file
plink = op.abspath(op.dirname(__file__))+'/../apps/plink'

def main():
    actions = (
        ('fetchMAF', 'calculate the MAFs of selected SNPs'),
        ('fetchEVs', 'fetch effect sizes of selected SNPs'),
        ('fetchLinkedSNPs', 'fetch highly linked SNPs'),
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

    minor_allele, major_allele, = (allele1, allele2) if a1 <= a2 else (allele2, allele1)
    minor_idx, major_idx, hetero_idx = [], [] , []
    for m,n in enumerate(j[11:]):
        k = list(set(n))
        if len(k)==1:
            if k[0] == minor_allele:
                minor_idx.append(m+11)
            elif k[0] == major_allele:
                major_idx.append(m+11)
            else:
                print(n)
                print('bad allele!!!')
        else:
            hetero_idx.append(m+11)

    return j[0], maf, count, minor_idx, major_idx, hetero_idx
    

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
    f1.write('SNPs\tMAF\tCount\tMinorAlleleSMs\tMajorAlleleSMs\tHeteroSMs\n')
    header = np.array(open(hmp).readline().split())
    for i in f:
        snp, maf, count, minor_idx, major_idx, hetero_idx = parseMAF(i)
        minor_SMs, major_SMs, hetero_SMs = ','.join(list(header[minor_idx])), ','.join(list(header[major_idx])), ','.join(list(header[hetero_idx]))
        print(minor_SMs)
        print(major_SMs)
        print(hetero_SMs)
        newi = '%s\t%s\t%s\t%s\t%s\t%s\n'%(snp, maf, count, minor_SMs, major_SMs, hetero_SMs)
        f1.write(newi)
    f.close()
    f1.close()
    print('see MAF.%s'%SNPlist)

def fetchEVs(args):
    """
    %prog SNPlist FarmCPUresult
    
    extract effect size of SNPs in the list from FarmCPU result
    """
    p = OptionParser(fetchEVs.__doc__)
    p.add_option('--header', default = 'no', choices=('yes', 'no'),
        help = 'specify if there is a header in your SNP list file')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    SNPlist, farmResult = args
    df = pd.read_csv(SNPlist, delim_whitespace=True, header=None) \
        if opts.header == 'no' \
        else pd.read_csv(SNPlist, delim_whitespace=True)
    SNPs = df.iloc[:, 0]
    SNPsfile = SNPs.to_csv('SNPs_list.csv', index=False)
    cmd = 'grep -f SNPs_list.csv %s > FarmCPU_list.csv'%farmResult
    call(cmd, shell=True)
    f = open('FarmCPU_list.csv')
    f1 = open('EVs.%s'%SNPlist, 'w')
    f1.write('SNPs\tEVs\n')
    for i in f:
        j = i.strip().split(',')
        snp, ev = j[0], j[-1]
        newi = '%s\t%s\n'%(snp, ev)
        f1.write(newi)
    f.close()
    f1.close()
    print('see EVs.%s'%SNPlist)

def fetchLinkedSNPs(args):
    """
    %prog SNPlist bed_prefix r2_cutoff output_prefix

    extract linked SNPs using plink
    """
    p = OptionParser(fetchLinkedSNPs.__doc__)
    p.set_slurm_opts(array=False)
    p.add_option('--header', default = 'no', choices=('yes', 'no'),
        help = 'specify if there is a header in your SNP list file')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    SNPlist, bedprefix, cutoff, output_prefix, = args
    df = pd.read_csv(SNPlist, delim_whitespace=True, header=None) \
        if opts.header == 'no' \
        else pd.read_csv(SNPlist, delim_whitespace=True)
    SNPs = df.iloc[:, 0]
    SNPsfile = SNPs.to_csv('SNPs_list.csv', index=False)
    cmd = '%s --bfile %s --r2 --ld-snp-list SNPs_list.csv --ld-window-kb 5000 --ld-window 99999 --ld-window-r2 %s --noweb --out %s\n'%(plink, bedprefix, cutoff, output_prefix)
    print('command run on local:\n%s'%cmd)
    f = open('%s.slurm'%output_prefix, 'w')
    h = Slurm_header
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f.write(header)
    f.close()
    print('Job file has been generated. You can submit: sbatch -p jclarke %s.slurm'%output_prefix)
     

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
