"""
parse mstmap results
"""

import sys
from pathlib import Path
from schnablelab.formats.base import read_block
from schnablelab.apps.Tools import eprint
from schnablelab.apps.base import OptionParser, ActionDispatcher, SUPPRESS_HELP

def main():
    actions = (
        ('mstmap2allmaps', 'convert mstmap raw results to the allmaps inputfile format'),
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def mstmap2allmaps(args):
    """
    %prog mstmap2allmaps mstmap_fn allmaps_fn

    convert mstmap results to the file format Allmaps required
    """
    p = OptionParser(mstmap2allmaps.__doc__)
    p.add_option("-i", "--input", help=SUPPRESS_HELP)
    p.add_option("-o", "--output", help=SUPPRESS_HELP)
    p.add_option('--min_markers', default=10, type='int',
        help = 'set the cutoff of marker numbers in a linkage group')
    opts, args = p.parse_args(args)

    if len(args) != 2:
        sys.exit(not p.print_help())
    
    mst_in, allmp_out = args
    inputmstmap = opts.input or mst_in
    outputallmp = opts.output or allmp_out

    if Path(outputallmp).exists():
        eprint('EROOR: Filename collision. The fugure output file `{}` exists'.format(outputallmp)) 
    
    fp = open(inputmstmap)
    for header, seq in read_block(fp, "group "):
        lg_name = header.split()[-1]
        print(lg_name)

if __name__ == "__main__":
    main()
