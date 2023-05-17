#!/bin/bash
#SBATCH --qos regular
#SBATCH --constraint=haswell
#SBATCH -N 1
#SBATCH -t 00:30:00
#SBATCH --ntasks-per-node=12
#SBATCH --license=SCRATCH
#SBATCH --output=/global/cscratch1/sd/hongbo/lens_rot_bias/SimJobs/slurmjob.log.0

cd /global/cscratch1/sd/hongbo/lens_rot_bias/src/

OMP_NUM_THREADS=4 python CMBLensed_sim.py --sim_num=100 & sleep 1
OMP_NUM_THREADS=4 python CMBLensed_sim.py --sim_num=101 & sleep 1
OMP_NUM_THREADS=4 python CMBLensed_sim.py --sim_num=102 & sleep 1
wait
