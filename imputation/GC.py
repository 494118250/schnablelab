#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Correct Genotype Calls with Sliding Window Method.
"""

import re
import sys
import logging
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from collections import defaultdict, Counter
from JamesLab import __version__ as version
from JamesLab.apps.Tools import getChunk, eprint, random_alternative
from JamesLab.apps.base import OptionParser, OptionGroup, ActionDispatcher, SUPPRESS_HELP
try: 
    from ConfigParser import ConfigParser
except ModuleNotFoundError:
    from configparser import ConfigParser

homo_pattern1 = re.compile('9*09*09*|9*29*29*')
hete_pattern = re.compile('1|9*09*29*|9*29*09*')
homo_pattern2 = re.compile('9*29*29*2*9*2*9*2*9*2*9*2*9*|9*09*09*0*9*0*9*0*9*0*9*0*9*')

class ParseConfig(object):
    """
    Parse the configure file using configparser
    """
    def __init__(self, configfile):
        config = ConfigParser()
        cfgFn = config.read(configfile)[0]
        self.po_type = config.get('Section1', 'Population_type')
        self.gt_a = config.get('Section2', 'Letter_for_homo1')
        self.gt_h = config.get('Section2', 'Letter_for_hete')
        self.gt_b = config.get('Section2', 'Letter_for_homo2')
        self.gt_miss = config.get('Section2', 'Letter_for_missing_data')
        self.error_a = config.getfloat('Section3', 'error_rate_for_homo1')
        self.error_b = config.getfloat('Section3', 'error_rate_for_homo2')
        self.error_h = abs(self.error_a - self.error_b)
        self.win_size = config.getint('Section4', 'Sliding_window_size')

def het2hom(seqnum):
    """
    temporarily convert heterozygous to homozygous as random as possible
    """
    seqnum_tmp = seqnum.copy()
    grouper = (seqnum_tmp.diff(1)!=0).astype('int').cumsum()
    for __, grp in seqnum_tmp.groupby(grouper):
        geno, lens = grp.unique()[0], grp.shape[0]
        if geno==1:
            if lens > 1:
                homos = random_alternative(lens)
                seqnum_tmp[grp.index] = homos
    if seqnum_tmp[0] == 1:
        seqnum_tmp[0] = np.random.choice([0,2])
    
    het_idx = seqnum_tmp[seqnum_tmp==1].index
    nearby_homo = seqnum_tmp[het_idx-1]
    rep_dict = {0:2, 2:0, 9:np.random.choice([0,2])}
    replace_genos = nearby_homo.apply(lambda x: rep_dict[x])
    seqnum_tmp[het_idx] = replace_genos
    return seqnum_tmp

def get_mid_geno(np_array, cargs_obj):
    """
    return the genotype with highest probability in the central part.
    """
    a_count, b_count, miss_count = count_genos(np_array)
    ab_count = a_count + b_count
    if ab_count > cargs_obj.win_size//2:
        a_ex_prob = stats.binom.pmf(b_count, ab_count, cargs_obj.error_a)
        h_ex_prob = stats.binom.pmf(b_count, ab_count, 0.5+cargs_obj.error_h/2)
        b_ex_prob = stats.binom.pmf(b_count, ab_count, 1-cargs_obj.error_b)
        d = {key: value for (key, value) in zip([0, 1, 2], [a_ex_prob, h_ex_prob, b_ex_prob])}
        return max(d, key=d.get)
    else:
        return np.nan

def count_genos(np_array):
    """
    count genotypes in a given seq. if a genotype is not in the seq, will return 0 rather than raising an error or NaN.
    """
    counts = Counter(np_array)
    a_count, b_count, miss_count = counts[0], counts[2], counts[9]
    return a_count, b_count, miss_count

def get_score(np_array, cargs_obj):
    """
    calculate the score for each sliding window in the seq_num_no1
    """
    a_count, b_count, __ = count_genos(np_array)
    if a_count+b_count > cargs_obj.win_size//2:
        return a_count/float(b_count) if b_count != 0 else a_count/(b_count+0.1)
    else:
        return np.nan

def judge_h_island(h_scores):
    """
    judge if the h island in the corrected seqs is real or fake.
    """
    length = h_scores.shape[0]
    if length >=3:
        trends = h_scores.diff().iloc[1:]
        ups, downs = (trends>0).sum(), (trends<0).sum() 
        if ups == 0 or downs == 0:
            return False # the score curve monotonically increases or decreases so it is the fake h island
        else:
            return True # real h island
    else: 
        return True # real h island

def callback(h_scores):
    """
    call back the h island to the origianl genotypes based on the socre
    """
    realgenos = []
    for val in h_scores:
        if val > 1: realgenos.append(0)
        elif val < 1: realgenos.append(2)
        else: realgenos.append(np.nan)
    return realgenos
    
def fix_sliding_case1(seqnum, initial_corrected_seq, h_island_idx):
    """
    original seq: hhhh,aaaa
    after initial correction: hhh,aaaaa
    """
    st = h_island_idx[-1]+1
    ed = st+6
    if ed <= seqnum.index[-1]:
        indent_genos = ''.join(map(str, seqnum.loc[st: ed].values))
        #print('case1 indent_geno: {}'.format(indent_genos))
        result = homo_pattern1.search(indent_genos)
        try:
            i = result.start()
            if i > 0:
                initial_corrected_seq.loc[st:st+i-1] = 1
                #print(pd.concat([seqnum, initial_corrected_seq], axis =1))
        except AttributeError:
            pass

def fix_sliding_case2(seqnum, initial_corrected_seq, h_island_idx):
    """
    original seq: hhhh,aaaa
    after initial correction: hhhhh,aaa
    """
    ed = h_island_idx[-1]
    st = ed - 6
    if st >= seqnum.index[0]:
        indent_genos = ''.join(map(str, seqnum.loc[st: ed].values))
        #print('case2 indent_geno: {}'.format(indent_genos))
        result = homo_pattern1.search(indent_genos)
        try:
            i = result.start()
            if i > 0:
                if hete_pattern.search(indent_genos, i) is None:
                    geno = 0 if '0' in result.group() else 2
                    initial_corrected_seq.loc[st+i:ed] = geno
                    #print(pd.concat([seqnum, initial_corrected_seq], axis =1))
        except AttributeError:
            pass
    
def fix_sliding_case3(seqnum, initial_corrected_seq, h_island_idx):
    """
    original seq: aaaa,hhhh
    after initial correction: aaa,hhhhh
    """
    st = h_island_idx[0]
    ed = st+6
    if ed <= h_island_idx[-1]:
        indent_genos = ''.join(map(str, seqnum.loc[st: ed].values))
        #print('case3 indent_geno: {}'.format(indent_genos))
        result = homo_pattern2.match(indent_genos)
        try:
            i = result.end()
            if i > 0:
                geno = 0 if '0' in result.group() else 2
                initial_corrected_seq.loc[st:st+i-1] = geno
                #print(pd.concat([seqnum, initial_corrected_seq], axis =1))
        except AttributeError:
            pass

def fix_sliding_case4(seqnum, initial_corrected_seq, h_island_idx):
    """
    original seq: aaaa,hhhh
    after initial correction: aaaaa,hhh
    """
    ed = h_island_idx[0]-1
    st = ed - 6
    if st >= seqnum.index[0]:
        indent_genos = ''.join(map(str, seqnum.loc[st: ed].values))
        #print('case4 indent_geno: {}'.format(indent_genos))
        result = homo_pattern2.search(indent_genos)
        try:
            i = result.end()
            if i < 7:
                initial_corrected_seq.loc[st+i:ed] = 1
                #print(pd.concat([seqnum, initial_corrected_seq], axis =1))
        except AttributeError:
            pass

def get_corrected_num(seqnum, corrected_seq):
    """
    count number of genotpes corrected
    """
    return (seqnum != corrected_seq).sum()

class CorrectOO(object):
    """
    This class contains the routine to correct the original seq per sample
    """
    def __init__(self, config_params, orig_seq_without_idx_num):
        self.cargs = config_params
        self.seq_num = orig_seq_without_idx_num
        self.seq_num_no1 = het2hom(self.seq_num)
        self.rolling_geno = self.seq_num_no1.rolling(self.cargs.win_size, center=True).apply(get_mid_geno, raw=True, args=(self.cargs,))
        self.rolling_score = self.seq_num_no1.rolling(self.cargs.win_size, center=True).apply(get_score, raw=True, args=(self.cargs,))

        # debug the h island
        grouper = (self.rolling_geno.diff(1)!=0).astype('int').cumsum()
        for __, grp in self.rolling_geno.groupby(grouper):
            geno = grp.unique()[0]
            if geno==1:
                h_score_island = self.rolling_score[grp.index]
                if judge_h_island(h_score_island): # adjust the slding problem of the real h island.
                    h_island_len = grp.shape[0]
                    fix_sliding_case1(self.seq_num, self.rolling_geno, grp.index)
                    fix_sliding_case2(self.seq_num, self.rolling_geno, grp.index)
                    fix_sliding_case3(self.seq_num, self.rolling_geno, grp.index)
                    fix_sliding_case4(self.seq_num, self.rolling_geno, grp.index)
            
                else: # call back the fake h island to the origianl genotypes
                    real_genos = callback(h_score_island)
                    self.rolling_geno[grp.index] = real_genos

        # substitute NaNs with original genotypes
        self.corrected = self.rolling_geno.where(~self.rolling_geno.isna(), other=self.seq_num).astype('int')

def correct(args):
    """
    %prog correct config.txt input.matrix 

    Correct wrong genotype calls and impute missing values in `input.matrix` using sliding
    window method with parameters defined in `config.txt`.
    """
    p = OptionParser(correct.__doc__)
    p.add_option("-c", "--configfile", help=SUPPRESS_HELP)
    p.add_option("-m", "--matrixfile", help=SUPPRESS_HELP)
    p.add_option('--itertimes', default=7, type='int', 
                help='maximum correction times to reach the stablized status')
    q = OptionGroup(p, "output options")
    p.add_option_group(q)
    q.add_option('--opp', default="'infer'",
                help='specify the prefix of the output file names')
    q.add_option("--logfile", default='GC.correct.log',
                help="specify the file saving running info")
    q.add_option('--debug', default=False, action="store_true",
                help='trun on the debug mode that will generate a tmp file containing both original and corrected genotypes for debug use')

    p.set_cpus(cpus=8)
    opts, args = p.parse_args(args)

    if len(args) != 2:
        sys.exit(not p.print_help())

    configfile, mapfile = args
    inputmatrix = opts.matrixfile or mapfile
    inputconfig = opts.configfile or configfile

    opf = inputmatrix.rsplit(".", 1)[0]+'.corrected.map' if opts.opp=="'infer'" else '{}.map'.format(opts.opp) # output file
    if Path(opf).exists():
        eprint("ERROR: Filename collision. The future output file `{}` exists".format(opf))
        sys.exit(1)

    cpus = opts.cpus
    if sys.version_info[:2] < (2, 7):
        logging.debug("Python version: {0}. CPUs set to 1.".\
                    format(sys.version.splitlines()[0].strip()))
        cpus = 1

    logging.basicConfig(filename=opts.logfile, 
        level=logging.DEBUG,
        format="%(asctime)s:%(levelname)s:%(message)s")

    cargs = ParseConfig(inputconfig)
    if cargs.win_size % 2 == 0:
        eprint("ERROR: The slding window value cannot be even")
        sys.exit(1)
    logging.debug("Parameters in config file: {0}".format(cargs.__dict__))

    chr_order, chr_nums = getChunk(inputmatrix)
    map_reader = pd.read_csv(inputmatrix, delim_whitespace=True, index_col=[0, 1],  iterator=True)
    tmp_chr_list = []
    for chrom in chr_order:
        logging.debug('{}...'.format(chrom))
        print('{}...'.format(chrom))
        chunk = chr_nums[chrom]
        df_chr_tmp = map_reader.get_chunk(chunk)
        marker_num, sample_num = df_chr_tmp.shape
        logging.debug('{} contains {} markers and {} samples.'.format(chrom, marker_num, sample_num))
        tmp_sm_list = []
        for sm in df_chr_tmp:
            logging.debug('Start correcting {}...'.format(sm))
            orig_seq = df_chr_tmp[sm]
            orig_idx = orig_seq.index
            seq_no_idx = orig_seq.reset_index(drop=True)
            seq_no_idx_num = seq_no_idx.replace([cargs.gt_a, cargs.gt_b, cargs.gt_h, cargs.gt_miss], [0, 2, 1, 9])
            if seq_no_idx_num.shape[0] <= cargs.win_size:
                logging.debug('number of markers smaller than the window size, omit...')
                final_seq_no_idx = seq_no_idx
            else:
                logging.debug('correction round 1...')
                correct_obj = CorrectOO(cargs, seq_no_idx_num)
                corrected_n = get_corrected_num(seq_no_idx_num, correct_obj.corrected)
                round_n = 2
                while round_n <= opts.itertimes:
                    logging.debug('correction round %s...'%round_n)
                    corrected_obj = CorrectOO(cargs, correct_obj.corrected)
                    corrected_n_new = get_corrected_num(seq_no_idx_num, corrected_obj.corrected)
                    round_n += 1
                    if (corrected_n_new - corrected_n)/float(corrected_n) <= 0.01:
                        break
                    else:
                        corrected_n = corrected_n_new
                final_seq_no_idx = corrected_obj.corrected.replace([0, 2, 1, 9], [cargs.gt_a, cargs.gt_b, cargs.gt_h, cargs.gt_miss])
            final_seq_no_idx.index = orig_idx
            final_seq = final_seq_no_idx
            tmp_sm_list.append(final_seq)
        df_sm_tmp = pd.concat(tmp_sm_list, axis=1)
        tmp_chr_list.append(df_sm_tmp)
    df_corrected = pd.concat(tmp_chr_list)
    
    df_corrected.to_csv(opf, sep='\t', index=True)

    if opts.debug:
        logging.debug('generating the tmp file for debug use...')
        df_uncorrected = pd.read_csv(inputmatrix, delim_whitespace=True, index_col=[0, 1])
        df_debug = df_corrected.where(df_corrected==df_uncorrected, other=df_corrected+'('+df_uncorrected+')')
        df_debug.to_csv(opf+'.debug', sep='\t', index=True)
    print('Done!')

def filtermissing(args):
    """
    %prog filtermissing input.matrix output.matrix

    run quality control of the missing genotypes in the input.matrix before starting the correction.
    """
    p = OptionParser(filtermissing.__doc__)
    p.add_option("-i", "--input", help=SUPPRESS_HELP)
    p.add_option("-o", "--output", help=SUPPRESS_HELP)
    p.add_option('--cutoff_snp', default=0.5, type='float',
                help = "SNP with missing rate higher than this value will be removed")
    p.add_option('--rm_bad_samples', default=False, action="store_true",
                help='remove bad samples after controlling the SNPs with high missing rate')
    p.add_option('--cutoff_sample', type='float',
                help = "sample missing rate higher than this value will be removed after controlling the SNP missing rate")
    q = OptionGroup(p, "format options")
    p.add_option_group(q)
    q.add_option('--homo1', default="A",
                help='character for homozygous genotype')
    q.add_option("--homo2", default='B',
                help="character for alternative homozygous genotype")
    q.add_option('--hete', default='X',
                help='character for heterozygous genotype')
    q.add_option('--missing', default='-',
                help='character for missing value')
    opts, args = p.parse_args(args)

    if len(args) != 2:
        sys.exit(not p.print_help())

    if opts.rm_bad_samples and not opts.cutoff_sample:
        eprint('missing value cutoff for --cutoff_sample option must be specified when --rm_bad_samples added.')
        sys.exit(1)

    inmap, outmap = args
    inputmatrix = opts.input or inmap
    outputmatrix = opts.output or outmap

    chr_order, chr_nums = getChunk(inputmatrix)
    map_reader = pd.read_csv(inputmatrix, delim_whitespace=True, index_col=[0, 1],  iterator=True)
    Good_SNPs = []
    for chrom in chr_order:
        print('{}...'.format(chrom))
        chunk = chr_nums[chrom]
        df_chr_tmp = map_reader.get_chunk(chunk)
        df_chr_tmp_num = df_chr_tmp.replace([opts.homo1, opts.homo2, opts.hete, opts.missing], [0, 2, 1, 9])
        snp_num, sample_num = df_chr_tmp_num.shape
        good_rates = df_chr_tmp_num.apply(lambda x: (x==9).sum()/sample_num, axis=1) <= opts.cutoff_snp
        good_snp = df_chr_tmp.loc[good_rates, :]
        Good_SNPs.append(good_snp)
    df1 = pd.concat(Good_SNPs)
    before_snp_num = sum(chr_nums.values())
    after_snp_num, before_sm_num = df1.shape
    pct = after_snp_num/float(before_snp_num)*100
    print('{} SNP markers before quality control.'.format(before_num))
    print('{}({:.1f}%) markers left after the quality control.'.format(after_num, pct))

    if opts.rm_bad_samples:
        print('start quality control on samples')
        good_samples = df1.apply(lambda x: (x==opts.missing).sum()/after_num, axis=0) <= opts.cutoff_sample
        df2 = df1.loc[:,good_samples]
        after_sm_num = df2.shape[1]
        pct_sm = after_sm_num/float(before_sm_num)*100
        print('{} samples before quality control.'.format(before_sm_num))
        print('{}({:.1f}%) markers left after the quality control.'.format(after_sm_num, pct_sm))
        df2.to_csv(outputmatrix, sep='\t', index=True)
    else:
        df1.to_csv(outputmatrix, sep='\t', index=True)

def main():
    actions = (
        ('filtermissing', 'quality control of the missing gneotypes before correction'),
        ('cstest', 'merge csv maps and convert to bed format'),
        ('mergemarkers', 'merge maps in bed format'),
        ('correct', 'correct wrong genotype calls'),
        ('cleanup', 'clean redundant info in the tmp matirx file'),
        ('format', 'convert genotype matix file to other formats for the genetic map construction'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

if __name__ == '__main__':
    main()