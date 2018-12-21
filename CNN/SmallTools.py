"""
generate labels of training images
"""

import pandas as pd
from pathlib import Path
import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import Slurm_header, Slurm_gpu_header
from JamesLab.apps.Tools import GenDataFrameFromPath
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
    %prog train_dir label_fn

    generate my_labels.csv in the training dir
    """
    p = OptionParser(genlabel.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    train_dir, label_fn, = args

    train_path = Path(train_dir)
    train_df = GenDataFrameFromPath(train_path)
    total_n = train_df.shape[0]
    print('total %s images.'%total_n)

    all_real_dir = Path('/work/schnablelab/cmiao/LeafCounts_JinliangData/Raw_RealImages')
    all_real_df = pd.read_csv(all_real_dir/'labels_4633.csv').set_index('sm')

    train_df['real'] = train_df['fn'].isin(all_real_df.index)

    real_n = train_df['real'].sum()
    fake_n = total_n-real_n
    print('%s real images.'%real_n)
    print('%s fake images.'%fake_n)

    if real_n != 0:
        # asign real labels
        real_idx = train_df['fn'][train_df['real']]
        real_labels = all_real_df.loc[real_idx, 'LeafCounts'].values
        train_df.loc[train_df['real'], 'real']=real_labels

    if fake_n != 0:
        fake_df = train_df[train_df['real'].isin([False])]
        fake_labels = fake_df['fn'].apply(lambda x: int(x.split('_')[0])).values
        train_df.loc[train_df['real'].isin([False]), 'real']=fake_labels

    train_df[['fn', 'real']].to_csv(train_path/label_fn, index=False, header=False)
    print('Done, check %s'%label_fn)

def convert2list(lines):
    vs = []
    for i in lines:
        j = i.strip().lstrip('[').rstrip(']').split()
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
    f1.close()
    ground_truth_rows = all_rows[left[0]: right[0]]
    prediction_rows = all_rows[left[1]: right[1]]
    ground_truth = convert2list(ground_truth_rows)
    prediction = convert2list(prediction_rows)
    #print(ground_truth)
    #print(len(ground_truth))
    #print(prediction)
    #print(len(prediction))
    
    df = pd.DataFrame(dict(zip(['ground_truth', 'prediction'], [ground_truth, prediction])))
    df.to_csv('%s.csv'%opp, index=False, sep='\t')
    print('Done! check %s.csv.'%opp)

def statistics(args):
    """
    %prog 2cols_csv cls_range(eg: 5-10) output_prefix 

    calculate CountDiff, AbsCountDiff, MSE, Agreement, r2, p_value, and scatter, bar plots
    """
    p = OptionParser(statistics.__doc__)
    p.add_option('--header', default=None,
        help = 'spefiy if csv file has header')
    p.add_option('--cutoff_agreement', default=0.5,
        help = 'spefiy the cutoff counted for agreement calculation')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mycsv,cls_range, opp, = args
    
    df_compare = pd.read_csv(mycsv, delim_whitespace=True) \
        if not opts.header \
        else pd.read_csv(mycsv, delim_whitespace=True, header=None)
    print('shape of %s: %s'%(mycsv, df_compare.shape))

    df_compare['diff'] = df_compare['ground_truth'] - df_compare['prediction']
    df_compare['abs_diff'] = np.abs(df_compare['diff'])

    mi, ma = df_compare['diff'].min(), df_compare['diff'].max()
    mi_int = np.ceil(mi) if mi>0 else np.floor(mi)
    ma_int = np.ceil(ma) if ma>0 else np.floor(ma)
    bins = np.arange(mi_int, ma_int+1)
    cats = pd.cut(df_compare['diff'], bins)
    ax1 = pd.value_counts(cats).sort_index().plot.bar(color='blue')
    plt.xticks(rotation=40)
    ax1.set_xlabel('Relative Count Differece')
    ax1.set_ylabel('Frequency')
    plt.tight_layout()
    plt.savefig('%s_diff_bar.png'%opp)
    print('diff bar/histogram plot done!')

    aggrmt = (df_compare['abs_diff']<=float(opts.cutoff_agreement)).sum()/df_compare.shape[0]
    print('agreement is defined as diff <= %s.'%opts.cutoff_agreement)
    slope, intercept, r_value, p_value, std_err = linregress(df_compare['ground_truth'], df_compare['prediction'])
    mse = mean_squared_error(df_compare['ground_truth'], df_compare['prediction'])

    bt = int(cls_range.split('-')[0])
    tp = int(cls_range.split('-')[1])
    x = np.array([bt-0.5,tp+0.5])
    y = slope*x+intercept

    mean, std = df_compare['diff'].mean(), df_compare['diff'].std()
    abs_mean, abs_std = df_compare['abs_diff'].mean(), df_compare['abs_diff'].std()
    txt = 'CountDiff: %.2f(%.2f)\n'%(mean, std)
    txt += 'AbsCountDiff: %.2f(%.2f)\n'%(abs_mean, abs_std)
    txt += 'r2: %.2f\n'%r_value**2
    txt += 'p value: %s\n'%p_value
    txt += 'MSE: %.2f\n'%mse
    txt += 'Agreement: %.2f'%aggrmt
    with open('%s.statics'%opp, 'w') as f1:
        f1.write(txt)
    print('statistics done!')

    ax2 = df_compare.plot.scatter(x='ground_truth', y='prediction', alpha=0.5, figsize=(7,7), edgecolor='k')        
    ax2.set_xlim(bt-0.9, tp+0.9)
    ax2.set_ylim(bt-0.9, tp+0.9)
    ax2.plot(x,y, color='red', linewidth=2)
    ax2.text(x=bt, y=tp-2, s = txt, fontsize=12, color='red')
    plt.savefig('%s_scatter.png'%opp)
    print('scatter plot done!')

if __name__ == "__main__":
    main()
