#!/bin/bash

# submitter.sh
#
# Usage:    submitter.sh
#
# instructions: edit this file to list the experiments, variables, etc. to process. It will run the cdo_time_mean.sh script.
#
# An example directory and file cominbation are:
# /badc/cmip6/data/CMIP6/GeoMIP/MOHC/UKESM1-0-LL/G6sulfur/r1i1p1f2/Amon/pr/gn/latest/
# pr_Amon_UKESM1-0-LL_G6sulfur_r1i1p1f2_gn_205001-210012.nc

############################################################
# First specify things for batch system
############################################################

# Define and create a directory to store messages from batch system, including error messages from code.
OUTPUTS_DIR=$PWD/lotus-outputs
mkdir -p $OUTPUTS_DIR

# Define the queue to submit the jobs to.
queue=short-serial
time=5

#############################################################
# Edit the following section to specify the files to process
#############################################################

# select which script you will use.
cdo_script=$PWD/cdo_time_mean.sh # $PWD outputs the current directory so make sure the script you want is in the directory that you run this script in.

# Specify the output directory for your processed netcdf files
out_dir=/home/users/$USER/data/ #
mkdir -p $out_dir # will create this directory if it doesn't already exist.

# input the date range for the processing period for the experiments. This will depend on the experiments.
date_range=2070-01-01,2100-01-01 # example is for 2070 to 2100
date_4_file=207001-210012

# run separately for different models as run numbers differ.
model=UKESM1-0-LL
centre=MOHC

# Variables and domains are looped through together. Ensure they match!
declare -a var_list=("tas" "pr")
declare -a domain_list=("Amon" "Amon")
var_len=${#var_list[@]} # number of elements in list

# Experiment and project are looped through together. Ensure they match!
declare -a exp_list=("G6sulfur")
declare -a project_list=("GeoMIP")
exp_len=${#exp_list[@]} # number of elements in list

# runs
declare -a run_list=("r1i1p1f2")
run_len=${#run_list[@]} # number of elements in list

###########################################################
# This section loops through everything and submits jobs
###########################################################

# Loop through each set of lists in turn.
for (( i=0; i<${var_len}; i++ )); do # variable loop
    for (( j=0; j<${exp_len}; j++ )); do # experiment loop
	for (( k=0; k<${run_len}; k++ )); do # run loop

	    # define the data directory to search for files using lists
	    data_dir=/badc/cmip6/data/CMIP6/${project_list[$j]}/${centre}/${model}/${exp_list[$j]}/${run_list[$k]}/${domain_list[$i]}/${var_list[$i]}/gn/latest
	    # define the base of the filename for the output file(s) using lists, note this matches the file format in the data directory except for the date_4_file section and the missing .nc.
	    out_base=${var_list[$i]}_${domain_list[$i]}_${model}_${exp_list[$j]}_${run_list[$k]}_gn_${date_4_file}

	    # give a name to the submission based on variables, etc.
	    call_name=${model}.${var_list[$i]}.${exp_list[$j]}.${run_list[$k]}

	    # define inputs for cdo_script
	    cdo_script_input="$data_dir $date_range $out_base $out_dir"

	    # Submit the job to LOTUS
	    echo "working on call name:"
	    echo $call_name
	    # sbatch command submits the job. backslash for line continuation.
	    sbatch -p $queue -t $time -o $OUTPUTS_DIR/${call_name}.%j.out \
		   -e $OUTPUTS_DIR/${call_name}.%j.err $cdo_script $cdo_script_input

	    # Wait 5 seconds before submitting next job, going too fast can get you blocked.
	    sleep 5

	done # close run loop
    done # close exp loop
done # close var loop
