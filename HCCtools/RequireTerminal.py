"""
require personal terminal used for computation
"""

gpu = 'srun --partition=gpu --gres=gpu --mem-per-cpu=1024 --ntasks-per-node=6 --nodes=1 --pty $SHELL'
