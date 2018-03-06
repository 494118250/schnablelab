# -*- coding: UTF-8 -*-

"""
create, submit, canceal jobs. 
Find more details at HCC document: 
<https://hcc-docs.unl.edu>
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob,iglob
from JamesLab.apps.natsort import natsorted
from subprocess import call

def main():
    actions = (
        ('submit', 'submit a batch of jobs or all of them'),
        ('quickjob', 'create a quick slurm job'),
        ('cancel', 'canceal running, pending or all jobs'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def submit(args):
    """
    %prog dir

    Submit part of job in the dir or all jobs
    """
    p = OptionParser(submit.__doc__)
    p.add_option("--pattern", default='*.slurm', 
                 help="specify the patter of your slurm job, remember to add quotes [default: %default]")
    p.add_option("--partition", default='jclarke', choices=('batch', 'jclarke'),
                help = "choose which partition you are going to submit [default: %default]")
    p.add_option("--range", default='all', 
                 help="exp: '0-10','all'. Values are included")
    opts, args = p.parse_args(args)
    if len(args) != 1:
        sys.exit(not p.print_help())

    folder, = args
    alljobs = ['sbatch -p jclarke %s'%i for i in glob(folder, opts.pattern)] \
        if opts.partition == 'jclarke' \
        else ['sbatch -p batch %s'%i for i in glob(folder, opts.pattern)]
    print("Total %s jobs under '%s'"%(len(alljobs), folder))

    if opts.range == 'all':
       for i in alljobs:
          print(i)
          call(i, shell=True)
    else:
        start, end = int(opts.range.split('-')[0]), int(jobrange.split('-')[1])
        if end <= len(all_jobs):
            for i in all_jobs[start-1 : end]:
                print(i)
                call(i, shell=True)
            print '%s of total %s were submitted. [%s to %s] this time.' \
                %(len(all_jobs[start-1 : end]), len(all_jobs), start, end)
        else:
            print 'jobs exceed the limit'

def quickjob(args):
    """
    %prog
    """
def cancel(args):
    """
    %prog
    """

if __name__ == "__main__":
    main()
