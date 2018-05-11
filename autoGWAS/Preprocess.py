# -*- coding: UTF-8 -*-

"""
Convert GWAS dataset to particular formats for GEMMA, GAPIT, FarmCPU, and MVP.
"""

import os.path as op
import sys
import pandas as pd
import numpy as np
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header
from subprocess import call

# the location of gemma executable file
gemma = op.abspath(op.dirname(__file__))+'/../apps/gemma'
plink = op.abspath(op.dirname(__file__))+'/../apps/plink'
tassel = op.abspath(op.dirname(__file__))+'/../apps/tassel-5-standalone/run_pipeline.pl'

def main():
    actions = (
        ('hmp2BIMBAM', 'transform hapmap format to BIMBAM format (GEMMA)'),
        ('hmp2numeric', 'transform hapmap format to numeric format(gapit and farmcpu)'),
        ('hmp2MVP', 'transform hapmap format to MVP genotypic format'),
        ('hmp2ped', 'transform hapmap format to plink ped format'),
        ('nine2zero', 'replace -9 in the ped file generated from tassel to 0!!!'),
        ('ped2bed', 'convert plink ped format to binary bed format'),
        ('genKinship', 'using gemma to generate centered kinship matrix'),
        ('genPCA10', 'using tassel to generate the first 10 PCs'),
        ('subsampling', 'resort hmp file by extracting part of samples'),
        ('downsampling', 'using part of SNPs when dataset is too large'),
        ('LegalHmp', 'convert illegal genotypes in hmp file to legal genotypes'),
        ('SortHmp', 'Sort hmp position in wired tassle way'),
        ('reorgnzTasselPCA', 'reorganize PCA results from TASSEL so it can be used in other software'),
        ('reorgnzGemmaKinship', 'reorganize kinship results from GEMMA so it can be used in other software'),
        ('genGemmaPheno', 'reorganize normal phenotype format to GEMMA'),
        ('combineHmp', 'combine split chromosome Hmps to a single large one'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def judge(ref, alt, genosList):
    newlist = []
    for k in genosList:
        if len(set(k))==1 and k[0] == ref:
        #if k=='AA':
            newlist.append('0')
        elif len(set(k))==1 and k[0] == alt:
        #elif k=='BB':
            newlist.append('2')
        elif len(set(k))==2 :
        #elif k=='AB' :
            newlist.append('1')
        else:
            print 'genotype error !'
    return newlist

def hmp2BIMBAM(args):
    """
    %prog hmp2BIMBAM hmp bimbam_prefix
    
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
    %prog hmp2MVP hmp MVP_prefix
    
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
    %prog hmp2numeric hmp numeric_prefix
    
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
    %prog genKinship genotype.mean
    
    Calculate kinship matrix file
    """
    p = OptionParser(genKinship.__doc__)
    p.add_option('--type', default = 1, choices=(1, 2),
        help = 'specify the way to calculate the relateness, 1: centered; 2: standardized')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help()) 
    geno_mean, = args
    # generate a fake bimbam phenotype based on genotype
    f = open(geno_mean)
    num_SMs = len(f.readline().split(',')[3:])
    mean_prefix = geno_mean.replace('.mean','')
    tmp_pheno = '%s.tmp.pheno'%mean_prefix
    f1 = open(tmp_pheno, 'w')
    for i in range(num_SMs):
        f1.write('sm%s\t%s\n'%(i, 20))
    f.close()
    f1.close()

    # the location of gemma executable file
    gemma = op.abspath(op.dirname(__file__))+'/../apps/gemma'

    cmd = '%s -g %s -p %s -gk %s -outdir . -o gemma.centered.%s' \
        %(gemma, geno_mean, tmp_pheno, opts.type, mean_prefix)
    print('The kinship command running on the local node:\n%s'%cmd)
   
    h = Slurm_header
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f = open('%s.kinship.slurm'%mean_prefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.kinship.slurm has been created, you can sbatch your job file.'%mean_prefix)

def hmp2ped(args):
    """
    %prog hmp

    Convert hmp to plink ped format using Tassel
    """
    p = OptionParser(hmp2ped.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    hmp,  = args
    prefix = '.'.join(hmp.split('.')[0:-1])
    cmd = '%s -Xms512m -Xmx38G -fork1 -h %s -export -exportType Plink\n'%(tassel, hmp)
    header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
    header += 'module load java/1.8\n'
    header += cmd
    f = open('%s.hmp2ped.slurm'%prefix, 'w')
    f.write(header)
    f.close()
    print('Job file has been created. You can submit: sbatch -p jclarke %s.hmp2ped.slurm'%prefix)

def nine2zero(args):
    """
    %prog old_ped new_ped

    Convert -9 to 0 in the ped genotype file
    """
    p = OptionParser(nine2zero.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    old_ped, new_ped,  = args
    f = open(old_ped)
    f1 = open(new_ped, 'w')
    for i in f:
        j = i.replace('-9\t', '0\t')
        f1.write(j)
    f.close()
    f1.close()
    print('Done!')


def ped2bed(args):
    """
    %prog ped_prefix

    Convert plink ped to binary bed format using Plink
    """
    p = OptionParser(ped2bed.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    ped_prefix,  = args
    cmd = '%s --noweb --file %s --make-bed --out %s\n'%(plink, ped_prefix, ped_prefix)
    print('run cmd on local:\n%s'%cmd)
    header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
    header += cmd
    f = open('%s.ped2bed.slurm'%ped_prefix, 'w')
    f.write(header)
    f.close()
    print('Job file has been created. You can submit: sbatch -p jclarke %s.ped2bed.slurm'%ped_prefix)

def LegalGeno(row):
    """
    function to recover illegal genotypes
    """
    ref, alt = row[1].split('/')
    ref = ref if len(ref)==1 else ref.replace(alt, '')[0]
    alt = alt if len(alt)==1 else alt.replace(ref, '')[0]
    genos = row[11:]
    newgenos = row.replace('AA',ref+ref).replace('BB',alt+alt).replace('AB', ref+alt)
    return newgenos

def LegalHmp(args):
    """
    %prog LegalHmp hmp
    
    Recover illegal genotypes in hmp file to legal genotypes
    """
    p = OptionParser(LegalHmp.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    hmp, = args

    df = pd.read_csv(hmp, delim_whitespace=True)
    df1 = df.apply(LegalGeno, axis=1)
    legal_fn = hmp.replace('.hmp','.legal.hmp')
    df1.to_csv(legal_fn, index=False, sep='\t')
    print('Finish! check %s'%legal_fn)

def SortHmp(args):
    """
    %prog SortHmp hmp

    Sort hmp in wired TASSEL way...
    """
    p = OptionParser(SortHmp.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    hmp, = args
    prefix = hmp.replace('.hmp','')
    out_prefix = hmp.replace('.hmp','')+'.sorted'
    cmd = 'run_pipeline.pl -Xms16g -Xmx18g -SortGenotypeFilePlugin -inputFile %s -outputFile %s -fileType Hapmap\n'%(hmp, out_prefix)
    cmd1 = 'mv %s %s'%(out_prefix+'.hmp.txt', out_prefix+'.hmp')

    h = Slurm_header
    h += 'module load java/1.8\n'
    h += 'module load  tassel/5.2\n'
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    header += cmd1
    f = open('%s.Sort.slurm'%prefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.Sort.slurm has been created, you can sbatch your job file.'%prefix)


def genPCA10(args):
    """
    %prog genPCA10 hmp
    
    Generate first 10 PCs using tassel
    """
    p = OptionParser(genPCA10.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    hmp, = args
    out_prefix = hmp.replace('.hmp', '')
    cmd = '%s -Xms18g -Xmx20g -fork1 -h %s -PrincipalComponentsPlugin -ncomponents 10 -covariance true -endPlugin -export 10PC.%s -runfork1'%(tassel, hmp, out_prefix)

    h = Slurm_header
    h += 'module load java/1.8\n'
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f = open('%s.PCA10.slurm'%out_prefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.PCA10.slurm has been created, you can sbatch your job file.'%out_prefix)

def reorgnzTasselPCA(args):
    """
    %prog reorgnzTasselPCA tasselPCA1

    Reorganize PCA result from TASSEL so it can be used in other software.
    There are three different PC formats: 
    gapit(header and 1st taxa column), farmcpu(only header), mvp/gemma(no header, no 1st taxa column)
    """
    p = OptionParser(reorgnzTasselPCA.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pc1, = args
    df = pd.read_csv(pc1, delim_whitespace=True, header=2)
    df1 = df[df.columns[1:]]
    prefix = '.'.join(pc1.split('.')[0:2])
    gapit_pca, farm_pca, gemma_pca = prefix+'.gapit', prefix+'.farmcpu',prefix+'.gemmaMVP'
    df.to_csv(gapit_pca, sep='\t', index=False)
    df1.to_csv(farm_pca, sep='\t', index=False)
    df1.to_csv(gemma_pca, sep='\t', index=False, header=False)
    print('finished! %s, %s, %s have been generated.'%(gapit_pca,farm_pca,gemma_pca))
    
def reorgnzGemmaKinship(args):
    """
    %prog reorgnzGemmaKinship GEMMAkinship hmp

    Reorganize kinship result from GEMMA so it can be used in other software, like GAPIT.
    The hmp file only provides the order of the smaple names.
    """
    p = OptionParser(reorgnzGemmaKinship.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    gemmaKin, hmpfile,  = args
    
    f = open(hmpfile)
    SMs = f.readline().split()[11:]
    f.close()
    f1 = open(gemmaKin)
    f2 = open('GAPIT.'+gemmaKin, 'w')
    for i,j in zip(SMs, f1):
        newline = i+'\t'+j
        f2.write(newline)
    f1.close()
    f2.close() 
    print("Finished! Kinship matrix file for GEMMA 'GAPIT.%s' has been generated."%gemmaKin)


def genGemmaPheno(args):
    """
    %prog genGemmaPheno normalPheno

    Change the phenotype format so that can be fed to GEMMA
    """
    p = OptionParser(genGemmaPheno.__doc__)
    p.add_option('--header', default=True,
        help = 'whether a header exist in your normal phenotype file')
    p.add_option('--sep', default='\t', choices=('\t', ','),
        help = 'specify the separator in your normal phenotype file')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    normalPheno, = args
    df = pd.read_csv(normalPheno, sep=opts.sep) \
        if opts.header==True \
        else pd.read_csv(normalPheno, sep=opts.sep, header=None)
    output = 'gemma.'+normalPheno
    df.iloc[:,1].to_csv(output, index=False, header=False)
    print('Finished! %s has been generated.'%output)



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
    %prog subsampling hmp SMs_file out_prefix

    In the SMs_file, please put sample name row by row, only the first column will be read. If file had multiple columns, use space or tab as the separator.
    """
    p = OptionParser(subsampling.__doc__)
    p.add_option('--header', default=False,
        help = 'whether a header exist in your sample name file')
    p.add_option('--filter', default=True,
        help = 'if True, SNPs with maf <= 0.01 and paralogous SNPs (bad heterozygous) will be removed automatically')
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

def downsampling(args):
    """
    %prog downsampling file

    Choose part of SNPs as mapping markers when the genotype dataset is huge
    """
    p = OptionParser(downsampling.__doc__)
    p.add_option('--downsize', default=10,
        help = 'specify the downsize scale.')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    myfile, = args
    new_f = '.'.join(myfile.split('.')[0:-1])+'.ds%s.hmp'%opts.downsize
    cmd = "sed -n '1~%sp' %s > %s"%(opts.downsize, myfile, new_f) 
    call(cmd, shell=True)

def combineHmp(args):
    """
    %prog combineHmp N pattern output
    combine split hmp (1-based) files to a single one. Pattern example: hmp321_agpv4_chr%s.hmp
    """

    p = OptionParser(combineHmp.__doc__)
    p.add_option('--header', default = 'yes', choices=('yes', 'no'),
        help = 'choose whether add header or not')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    N, hmp_pattern,new_f, = args
    N = int(N)

    f = open(new_f, 'w')

    fn1 = open(hmp_pattern%1)
    print(1)
    if opts.header == 'yes':
        for i in fn1:
            f.write(i)
    else:
        fn1.readline()
        for i in fn1:
            f.write(i)
    fn1.close()
    for i in range(2, N+1):
        print(i)
        fn = open(hmp_pattern%i)
        fn.readline()
        for j in fn:
            f.write(j)
        fn.close()
    f.close()

if __name__ == '__main__':
    main()
