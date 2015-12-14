#!/usr/bin/env python
# This script converts all z-score matrices from a dumped 3D
# array into CDTs, which are visualized using Java Treeview.

import pandas as pd
import numpy as np
import scipy
import sys, os, gzip
import tarfile
import matplotlib
matplotlib.use('Agg') # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt
import itertools as it
import cPickle
import shutil

barseq_path = os.getenv('BARSEQ_PATH')
sys.path.append(os.path.join(barseq_path, 'scripts'))
sys.path.append(os.path.join(barseq_path, 'lib'))

import config_file_parser as cfp
import compressed_file_opener as cfo
import cg_file_tools as cg_file
import cluster_dataset_wrappers as clus_wrap
from cg_common_functions import *

import argparse

def read_sample_table(tab_filename):

    assert os.path.isfile(tab_filename), 'File {} does not exist'.format(tab_filename)
    # Read everything in as a string, to prevent vexing
    # number interpretation problems! Methods further down
    # can coerce to different types.
    tab = pd.read_table(tab_filename, dtype = 'S')
    return tab

# Parse the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('dataset', help = 'The stacked matrix object, saved to file.')
parser.add_argument('clustergram_name', help = 'A name to attach to the clustergrams. Must be filename-compatible.')
parser.add_argument('strain_table', help = 'The strain barcode table used to interpret the strain barcodes (is in the "data" folder by default).')
parser.add_argument('sample_table', help = 'The sample table corresponding to the dataset.')
parser.add_argument('strain_columns', help = 'The columns from the barcode table to be included in the visualization.')
parser.add_argument('condition_columns', help = 'The columns from the sample table to be included in the visualization.')
parser.add_argument('-v', '--verbosity', help = 'The level of verbosity printed to stdout. Ranges from 0 to 3, 1 is default.')
args = parser.parse_args()

# Load in dataset
dataset_filename = os.path.abspath(args.dataset)
dataset_f = gzip.open(args.dataset)
dataset = cPickle.load(dataset_f)
dataset_f.close()

# Define an output folder and create it, using the dataset filename
output_folder = os.path.join(os.path.dirname(dataset_filename), 'CDTs')
if not os.path.isdir(output_folder):
    os.makedirs(output_folder)

# Read in the sample table
sample_table = read_sample_table(args.sample_table)

# Read in the barcode table
strain_table = read_sample_table(args.strain_table)

# Extract one matrix from the stack of matrices at a time, cluster, and
# export to files! Retain the filenames so they can be tarred/gzipped
# to be ready for distribution.
filenames_noext = []
num_components = dataset[0]
for i in num_components:
    matrix_id = '{}_{}-components-removed'.format(args.clustergram_name, i)
    print 'clustering {} matrix'.format(matrix_id)
    single_matrix_dataset = np.array([dataset[1], dataset[2], dataset[3][i]])
    filename_noext = clus_wrap.cluster_one_stacked_matrix(single_matrix_dataset, matrix_id, strain_table, sample_table, args.strain_columns, args.condition_columns, output_folder)
    filenames_noext.append(filename_noext)

###### Ultimate goal: combine all CDTs into one big tarred/gzipped folder, for distribution!
# First, get all of the filenames (cdt, atr, gtr)
filenames = []
for f_noext in filenames_noext:
    for ext in ['cdt', 'atr', 'gtr']:
        filenames.append('{}.{}'.format(f_noext, ext))
if args.verbosity >= 2:
    print filenames
# Now, create a temporary folder to hold all of the clustergrams for tarring/gzipping
# This temp folder name is also the name of the tarred archive. Cool, right?!
tmp_dir = get_temp_clustergram_name(output_folder, args.clustergram_name)
if args.verbosity >= 2:
    print tmp_dir
# Since it's timestamped, directory should never exist with this exact name
os.makedirs(tmp_dir)
# And copy all of the files to that temp directory!
for f in filenames:
    shutil.copy(f, tmp_dir)
# Now tar the directory!
tar_fname = '{}.tar.gz'.format(tmp_dir)
tar = tarfile.open(tar_fname, 'w:gz')
tar.add(tmp_dir, arcname = os.path.basename(tmp_dir))
tar.close()
# And, remove the temporary directory!
shutil.rmtree(tmp_dir, ignore_errors = True)





