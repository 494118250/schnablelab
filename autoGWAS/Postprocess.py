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
faOneRecord = op.abspath(op.dirname(__file__))+'/../apps/faOneRecord' 
def main():
    actions = (
        ('fetchMAF', 'calculate the MAFs of selected SNPs'),
        ('SigSNPs', 'fetch the first n significant SNPs'),
        ('fetchEVs', 'fetch effect sizes of selected SNPs'),
        ('fetchLinkedSNPs', 'fetch highly linked SNPs'),
        ('fetchGenoVCF', 'fetch genotypes for SNPs from vcf file'),
        ('fetchGene', 'fetch genes of selected SNPs from significant SNP list'),
        ('fetchFunc', 'fetch functions of candidate genes'),
        ('fetchProSeq', 'fetch corresponding sequences of condidated genes'),
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
    
    Calculate MAF of SNPs in a file where SNPs are listed row by row.
    If there are multiple columns, use space or tab as separators
    """
    p = OptionParser(fetchMAF.__doc__)
    p.add_option('--header', default = 'no', choices=('yes', 'no'),
        help = 'specify if there is a header in your SNP list file')
    p.add_option('--col_idx', default = '0',
        help = 'specify the SNP column')
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    
    SNPlist, hmp = args
    df = pd.read_csv(SNPlist, delim_whitespace=True, header=None) \
        if opts.header == 'no' \
        else pd.read_csv(SNPlist, delim_whitespace=True)
    SNPs = df.iloc[:, int(opts.col_idx)]
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
    p.add_option('--col_idx', default = '0',
        help = 'specify the SNP column')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    SNPlist, farmResult = args
    df = pd.read_csv(SNPlist, delim_whitespace=True, header=None) \
        if opts.header == 'no' \
        else pd.read_csv(SNPlist, delim_whitespace=True)
    SNPs = df.iloc[:, int(opts.col_idx)]
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

def SigSNPs(args):
    """
    %prog gwas_results output 
    extract the first N significant SNPs from GWAS result. The results will be saved to software.causalSNPs.csv
    """
    p = OptionParser(SigSNPs.__doc__)
    p.add_option('--MeRatio', default = '1',
        help = "specify the ratio of independent SNPs, maize is 0.32, sorghum is 0.53")
    p.add_option('--chromosome', default = 'all',
        help = "specify chromosome, such 1, 2. 'all' means genome level")
    p.add_option('--software', default = 'gemma', choices=('gemma', 'gapit', 'farmcpu', 'mvp'),
        help = 'specify which software generates the GWAS result')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    gwas,output, = args
    if opts.software == 'gemma':
        df = pd.read_csv(gwas, delim_whitespace=True, usecols=['chr', 'rs', 'ps', 'p_lrt'])
        cutoff = 0.05/(float(opts.MeRatio) * df.shape[0])
        print('significant cutoff: %s'%cutoff)
        df['chr'] = df['chr'].astype('str')
        df = df if opts.chromosome=='all' else df[df['chr']==opts.chromosome]
        df = df[['rs', 'chr', 'ps', 'p_lrt']]
        df[df['p_lrt'] < cutoff].to_csv(output, index=False, sep='\t')

    elif opts.software == 'farmcpu':
        df = pd.read_csv(gwas, usecols=['SNP', 'Chromosome', 'Position', 'P.value'])
        cutoff = 0.05/(float(opts.MeRatio) * df.shape[0])
        print('significant cutoff: %s'%cutoff)
        df['Chromosome'] = df['Chromosome'].astype('str')
        df = df if opts.chromosome=='all' else df[df['chr']==opts.chromosome]
        df[df['P.value'] < cutoff].to_csv(output, index=False, sep='\t')

    elif opts.software == 'gapit':
        df = pd.read_csv(gwas, usecols=['SNP', 'Chromosome', 'Position ', 'P.value'])
        cutoff = 0.05/(float(opts.MeRatio) * df.shape[0])
        print('significant cutoff: %s'%cutoff)
        df['Chromosome'] = df['Chromosome'].astype('str')
        df = df if opts.chromosome=='all' else df[df['chr']==opts.chromosome]
        df[df['P.value'] < cutoff].to_csv(output, index=False, sep='\t')
    else:
        pass # for mvp
    print('Done! Check %s'%output)
        
def fetchLinkedSNPs(args):
    """
    %prog SNPlist(only read 1st col) bed_prefix r2_cutoff output_prefix

    extract linked SNPs using plink
    """
    p = OptionParser(fetchLinkedSNPs.__doc__)
    p.set_slurm_opts(array=False)
    p.add_option('--header', default = 'yes', choices=('yes', 'no'),
        help = 'specify if there is a header in your SNP list file')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())

    SNPlist, bedprefix, cutoff, output_prefix, = args
    df = pd.read_csv(SNPlist, delim_whitespace=True, header=None) \
        if opts.header == 'no' \
        else pd.read_csv(SNPlist, delim_whitespace=True)
    SNPs = df.iloc[:, 0]
    pre = SNPlist.split('.')[0]
    SNPsfile = SNPs.to_csv('%s.SNPs_list.csv'%pre, index=False)
    cmd = '%s --bfile %s --r2 --ld-snp-list %s.SNPs_list.csv --ld-window-kb 5000 --ld-window 99999 --ld-window-r2 %s --noweb --out %s\n'%(plink, bedprefix, pre, cutoff, output_prefix)
    print('command run on local:\n%s'%cmd)
    f = open('%s.slurm'%output_prefix, 'w')
    h = Slurm_header
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f.write(header)
    f.close()
    print('Job file has been generated. You can submit: sbatch -p jclarke %s.slurm'%output_prefix)

def fetchGenoVCF(args):
    """
    %prog SNP_list_file VCF output

    extract genotypes for a buch of SNPs from VCF
    """     
    p = OptionParser(fetchGenoVCF.__doc__)
    p.add_option('--header', default = 'yes', choices=('yes', 'no'),
        help = 'specify if there is a header in your SNP list file')
    p.add_option('--column', default = '0',
        help = 'specify which column is your SNP column 0-based')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    snplist,vcf,output, = args

    df = pd.read_csv(snplist, delim_whitespace=True) \
        if opts.header=='yes' \
        else pd.read_csv(snplist, delim_whitespace=True, header=None)
    SNPs = df.iloc[:,int(opts.column)]
    SNP_keys = '\t'+SNPs+'\t'
    SNP_keys.to_csv('SNP_keys.csv', index=False)
    print('grep keys generated: SNP_keys.csv')
 
    cmd1 = 'zgrep -f SNP_keys.csv %s > SNPs_keys.tmp.vcf'%(vcf) \
        if vcf.endswith('gz')\
        else 'grep -f SNP_keys.csv %s > SNPs_keys.tmp.vcf'%(vcf)
    call(cmd1, shell=True)
    print('grep vcf done: SNPs_keys.tmp.vcf')

    cmd2 = "zgrep -m 1 -P '#CHROM\tPOS' %s > header.vcf"%(vcf) \
        if vcf.endswith('gz')\
        else "zgrep -m 1 -P '#CHROM\tPOS' %s > header.vcf"%(vcf)
    call(cmd2, shell=True)
    vcf_header = open('header.vcf')
    df_header = vcf_header.readline().split()
    print('header done: header.vcf')

    df_geno = pd.read_csv('SNPs_keys.tmp.vcf', delim_whitespace=True, header=None)
    df_geno.columns = df_header
    df_geno0 = df_geno[['#CHROM','POS','ID','REF','ALT']]
    df_geno1 = df_geno[df_geno.columns[9:]]
    df_geno2 = df_geno1.applymap(lambda x: x.split(':')[0])
    df_geno_final = pd.concat([df_geno0, df_geno2], axis=1)
    df_geno_final.to_csv(output, index=False)
    print('genotype processing done: %s'%output)

def fetchGene(args):
    """
    %prog SNPlist gene.gff3 output_prefix

    extract gene names
    """
    p = OptionParser(fetchGene.__doc__)
    p.add_option('--header', default = 'yes', choices=('yes', 'no'),
        help = 'specify if there is a header in your SNP list file')
    p.add_option('--col_idx', default = '3,4,5',
        help = 'specify the index of Chr, Pos, SNP columns')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    SNPlist, gff, out_prefix, = args

    df0 = pd.read_csv(SNPlist, delim_whitespace=True, header=None) \
        if opts.header == 'no' \
        else pd.read_csv(SNPlist, delim_whitespace=True)
    cols = [df0.columns[int(i)] for i in opts.col_idx.split(',')]
    df0 = df0[cols]
    df0.columns = ['chr', 'pos', 'snp']
    df0 = df0.sort_values(['chr', 'pos'])
    df0 = df0.reset_index(drop=True)

    df1 = pd.read_csv(gff, sep='\t', header=None)
    df1['gene'] = df1.iloc[:,8].str.split('gene:').str.get(1).str.split(';').str.get(0)
    df1 = df1[[0,3,4, 'gene']]
    df1.columns = ['chr', 'start', 'end', 'gene']
    f0 = open('%s.info'%out_prefix, 'w')
    f1 = open('%s.genes'%out_prefix, 'w')

    for g in df0.groupby('chr'):
        chrom = str(g[0])
        f0.write('Chromosome: %s\n'%chrom)
        SNPs = list(g[1]['snp'].unique())
        f0.write('Causal SNPs(%s):\n %s\n'%(len(SNPs), ','.join(SNPs)))
        Genes = []
        for pos in g[1]['pos']:
            print('SNP position: %s'%pos)
            df2 = df1[df1['chr'] == chrom]
            df2['dist'] = np.abs(df2['end'] - df2['start'])
            df2['st_dist'] = np.abs(pos - df2['start'])
            df2['ed_dist'] = np.abs(pos - df2['end'])
            min_idx_1, min_idx_2 = df2['st_dist'].idxmin(), df2['ed_dist'].idxmin()
            min_val_1, min_val_2 = df2['st_dist'].min(), df2['ed_dist'].min()

            if (min_idx_1 == min_idx_2) and \
                (min_val_1 <=  df2.loc[min_idx_1, :]['dist']) and \
                (min_val_2 <=  df2.loc[min_idx_1, :]['dist']):
                gene = df2.loc[min_idx_1,'gene']
                if gene in Genes:
                    pass
                else: 
                    Genes.append(gene)
            else:
                if pos > df2.loc[min_idx_1, :][3]:
                    gene = df2.loc[[min_idx_1, min_idx_1+1], 'gene'].tolist()
                elif pos < df2.loc[min_idx_1, :][3]:
                    gene = df2.loc[[min_idx_1-1, min_idx_1], 'gene'].tolist()
                else:
                    print('wrong position!!!')
                for i in gene:
                    if i in Genes:
                        pass
                    else: 
                        Genes.append(i)
        f0.write('Candidate genes(%s):\n %s\n\n'%(len(Genes), ','.join(Genes)))
        
        for  i in Genes:
            f1.write(i+'\n')
    f0.close()
    f1.close()
    print('Done! Check results:\n%s\n%s\n'%(out_prefix+'.info', out_prefix+'.genes'))

def fetchFunc(args):
    """
    %prog GeneList FunctionFile output

    extract gene functions
    """
    p = OptionParser(fetchFunc.__doc__)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    genelist, FuncFile, output, = args
    cmd = 'grep -f %s %s > %s'%(genelist, FuncFile, output)
    call(cmd, shell=True)
    print('Done! Check file: %s'%output)
    
def fetchProSeq(args):
    """
    %prog GeneList seq_file output_prefix

    extract protein sequences of candidate genes
    """
    p = OptionParser(fetchProSeq.__doc__)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    genelist, SeqFile, out_prefix, = args
    cmd = "grep '>' %s|cut -d ' ' -f 1|cut -d '>' -f 2 > AllGene.names"%SeqFile
    call(cmd, shell=True)

    df_Genes = pd.read_csv(genelist, header=None)
    df_Trans = pd.read_csv('AllGene.names', header=None)
    df_Trans['gene'] = df_Trans[0].str.split('_').str.get(0)
    df1 = df_Trans[df_Trans['gene'].isin(df_Genes[0])]
    df1['gene'] = df1['gene'].astype('category')
    df1['gene'].cat.set_categories(df_Genes[0].tolist(), inplace=True)
    df2 = df1.sort_values(['gene',0]).reset_index(drop=True)
    df2[0].to_csv('%s.ProSeq.names'%out_prefix, index=False, header=False)
    
    for i in list(df2[0]):
        print('fetching %s'%i)
        cmd = "%s %s %s >> %s"%(faOneRecord, SeqFile, i, out_prefix+'.seqs')
        call(cmd, shell=True)
    print('Done!')
    

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
