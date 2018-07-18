#!/bin/bash -l

#SBATCH --job-name=held_suarez_test_case
#SBATCH --partition=parallel
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#number of tasks ~ processes per node
#SBATCH --ntasks-per-node=16
#number of cpus (cores) per task (process)
#SBATCH --cpus-per-task=1
#SBATCH --mail-user=%u
#SBATCH --mail-type=all
#SBATCH --output=slurm_%j_%x.out

echo Running on host `hostname`
echo Time is `date`
echo Directory is `pwd`


module purge
source $HOME/.bashrc
source $HOME/Isca/src/extra/env/jhu
source activate isca_env



$HOME/anaconda3/envs/isca_env/bin/python held_suarez/held_suarez_test_case.py
