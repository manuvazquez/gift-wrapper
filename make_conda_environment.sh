#!/bin/bash

MANAGER="mamba"
NAME=gift

COLOR="\033[40m\033[32m"
UNCOLOR="\033[0m"


# only required if "anaconda" is not in the path
source $HOME/anaconda3/etc/profile.d/conda.sh

$MANAGER create --yes -n $NAME python=3 ipdb pyyaml paramiko tqdm colorama twine -c defaults -c conda-forge

echo -e new environment is \"$COLOR$NAME$UNCOLOR\"

conda activate $NAME

# # the environment is exported into a yaml file
# conda env export --no-builds --from-history -f environment.yml
