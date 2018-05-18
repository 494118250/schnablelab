# -*- coding: UTF-8 -*-
"""
Collect all the headers for slurm, gapit, FarmCPU.
"""

Slurm_header = '''#!/bin/sh
#SBATCH --time=%s:00:00          # Run time in hh:mm:ss
#SBATCH --mem-per-cpu=%s       # Maximum memory required per CPU (in megabytes)
#SBATCH --job-name=%s
#SBATCH --error=./%s.err
#SBATCH --output=./%s.out

'''

Slurm_gpu_header = '''#!/bin/sh
#SBATCH --time=130:00:00          # Run time in hh:mm:ss
#SBATCH --mem-per-cpu=10000       # Maximum memory required per CPU (in megabytes)
#SBATCH --job-name=%s
#SBATCH --error=./%s.err
#SBATCH --output=./%s.out
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --constraint=gpu_%s

'''

Gapit_header = '''library(multtest)
library(gplots)
library(genetics)
library(ape)
library(EMMREML)
library(compiler) #this library is already installed in R
library("scatterplot3d")
source("http://zzlab.net/GAPIT/gapit_functions.txt")
source("http://zzlab.net/GAPIT/emma.txt")
setwd(".")
myY <- read.table("%s", head = TRUE) # sep is the space related separator
myGM <- read.table("%s.GM", head = TRUE)
myGD <- read.table("%s.GD", head = TRUE)
myCV <- read.table("%s", head = TRUE)
myKI <- read.table("%s", head = FALSE)
#Step 2: Run GAPIT
myGAPIT <- GAPIT(Y=myY, GD=myGD, GM=myGM, CV=myCV, KI=myKI, memo='%s')
'''

FarmCPU_header = '''
library("bigmemory")
library("biganalytics")
library("compiler")
source("http://zzlab.net/GAPIT/gapit_functions.txt")
source("http://zzlab.net/FarmCPU/FarmCPU_functions.txt")
setwd(".")
myY <- read.table("%s", head = TRUE)
myGM <- read.table("%s.GM", head = TRUE)
myGD <- read.big.matrix("%s.GD", type="char", sep="\t", head = TRUE)
myCV <- read.table("%s", head = TRUE)
#Step 2: Run FarmCPU
myFarmCPU <- FarmCPU(Y=myY, GD=myGD, GM=myGM, CV=myCV, method.bin="optimum", bin.size=c(5e5,5e6,5e7), bin.selection=seq(10,100,10), threshold.output=1, memo='%s')
'''

FarmCPUpp_header = '''
library("bigmemory")
library("biganalytics")
library("compiler")
source("http://zzlab.net/GAPIT/gapit_functions.txt")
source("http://zzlab.net/FarmCPU/FarmCPU_functions.txt")
setwd(".")
myY <- read.table(system.file("extdata", "%s", package = "FarmCPUpp"), header = TRUE, stringsAsFactors = FALSE)
myGM <- read.table(system.file("extdata", "%s.GM", package = "FarmCPUpp"),header = TRUE, stringsAsFactors = FALSE)
myGD <- read.big.matrix(system.file("extdata", "%s.GD", package = "FarmCPUpp"),type = "double", sep = "\t", header = TRUE, col.names = myGM$SNP, ignore.row.names = FALSE, has.row.names = TRUE)
myCV <- read.table("%s", head = TRUE)
#Step 2: Run FarmCPU
myFarmCPU <- FarmCPU(Y=myY, GD=myGD, GM=myGM, CV=myCV, method.bin="optimum", bin.size=c(5e5,5e6,5e7), bin.selection=seq(10,100,10), threshold.output=1, memo='%s')
'''

MSTMap_header = '''
population_type RIL%s
population_name original
distance_function kosambi
cut_off_p_value 0.000001
no_map_dist 15.0
no_map_size 0
missing_threshold 0.3
estimation_before_clustering yes
detect_bad_data yes
objective_function COUNT
number_of_loci %s
number_of_individual %s

'''
