# -*- coding: UTF-8 -*-
"""
basic support for slurm job file header
"""

Header = '''#!/bin/sh
#SBATCH --time=%s:00:00          # Run time in hh:mm:ss
#SBATCH --mem-per-cpu=%s       # Maximum memory required per CPU (in megabytes)
#SBATCH --job-name=%s
#SBATCH --error=./%s.err
#SBATCH --output=./%s.out

'''
class SlrumHeader():
    """
    generate slurm header
    """
    def __init__(self):
        self.header = Header

    def AddModule(self, sn): # sn represent software name
        lml = 'module load %s \n'
        self.header += lml%sn    #lml: load module line
