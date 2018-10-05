# -*- coding: UTF-8 -*-

"""
preprocess dhs files
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob, iglob
from JamesLab.apps.natsort import natsorted
import subprocess
from JamesLab.apps.header import Slurm_header
import pandas as pd
import re
import numpy as np

def main():
    actions = (
        ('genTissueSpecies', 'generate leaf, stem and root csv files'),
    )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def rmsufix(df):
    pat = re.compile('\.v[1-3].')
    df['Gene'] = df['Gene'].apply(lambda x:re.split(pat, x)[0])

def genTissueDf(tissue):
    sorghum_idx,millet_idx,brachy_idx = [], [], []
    for j in ['cold', 'normal']:
        for n in (1,2,3):
            sorghum_idx.append('sorghum_%s_%s%s'%(j, tissue, n))
            millet_idx.append('millet_%s_%s%s'%(j, tissue, n))
            brachy_idx.append('brachy_%s_%s%s'%(j, tissue, n))
    return sorghum_idx,millet_idx,brachy_idx

def genTissueSpecies(args):
    """
    %prog genTissueSpecies sorghum_xls millet_xls brachy_xls intelligent_csv
    generate tissue csv files including three species to perform interaction study
    """
    p = OptionParser(genTissueSpecies.__doc__)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    sorghumC, milletC, brachyC, syntenicF = args
    print('read three excel count files')
    df_sorghum = pd.read_excel(sorghumC)
    df_millet = pd.read_excel(milletC)
    df_brachy = pd.read_excel(brachyC)
    print('remve suffix of gene name') 
    rmsufix(df_brachy)
    rmsufix(df_millet)
    rmsufix(df_sorghum)    
    print('reorder the columns') 
    rightCols = ['Gene',\
             'cold_leaf1', 'cold_leaf2', 'cold_leaf3',\
             'cold_root1', 'cold_root2', 'cold_root3',\
             'cold_stem1', 'cold_stem2', 'cold_stem3',\
             'leaf1', 'leaf2','leaf3',\
             'root1', 'root2', 'root3',\
             'stem1', 'stem2','stem3']
    df_brachy = df_brachy[rightCols]
    df_sorghum = df_sorghum[rightCols]
    df_millet = df_millet[rightCols]
    print('rename columns')
    brachy_cols = ['Gene']
    millet_cols = ['Gene']
    sorghum_cols = ['Gene']
    for i in rightCols[1:]:
        brachy_cols.append('brachy_'+i if 'cold' in i else 'brachy_normal_'+i)
        millet_cols.append('millet_'+i if 'cold' in i else 'millet_normal_'+i)
        sorghum_cols.append('sorghum_'+i if 'cold' in i else 'sorghum_normal_'+i)
    df_brachy.columns = brachy_cols
    df_millet.columns = millet_cols
    df_sorghum.columns = sorghum_cols
    print(df_brachy.shape)
    print(df_millet.shape)
    print(df_sorghum.shape)

    print('concise syntenic gene list')
    df_syc = pd.read_csv(syntenicF, usecols=['sorghum2', 'setaria22', 'brachy'])
    print(df_syc.shape)
    df_syc = df_syc.replace('No Gene', np.nan).dropna(axis=0, how='any').reset_index(drop=True)
    cd1 = df_syc['sorghum2'].isin(df_sorghum['Gene'])
    cd2 = df_syc['setaria22'].isin(df_millet['Gene'])
    cd3 = df_syc['brachy'].isin(df_brachy['Gene'])
    syn_cond = cd1 & cd2 & cd3
    df_syc_17150 = df_syc[syn_cond]
    print(df_syc_17150.shape)
    
    print('concise count files by only keeping concised syntenic genes')
    df_brachy = df_brachy.set_index('Gene')
    df_sorghum = df_sorghum.set_index('Gene')
    df_millet = df_millet.set_index('Gene')
    df_brachy = df_brachy.loc[df_syc_17150['brachy'],]
    df_sorghum = df_sorghum.loc[df_syc_17150['sorghum2'],]
    df_millet = df_millet.loc[df_syc_17150['setaria22'],]
    df_syc_17150.columns = ['sorghum', 'millet', 'brachy']
    df_syc_17150 = df_syc_17150.reset_index(drop=True)
    df_brachy = df_brachy.reset_index()
    df_sorghum = df_sorghum.reset_index()
    df_millet = df_millet.reset_index()
    print(df_brachy.shape)
    print(df_millet.shape)
    print(df_sorghum.shape)
    
    # leaf
    sorghum_idx,millet_idx,brachy_idx= genTissueDf('leaf')
    df_leaf = pd.concat([df_syc_17150, df_sorghum[sorghum_idx], df_millet[millet_idx], df_brachy[brachy_idx]], axis=1)
    df_leaf.to_csv('leaf.csv', index=False)
    # stem
    sorghum_idx,millet_idx,brachy_idx= genTissueDf('stem')
    df_stem = pd.concat([df_syc_17150, df_sorghum[sorghum_idx], df_millet[millet_idx], df_brachy[brachy_idx]], axis=1)
    df_stem.to_csv('stem.csv', index=False)
    # root
    sorghum_idx,millet_idx,brachy_idx= genTissueDf('root')
    df_root = pd.concat([df_syc_17150, df_sorghum[sorghum_idx], df_millet[millet_idx], df_brachy[brachy_idx]], axis=1)
    df_root.to_csv('root.csv', index=False)
    print('leaf.csv, stem.csv, root.csv generated')

    
if __name__ == "__main__":
    main()
