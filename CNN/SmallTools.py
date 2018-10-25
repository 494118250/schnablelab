"""
generate labels of training images
"""

import pandas as pd
from pathlib import Path
import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header, Slurm_gpu_header
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
import numpy as np
from scipy.stats import linregress

def main():
    actions = (
        ('genlabel', 'genearte label for training image files'),
        ('extract_info', 'extract testing and prediction results from dpp log file'),
        ('statistics', 'calculate CountDiff, AbsCountDiff, MSE, Agreement, r2, p_value, and draw scatter, bar plots'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def genlabel(args):
    """
    %prog train_dir

    generate my_labels.csv in the training dir
    """
    p = OptionParser(genlabel.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    train_dir, = args
    #print(train_dir)
    img_path = Path(train_dir)
    imgs = img_path.glob('*png')
    fns = [i.name for i in imgs]
    lcs = [i.split('_')[0] for i in fns]
    mydf = pd.DataFrame(dict(zip(['fn', 'lc'], [fns, lcs])))
    print('%s images in the trainig dir.'%(mydf.shape[0]))
    mydf.to_csv(img_path/'my_labels.csv', index=False, header=False)
    print('Done, check my_labels.csv')

def convert2list(lines):
    vs = []
    for i in lines:
        j = i.split()
        for it in j:
            try:
                v = float(it)
                vs.append(v)
            except:
                pass
    return vs

def extract_info(args):
    """
    %prog log_file output_prefix
    
    extract testing and prediction results from dpp log file
    """
    p = OptionParser(extract_info.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    logfile, opp, = args

    left, right = [], []
    pl, pr = 0, 0
    with open(logfile) as f:
        for i,j in enumerate(f):
            m = j.split()
            if len(m)>1 and m[1]=='[':
                left.append(i)
                pl=i
            if j[-2]==']' and i>pl and pl!=0:
                pr = i
                right.append(i+1)
    print(left)
    print(right)
    f1 = open(logfile)
    all_rows = f1.readlines()
    ground_truth_rows = all_rows[left[0]: right[0]]
    prediction_rows = all_rows[left[1]: right[1]]
    ground_truth = convert2list(ground_truth_rows)
    prediction = convert2list(prediction_rows)
    
    df = pd.DataFrame(dict(zip(['ground_truth', 'prediction'], [ground_truth, prediction])))
    df.to_csv('%s.csv'%opp, index=False, sep='\t')
    print('Done! check %s.csv.'%opp)

def statistics(args):
    """
    %prog 2cols_csv output_prefix 

    calculate CountDiff, AbsCountDiff, MSE, Agreement, r2, p_value, and scatter, bar plots
    """
    p = OptionParser(statistics.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mycsv,opp, = args
    
    df_compare = pd.read_csv(mycsv, delim_whitespace=True)
    df_compare['diff'] = df_compare['ground_truth'] - df_compare['prediction']
    df_compare['abs_diff'] = np.abs(df_compare['diff'])
    ax1 = df_compare['diff'].value_counts().sort_index().plot.bar(color='blue', grid=True)
    ax1.set_xlabel('Relative Count Differece')
    ax1.set_ylabel('Frequency')
    #ax1.set_title(title, fontsize=20)
    plt.savefig('%s_diff_bar.png'%opp)
    print('diff bar plot done!')

    aggrmt = (df_compare['abs_diff']<=0.1).sum()/df_compare.shape[0]
    slope, intercept, r_value, p_value, std_err = linregress(df_compare['ground_truth'], df_compare['prediction'])
    mse = mean_squared_error(df_compare['ground_truth'], df_compare['prediction'])
    x = np.array([6.5,14.5])
    y = slope*x+intercept
    mean, std = df_compare['diff'].mean(), df_compare['diff'].std()
    abs_mean, abs_std = df_compare['abs_diff'].mean(), df_compare['abs_diff'].std()
    txt = 'CountDiff: %.2f(%.2f)\n'%(mean, std)
    txt += 'AbsCountDiff: %.2f(%.2f)\n'%(abs_mean, abs_std)
    txt += 'r2: %.2f\n'%r_value**2
    txt += 'p value: %s\n'%p_value
    txt += 'MSE: %.2f\n'%mse
    txt += 'Agreement(defined as absdiff<=0.1): %.2f'%aggrmt
    with open('%s.statics'%opp, 'w') as f1:
        f1.write(txt)
    print('statistics done!')

    ax2 = df_compare.plot.scatter(x='ground_truth', y='prediction', alpha=0.7, edgecolors='k', figsize=(7,7))        
    ax2.set_xlim(6.1,14.9)
    ax2.set_ylim(6.1,14.9)
    ax2.plot(x,y, color='red', linewidth=2)
    ax2.text(x=7,y=12, s = '$r^2$: %.2f'%r_value**2, fontsize=12, color='red')
    plt.savefig('%s_scatter.png'%opp)
    print('scatter plot done!')

if __name__ == "__main__":
    main()
