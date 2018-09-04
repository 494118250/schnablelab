# -*- coding: UTF-8 -*-

"""
Split a big file using sed.
Find more details at cnblog:
www.cnblogs.com/freemao/p/7076127.html
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob, iglob
from JamesLab.apps.natsort import natsorted
import subprocess
from JamesLab.apps.header import Slurm_header

# the location of linkimpute, beagle executable
lkipt = op.abspath(op.dirname(__file__)) + '/../apps/LinkImpute.jar'
begle = op.abspath(op.dirname(__file__)) + '/../apps/beagle.21Jan17.6cc.jar'
tassel = op.abspath(op.dirname(__file__)) + '/../apps/tassel-5-standalone/run_pipeline.pl'


def main():
    actions = (
        ('splitVCF', 'split a vcf to several smaller files with equal size'),
        ('combineVCF', 'combine split vcfs'),
        ('impute', 'impute vcf using beagle or linkimpute'),
        ('vcf2hmp', 'convert vcf to hmp format'),
        ('FixIndelHmp', 'fix the indels problems in hmp file converted from tassel'),
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def splitVCF(args):
    """
    %prog splitVCF N vcf
    split vcf to N smaller files with equal size
    """
    p = OptionParser(splitVCF.__doc__)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    N, vcffile, = args
    N = int(N)
    prefix = vcffile.split('.')[0]
    cmd_header = "sed -ne '/^#/p' %s > %s.header" % (vcffile, prefix)
    subprocess.call(cmd_header, shell=True)
    child = subprocess.Popen('wc -l %s' % vcffile, shell=True, stdout=subprocess.PIPE)
    total_line = int(child.communicate()[0].split()[0])
    print('total %s lines' % total_line)
    step = total_line / N
    print(1)
    cmd_first = "sed -n '1,%sp' %s > %s.1.vcf" % (step, vcffile, prefix)
    subprocess.call(cmd_first, shell=True)
    for i in range(2, N):
        print(i)
        st = (i - 1) * step + 1
        ed = i * step
        cmd = "sed -n '%s,%sp' %s > %s.%s.tmp.vcf" % (st, ed, vcffile, prefix, i)
        subprocess.call(cmd, shell=True)
    print(i + 1)
    cmd_last = "sed -n '%s,%sp' %s > %s.%s.tmp.vcf" % ((ed + 1), total_line, vcffile, prefix, (i + 1))
    subprocess.call(cmd_last, shell=True)
    for i in range(2, N + 1):
        cmd_cat = 'cat %s.header %s.%s.tmp.vcf > %s.%s.vcf' % (prefix, prefix, i, prefix, i)
        subprocess.call(cmd_cat, shell=True)


def combineVCF(args):
    """
    %prog combineVCF N pattern
    combine split vcf (1-based) files to a single one. Pattern example: hmp321_agpv4_chr9.%s.beagle.vcf
    """

    p = OptionParser(combineVCF.__doc__)
    p.add_option('--header', default='yes', choices=('yes', 'no'),
                 help='choose whether add header or not')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    N, vcf_pattern, = args
    N = int(N)
    new_f = vcf_pattern.replace('%s', '').replace('..', '.')
    print('output file: %s' % new_f)

    f = open(new_f, 'w')

    fn1 = open(vcf_pattern % 1)
    print(1)
    if opts.header == 'yes':
        for i in fn1:
            f.write(i)
    else:
        for i in fn1:
            if not i.startswith('#'):
                f.write(i)
    fn1.close()
    for i in range(2, N + 1):
        print(i)
        fn = open(vcf_pattern % i)
        for j in fn:
            if not j.startswith('#'):
                f.write(j)
        fn.close()
    f.close()


def impute(args):
    """
    %prog impute vcf
    impute missing data in vcf using beagle or linkimpute
    """
    p = OptionParser(impute.__doc__)
    p.set_slurm_opts(jn=True)
    p.add_option('--software', default='linkimpute', choices=('linkimpute', 'beagle'),
                 help='specify the imputation software')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    vcffile, = args
    prefix = '.'.join(vcffile.split('.')[0:-1])
    new_f = prefix + '.impt.vcf'

    cmd = 'java -Xss100m -Xmx18G -jar %s -v %s %s \n' % (lkipt, vcffile, new_f) \
        if opts.software == 'linkimpute' \
        else 'java -Xss16G -Xmx18G -jar %s gt=%s out=%s.beagle \n' % (begle, vcffile, prefix)
    header = Slurm_header % (opts.time, 20000, opts.prefix, opts.prefix, opts.prefix)
    header += 'module load java/1.7 \n' \
        if opts.software == 'linkimpute' \
        else 'module load java/1.8 \n'
    header += cmd
    f = open('%s.%s.slurm' % (prefix, opts.software), 'w')
    f.write(header)
    f.close()
    print('slurm file %s.%s.slurm has been created! ' % (prefix, opts.software))


def vcf2hmp(args):
    """
    %prog vcf2hmp vcf
    convert vcf generated from beagle to hmp format using tassel
    """
    p = OptionParser(vcf2hmp.__doc__)
    p.set_slurm_opts(jn=True)
    p.add_option('--version', default='2', choices=('1', '2'),
                 help='specify the hmp type. 1: hyploid. 2: diploid')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    vcffile, = args
    prefix = '.'.join(vcffile.split('.')[0:-1])
    cmd = '%s -Xms512m -Xmx10G -fork1 -vcf %s -export -exportType HapmapDiploid\n' % (tassel, vcffile) \
        if opts.version == '2' \
        else '%s -Xms512m -Xmx10G -fork1 -vcf %s -export -exportType Hapmap\n' % (tassel, vcffile)
    header = Slurm_header % (opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += 'module load java/1.8\n'
    header += cmd
    f = open('%s.vcf2hmp.slurm' % prefix, 'w')
    f.write(header)
    f.close()
    print('slurm file %s.vcf2hmp.slurm has been created, you can submit your job file.' % prefix)


def FixIndelHmp(args):
    """
    %prog FixIndelHmp hmp
    Fix the InDels problems in hmp file generated from Tassel.
    """
    p = OptionParser(FixIndelHmp.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    hmpfile, = args
    prefix = '.'.join(hmpfile.split('.')[0:-1])

    f = open(hmpfile)
    f1 = open('%s.Findel.hmp' % prefix, 'w')

    bict = {'A': 'T', 'T': 'C', 'C': 'A', 'G': 'A'}
    for i in f:
        j = i.split()
        if '+' in j[1]:
            nb = bict[j[1][0]] if j[1][0] != '+' else bict[j[1][-1]]
            tail = '\t'.join(j[11:]) + '\n'
            n_tail = tail.replace('+', nb)
            head = '\t'.join(j[0:11])
            n_head = head.replace('/+', '/%s' % nb) \
                if j[1][0] != '+' \
                else head.replace('+/', '%s/' % nb)
            n_line = n_head + '\t' + n_tail
            f1.write(n_line)
        elif '-' in j[1]:
            nb = bict[j[1][0]] if j[1][0] != '-' else bict[j[1][-1]]
            tail = '\t'.join(j[11:]) + '\n'
            n_tail = tail.replace('-', nb)
            head = '\t'.join(j[0:11])
            n_head = head.replace('/-', '/%s' % nb) \
                if j[1][0] != '-' \
                else head.replace('-/', '%s/' % nb)
            n_line = n_head + '\t' + n_tail
            f1.write(n_line)
        else:
            f1.write(i)
    f.close()
    f1.close()


def downsampling(args):
    pass


if __name__ == "__main__":
    main()
