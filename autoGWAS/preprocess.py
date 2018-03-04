# -*- coding: UTF-8 -*-

"""
Convert GWAS dataset to particular formats for GEMMA, GAPIT, FarmCPU, and MVP.
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispathcer, OptionParser
from JamesLab.apps.slurmhead import SlrumHeader

def main():
    actions = (
        ('hmp2BIMBAM', 'transform hapmap format to BIMBAM format'),
        ('hmp2numeric', 'transform hapmap format to numeric format'),
        ('hmp2MVP', 'transform hapmap format to MVP format')
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def hmp2BIMBAM(args):
    pass
def hmp2numeric(args):
    pass


if __name__ == '__main__':
    main()
