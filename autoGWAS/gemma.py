# -*- coding: UTF-8 -*-

"""
Run GEMMA command or generate the coresponding slurm job file. Find details in GEMMA manual at <http://www.xzlab.org/software/GEMMAmanual.pdf>
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header
from JamesLab.apps.natsort import natsorted

# the location of gemma executable file
gemma = op.abspath(op.dirname(__file__))+'/../apps/gemma'

def main():
    actions = (
        ('GLM', 'Performe GWAS using general linear model'),
        ('MLM', 'Performe GWAS using mixed linear model '),
        # Visualization
        ('Manhattan', 'Draw the Manhanttan plot using GEMMA results'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def GLM(args):
    """
    %prog GLM GenoPrefix Pheno Outdir
    RUN automated GEMMA General Linear Model
    """ 
    p = OptionParser(GLM.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    GenoPrefix, Pheno, Outdir = args
    meanG, annoG = GenoPrefix+'.mean', GenoPrefix+'.annotation'
    outprefix = Pheno.split('.')[0]
    cmd = '%s -g %s -p %s -a %s -lm 4 -outdir %s -o %s' \
        %(gemma, meanG, Pheno, annoG, Outdir, outprefix)
    print('The command running on the local node:\n%s'%cmd)

    h = Slurm_header
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f = open('%s.glm.slurm'%outprefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.glm.slurm has been created, you can sbatch your job file.'%outprefix)


def MLM(args):
    """
    %prog MLM GenoPrefix('*.mean' and '*.annotation') Pheno Outdir
    RUN automated GEMMA Mixed Linear Model
    """ 
    p = OptionParser(MLM.__doc__)
    p.add_option('--kinship', default=False, 
        help = 'specify the relatedness matrix file name')
    p.add_option('--pca', default=False, 
        help = 'specify the principle components file name')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    GenoPrefix, Pheno, Outdir = args
    meanG, annoG = GenoPrefix+'.mean', GenoPrefix+'.annotation'
    outprefix = '.'.join(Pheno.split('.')[0:-1])
    cmd = '%s -g %s -p %s -a %s -lmm 4 -outdir %s -o %s' \
        %(gemma, meanG, Pheno, annoG, Outdir, outprefix)
    if opts.kinship:
        cmd += ' -k %s'%opts.kinship
    if opts.pca:
        cmd += ' -c %s'%opts.pca
    print('The command running on the local node:\n%s'%cmd)

    h = Slurm_header
    header = h%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += cmd
    f = open('%s.mlm.slurm'%outprefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.mlm.slurm has been created, you can sbatch your job file.'%outprefix)

def Manhattan(args):
    """
    %prog Manhattan GWAS_result Figure_title
    Mamhattan plot using GEMMA results
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib

    #matplotlib.style.use('ggplot')
    # Get current size
    fig_size = plt.rcParams["figure.figsize"]
    # Prints: [8.0, 6.0]
    #print "Current size:", fig_size
    # Set figure width to 12 and height to 9
    fig_size[0] = 14
    fig_size[1] = 8
    plt.rcParams["figure.figsize"] = fig_size
 
    p = OptionParser(Manhattan.__doc__)
    p.add_option('--pvalue', default=0.05, choices=(0.05, 0.01),
        help = 'choose the pvalue cutoff')
    p.add_option('--multipletest', default='bonferroni', choices=('bonferroni', 'adjust-bonferroni', 'fdr'),
        help = 'choose the type of multiple test')
    p.add_option('--ylim', type = 'int',
        help = 'specify the ylim of the figure')
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    GWASresult, title = args
    fields = ['chr', 'ps', 'p_wald', 'p_lrt', 'p_score']
    df = pd.read_csv(GWASresult, delim_whitespace=True, usecols=fields)
    df['MinusLog10p_wald'] = -np.log10(df['p_wald'])
    df['MinusLog10p_lrt'] = -np.log10(df['p_lrt'])
    df['MinusLog10p_score'] = -np.log10(df['p_score'])

    df_grouped = df.groupby(by='chr')
    groupkeys = list(df_grouped.groups.keys())
    groupkeys = natsorted(groupkeys)
    print(groupkeys)

    for typePvalue in ('MinusLog10p_wald','MinusLog10p_lrt','MinusLog10p_score'):

        fig1 = plt.figure()
        ax = fig1.add_subplot(111)
        colors = ['C0','C1','C2','C3','C4']
        x_labels, x_labels_pos = [], []
        maxPos = 0
        for num,name in enumerate(groupkeys):
            print(num, name)
            df1 = df_grouped.get_group(name).reset_index(drop=True)
            df1['xticks'] = df1['ps']+maxPos
            df1.plot(kind='scatter', x='xticks', y=typePvalue, s=4, color=colors[num % len(colors)], ax=ax)
            maxPos += df1['ps'].max()
            x_labels.append('Chr_%s'%(num+1))
            x_labels_pos.append((df1['xticks'].iloc[-1] - (df1['xticks'].iloc[-1] - df1['xticks'].iloc[0])/2))

        if opts.multipletest == 'bonferroni':
            cutoff = -np.log10(opts.pvalue/len(df))
        elif opts.multipletest == 'adjust-bonferroni':
            pass
        elif opts.multipletest == 'fdr':
            pass

        ax.axhline(cutoff)
        ax.set_xticks(x_labels_pos)
        ax.set_xticklabels(x_labels, fontsize='14',  fontweight='bold')
        ylim = opts.ylim \
            if opts.ylim \
            else np.ceil(df[typePvalue].max())+ .5
        ax.set_yticks(np.arange(0,ylim))
        ylabels = [str(int(i)) for i in np.arange(0,ylim)]
        ax.set_yticklabels(ylabels, fontsize='14',  fontweight='bold')
        patch = maxPos/120.0
        ax.set_xlim([-patch, maxPos+patch])
        ax.set_ylim(0, ylim)
        ax.set_xlabel('Chromosome', fontsize=20, fontweight='bold')
        ax.set_ylabel(r'$\mathrm{-log_{10}(Pvalue)}$', fontsize=18, fontweight='bold')
        ax.set_title(title,  fontsize = 25, fontweight='bold')
        plt.savefig('Mantattan.%s.%s.png'%(title, typePvalue.split('10')[-1]))
        #plt.savefig('Mantattan.%s.%s.pdf'%(title, typePvalue.split('10')[-1]))


if __name__ == "__main__":
    main()
