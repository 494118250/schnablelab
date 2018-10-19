"""
require personal terminal used for computation
"""
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser

def main():

    actions = (
        ('request_cpu', 'request cpu node'),
        ('request_gpu', 'request gpu node'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def request_cpu(args):
    """
    %prog  
    request a cpu node from hcc.
    """
    p = OptionParser(request_cpu.__doc__)
    p.add_option("--memory", default="10240",
                help="specify the how much memory [default: %default]")
    p.add_option("--time", default='20',
                help = "specify the time (hour) [default: %default]")
    opts, args = p.parse_args(args)
    if len(args) != 0:
        sys.exit(not p.print_help())

    cmd = 'srun --partition=jclarke --mem-per-cpu={memory} --ntasks-per-node=6 --nodes=1 --time={hour}:0:0 --pty $SHELL\n'.format(opts.memory, opts.time)
    print(cmd)

def request_gpu(args):
    """
    %prog
    request a gpu node from hcc.
    """
    p = OptionParser(request_gpu.__doc__)
    p.add_option("--memory", default="10000",
                help="specify the how much memory [default: %default]")
    p.add_option("--time", default='20',
                help = "specify the time (hour) [default: %default]")
    p.add_option("--model", default='p100', choices=(gpu_p100, gpu_k20, gpu_k40),
                help = "specify gpu mode, p100:16gb, k40:12gb, k20:5bg [default: %default]")
    opts, args = p.parse_args(args)
    if len(args) != 0:
        sys.exit(not p.print_help())

    cmd = 'srun --partition=gpu --gres=gpu --constraint={model} --mem-per-cpu={memory} --ntasks-per-node=1 --nodes=1 --time={hour}:0:0 --pty $SHELL\n'.format(opts.model, opts.memory, opts.time)
    print(cmd)

if __name__ == "__main__":
    main()
