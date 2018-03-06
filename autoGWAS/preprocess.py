# -*- coding: UTF-8 -*-

"""
Convert GWAS dataset to particular formats for GEMMA, GAPIT, FarmCPU, and MVP.
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import SlrumHeader

# the location of gemma executable file
gemma = op.abspath(op.dirname(__file__))+'/../apps/gemma'

def main():
    actions = (
        ('hmp2BIMBAM', 'transform hapmap format to BIMBAM format'),
        ('hmp2numeric', 'transform hapmap format to numeric format(gapit and farmcpu)'),
        ('hmp2MVP', 'transform hapmap format to MVP genotypic format'),
        ('genKinship', 'using gemma to generate centered kinship matrix'),
        ('genPCA10', 'using tassel to generate the first 10 PCs'),
        ('subsampling', 'resort hmp file by extracting part of samples')
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def judge(ref, alt, genosList):
    newlist = []
    for k in genosList:
        #if len(set(k))==1 and k[0] == ref:
        if k=='AA':
            newlist.append('0')
        #elif len(set(k))==1 and k[0] == alt:
        elif k=='BB':
            newlist.append('2')
        #elif len(set(k))==2 :
        elif k=='AB' :
            newlist.append('1')
        else:
            print 'genotype error !'
    return newlist

def hmp2BIMBAM(args):
    """
    %prog hmp bimbam_prefix
    
    Convert hmp genotypic data to bimnbam datasets (*.mean and *.annotation).
    """
    p = OptionParser(hmp2BIMBAM.__doc__)
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    
    hmp, bim_pre = args
    f1 = open(hmp)
    f1.readline()
    f2 = open(bim_pre+'.mean', 'w')
    f3 = open(bim_pre+'.annotation', 'w')
    for i in f1:
        j = i.split()
        rs = j[0]
        ref, alt = j[1].split('/')[0], j[1].split('/')[1]
        newNUMs = judge(ref, alt, j[11:])
        newline = '%s,%s,%s,%s\n'%(rs, ref, alt, ','.join(newNUMs))
        f2.write(newline)
        pos = j[3]
        chro = j[2]
        f3.write('%s,%s,%s\n'%(rs, pos, chro))
    f1.close()
    f2.close()
    f3.close()

def hmp2MVP(args):
    """
    %prog hmp MVP_prefix
    
    Convert hmp genotypic data to bimnbam datasets (*.numeric and *.map).
    """
    p = OptionParser(hmp2MVP.__doc__)
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    
    hmp, mvp_pre = args
    f1 = open(hmp)
    f1.readline()
    f2 = open(mvp_pre+'.numeric', 'w')
    f3 = open(mvp_pre+'.map', 'w')
    f3.write('SNP\tChrom\tBP\n')
    for i in f1:
        j = i.split()
        rs = j[0]
        ref, alt = j[1].split('/')[0], j[1].split('/')[1]
        newNUMs = judge(ref, alt, j[11:])
        newline = '\t'.join(newNUMs)+'\n'
        f2.write(newline)
        chro,pos = j[2],j[3]
        f3.write('%s\t%s\t%s\n'%(rs,chro, pos))
    f1.close()
    f2.close()
    f3.close()

def hmp2numeric(args):
    """
    %prog hmp numeric_prefix
    
    Convert hmp genotypic data to numeric datasets (*.GD and *.GM).
    """
    p = OptionParser(hmp2numeric.__doc__)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    hmp, num_pre = args
    f1 = open(hmp)
    f2 = open(num_pre+'.GD', 'w')
    f3 = open(num_pre+'.GM', 'w')

    hmpheader = f1.readline()
    preConverted = []
    header = 'taxa\t%s'%('\t'.join(hmpheader.split()[11:]))
    preConverted.append(header.split())

    f3.write('SNP\tChromosome\tPosition\n')
    for i in f1:
        j = i.split()
        taxa,ref,alt,chro,pos = j[0],j[1][0],j[1][2],j[2],j[3]
        f3.write('%s\t%s\t%s\n'%(taxa, chro, pos))
        newNUMs = judge(ref, alt, j[11:])
        newline = '%s\t%s'%(taxa, '\t'.join(newNUMs))
        preConverted.append(newline.split())
    rightOrder = map(list, zip(*preConverted))
    for i in rightOrder:
        newl = '\t'.join(i)+'\n'
        f2.write(newl)
    f1.close()
    f2.close()

def genKinship(args):
    """
    %prog genotype.mean
    
    Generate centered kinship matrix file
    """
    p = OptionParser(genKinship.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help()) 
    geno_mean, = args
    # generate a fake bimbam phenotype based on genotype
    f = open(geno_mean)
    num_SMs = len(f.readline().split(',')[3:])
    f1 = open('tmp.pheno', 'w')
    for i in range(num_SMs):
        f1.write('sm%s\t%s\n'%(i, 20))
    f.close()
    f1.close()

    mean_prefix = geno_mean.replace('.mean','')
    # the location of gemma executable file
    gemma = op.abspath(op.dirname(__file__))+'/../apps/gemma'

    cmd = '%s -g %s -p %s -gk 1 -outdir . -o gemma.centered.%s' \
        %(gemma, geno_mean, 'tmp.pheno', mean_prefix)
    print('The kinship command running on the local node:\n%s'%cmd)
   
    h = SlrumHeader()
    header = h.header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f = open('%s.kinship.slurm'%mean_prefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.kinship.slurm has been created, you can sbatch your job file.'%mean_prefix)

def genPCA10(args):
    """
    %prog hmp
    
    Generate first 10 PCs
    """
    p = OptionParser(genPCA10.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    hmp, = args
    out_prefix = hmp.replace('.hmp', '')
    cmd = 'run_pipeline.pl -Xms56g -Xmx58g -fork1 -h %s -PrincipalComponentsPlugin -ncomponents 10 -covariance true -endPlugin -export %s.PCA10 -runfork1'%(hmp, out_prefix)
    h = SlrumHeader()
    h.AddModule(('java/1.8', 'tassel/5.2'))
    header = h.header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f = open('%s.PCA10.slurm'%out_prefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.PCA10.slurm has been created, you can sbatch your job file.'%out_prefix)

def MAFandparalogous(row):
    """
    function to filter MAF and paralogous SNPs
    """
    ref, alt = row[1].split('/')
    genos = row[11:]
    refnum, altnum, refaltnum = (genos=='AA').sum(), (genos=='BB').sum(), (genos=='AB').sum()
    totalA = float((refnum + altnum + refaltnum)*2)
    #print(refnum, altnum, refaltnum)
    af1, af2 = (refnum*2 + refaltnum)/totalA, (altnum*2 + refaltnum)/totalA
    #print(af1, af2)
    maf = True if min(af1, af2) >=0.01 else False
    paralogous = True if refaltnum < min(refnum, altnum) else False
    TF = maf and paralogous
    #print(maf, paralogous)
    return TF

def subsampling(args):
    """
    %prog hmp SMs_file out_prefix

    In the SMs_file, please put sample name row by row, only the first column will be read. If file had multiple columns, use space or tab as the separator.
    """
    import pandas as pd
    import numpy as np

    p = OptionParser(subsampling.__doc__)
    p.add_option('--header', default=False,
        help = 'whether a head exist in your sample name file')
    p.add_option('--filter', default=True,
        help = 'if True, SNPs with maf <= 0.01 and paralogous SNPs will be removed automatically')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
   
    hmp, SMs_file, out_prefix = args
    hmp_df = pd.read_csv(hmp, delim_whitespace=True)
    SMs_df = pd.read_csv(SMs_file, delim_whitespace=True) \
        if opts.header \
        else pd.read_csv(SMs_file, delim_whitespace=True, header=None)
    SMs_df = SMs_df.dropna(axis=0)
    SMs = SMs_df.iloc[:,0].astype('str')

    hmp_header, hmp_SMs = hmp_df.columns[0:11].tolist(), hmp_df.columns[11:]
    
    excepSMs = SMs[~SMs.isin(hmp_SMs)]
    if len(excepSMs)>0:
        print('Warning: could not find %s in original samples, proceed anyway. \
            You may need to edit your phenotype file after finishing'%excepSMs)

    targetSMs = SMs[SMs.isin(hmp_SMs)].tolist()
    hmp_header.extend(targetSMs)
    new_hmp = hmp_df[hmp_header] 
    TFs = new_hmp.apply(MAFandparalogous, axis=1)
    final_hmp = new_hmp.loc[TFs] \
        if opts.filter \
        else new_hmp
    final_hmp.to_csv('%s.hmp'%out_prefix, index=False, sep='\t')

if __name__ == '__main__':
    main()
