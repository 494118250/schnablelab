# -*- coding: UTF-8 -*-
"""
Generate MVP slurm job file. Find more details about MVP at <https://github.com/XiaoleiLiuBio/MVP>.
If MVP hasn't be installed. Fllow steps below to install MVP:
$ wget https://raw.githubusercontent.com/XiaoleiLiuBio/MVP/master/packages.zip
$ unzip packages.zip
$ cd packages
$ R
> source("MVPinstall.r")
After installed successfully, MVP can be loaded by typing
> library(MVP)
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser
from JamesLab.apps.header import SlrumHeader
from JamesLab.apps.natsort import natsorted

class MVP():
    """
    class for generating mvp commands
    """
imMVP <- MVP(
    phe=phenotype,
    geno=genotype,
    map=map,
    #K=Kinship,
    #CV.GLM=Covariates,
    #CV.MLM=Covariates,
    #CV.FarmCPU=Covariates,
    nPC.GLM=5,
    nPC.MLM=3,
    nPC.FarmCPU=3,
    perc=1,
    priority="speed",
    ncpus=10,
    vc.method="EMMA",
    maxLoop=10,
    method.bin="FaST-LMM",#"FaST-LMM","EMMA", "static"
    #permutation.threshold=TRUE,
    #permutation.rep=100,
    threshold=0.05,
    method=c("GLM", "MLM", "FarmCPU")
)
