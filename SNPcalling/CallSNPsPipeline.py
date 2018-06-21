# -*- coding: UTF-8 -*-

"""
Call SNPs on tGBS data including combine replicates, trim, align, and SNP call.
"""

import os
import os.path as op
import sys
import pandas as pd
import numpy as np
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header
from subprocess import call

def main():
    actions = (
        ('CombineRep', 'combine fastq.gz files for the same sample'),
        ('Trim', 'perform quality control on raw fq.gz file'),
        ('Align', 'align reads to genome'),
        ('Sam2Bam', 'convert sam file to bam format'),
        ('SortBam', 'Sort bam files'),
        ('IndexBam', 'generate the index file on bam'),
        ('SNPsCall', 'call SNPs'),
)
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def CombineRep(args):
    """
    %prog CombinRep dir
    combine all fg.gz files for same sample
    """
    p = OptionParser(CombineRep.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    fqs = [i for i in os.listdir(mydir) if i.endswith('fq.gz')]
    fqs = sorted(fqs, key = lambda x: int(x.split('.')[0].split('_')[0].split('R')[0]))
    SMs = [x.split('.')[0].split('_')[0].split('R')[0] for x in fqs]
    mydf = pd.DataFrame(dict(zip(['SM', 'FNs'], [SMs, fqs])))
    mygrpdf = mydf.groupby('SM').agg(['count', lambda x: ' '.join(x)])
    f = open('combine_fqs.sh', 'w')
    for sm in mygrpdf.index:
        n, fns = mygrpdf.loc[sm,:]
        cmd = 'cat %s > %s.cbd.fq.gz\n'%(fns, sm)
        f.write(cmd)
    f.close()
    cmd1 = 'chmod +x combine_fqs.sh\n'
    cmd2 = './combine_fqs.sh\n'
    header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
    header += cmd1
    header += cmd2
    f = open('CombineFQs.slurm'%prefix, 'w')
    f.write(header)
    f.close()
    print('slurm file CombineFQs.slurm has been created, you can sbatch your job file.'%prefix)


def Trim(args):
    """
    %prog Trim dir
    quality control on raw fq.gz using Trimmomatric
    """
    p = OptionParser(Trim.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    allfiles = [i for i in os.listdir(mydir) if i.endswith('.fq.gz')]
    print 'Total %s fastq.gz files'%len(allfiles)
    for i in allfiles:
        sm = i.split('.')[0]
        cmd1 = 'java -jar $TM_HOME/trimmomatic.jar SE %s %s CROP:185 SLIDINGWINDOW:4:15 MINLEN:30'%(i, sm+'.trimed.fq\n')
        cmd2 = 'gzip %s'%(sm+'.trimed.fq\n')
        header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
        header += cmd1
        header += cmd2
        jobfile = '%s.trimc.slurm'%sm
        f = open(jobfile, 'w')
        f.write(header)
        f.close()
    print('slurm files *.trimed.slurm has been created, you can sbatch your job file.'%prefix)
        

def Align(args):
    """
    %prog Align dir
    Align reads to genome
    """
    p = OptionParser(Align.__doc__)
    p.add_option('--RefVersion', default = '1', choices=('1', '3'),
        help = 'select the reference genome version')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    allfiles = [i for i in os.listdir('.') if i.endswith('.trimed.fq.gz') and not op.isfile(i.split('.')[0]+'.sam')]
    print 'Total %s fq.gz files'%len(allfiles)
    for i in allfiles:
        SM = i.split('.')[0]
        R = r"'@RG\tID:%s\tSM:%s'"%(SM, SM)
        samoutput = '%s.sam'%SM
        cmd = 'bwa mem -R %s %s %s > %s \n'%(R, '/work/schnablelab/cmiao/SorghumGWAS/shared_files/references/Sbicolor_313_v3.0.fa', i, samoutput)\
            if opts.RefVersion == '3'\
            else 'bwa mem -R %s %s %s > %s \n'%(R, '/work/schnablelab/cmiao/SorghumGWAS/shared_files/references/Sbicolor_79.fa', i, samoutput)
        header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
        header += cmd1
        jobfile = '%s.bwa.slurm'%SM
        f = open(jobfile, 'w')
        f.write(header)
        f.close()
    print('slurm files *.bwa.slurm has been created, you can sbatch your job file.'%prefix)
        
        
def Sam2Bam(args):
    """
    %prog Sam2Bam dir
    Align reads to genome
    """
    p = OptionParser(Sam2Bam.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    allfiles = [i for i in os.listdir(mydir) if i.endswith('sam')]
    print 'Total %s sam files'%len(allfiles)
    for i in allfiles:
        SM = i.split('.')[0]
        output = '%s.bam'%SM
        cmd = 'samtools view -bS %s > %s\n'%(i, output)
        header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
        header += cmd
        jobfile = '%s.sam2bam.slurm'%SM
        f = open(jobfile, 'w')
        f.write(header)
        f.close()
    print('slurm files *.sam2bam.slurm has been created, you can sbatch your job file.'%prefix)
    
def SortBam(args):
    """
    %prog SortBam dir
    sort all the bam files
    """
    p = OptionParser(SortBam.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    allfiles = [i for i in os.listdir(mydir) if i.endswith('bam')]
    print 'Total %s bam files'%len(allfiles)
    for i in allfiles:
        SM = i.split('.')[0]
        output = '%s.sorted'%SM
        cmd = 'samtools sort %s %s\n'%(i, output)
        header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
        header += cmd
        jobfile = '%s.sortbam.slurm'%SM
        f = open(jobfile, 'w')
        f.write(header)
        f.close()
    print('slurm files *.sortbam.slurm has been created, you can sbatch your job file.'%prefix)

def IndexBam(args):
    """
    %prog IndexBam dir
    create the index for bam files
    """
    p = OptionParser(IndexBam.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    allfiles = [i for i in os.listdir(mydir) if i.endswith('sorted.bam')]
    print 'Total %s sorted.bam files'%len(allfiles)
    for i in allfiles:
        SM = i.split('.')[0]
        cmd = 'samtools index %s\n'%i
        header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
        header += cmd
        jobfile = '%s.idx.slurm'%SM
        f = open(jobfile, 'w')
        f.write(header)
        f.close()
    print('slurm files *.idx.slurm has been created, you can sbatch your job file.'%prefix)
    
def SNPsCall(args):
    """
    %prog SNPsCall ref info
    create the index for bam files
    """
    p = OptionParser(IndexBam.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    ref, info, = args
    allfiles = [i for i in os.listdir('.') if i.endswith('sorted.bam')]
    print 'Total %s sorted.bam files'%len(allfiles)
    f1 = open('bamfiles.fb.list', 'w')
    for i in allfiles :
        f1.write(i + '\n')
    f1.close()

    f2 = open(info)
    chrlist = [i.rstrip() for i in f2]
    for seq in chrlist:
        cmd = '/work/schnablelab/cmiao/SorghumGWAS/scripts/freebayes/bin/freebayes -r %s -f %s -C 1 -L bamfiles.fb.list > %s\n'%(seq, ref, "_".join(seq.split(':'))+'.vcf')
        header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix,opts.prefix)
        header += cmd
        jobfile = '%s.fb.slurm'%("_".join(seq.split(':')))
        f = open(jobfile, 'w')
        f.write(header)
        f.close()
    print('slurm files *.fb.slurm has been created, you can sbatch your job file.'%prefix)

if __name__ == "__main__":
    main()
