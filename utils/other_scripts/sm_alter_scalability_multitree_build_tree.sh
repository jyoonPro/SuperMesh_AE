#!/bin/bash
##NECESSARY JOB SPECIFICATIONS
#SBATCH --job-name=sm_alter_scalability_multitree_build_tree      #Set the job name to "JobExample1"
#SBATCH --time=72:00:00              #Set the wall clock limit to 1hr and 30min
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=32GB                  #Request 2560MB (2.5GB) per node
#SBATCH --output=sm_alter_scalability_multitree_build_tree.%j

## YOUR COMMANDS BELOW

module load GCCcore/11.2.0 Python/3.9.6
source venv/bin/activate
source setup_env.sh

totalNodes=(9 16 25 36 49 64 81 100 121 144 169 196 225 256)

outdir=$SIMHOME/results/ISCA2025/build_tree/SM_Alter
mkdir -p $outdir

mlperfdir=$SIMHOME/src/SCALE-Sim/topologies/mlperf
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets
modeldir=$SIMHOME/src/SCALE-Sim/topologies/CIFAR10_main_models

collective=AR
topology=SM_Alter
allreduce=multitree

for i in ${!totalNodes[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs ${totalNodes[$i]} \
      --num-vaults 16 \
      --mini-batch-size $((16*totalNodes[$i])) \
      --network $cnndir/alexnet.csv \
      --run-name "scalability" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_${totalNodes[$i]}_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size $((96000*totalNodes[$i])) \
      --bandwidth 100 \
      --only-save-tree \
      > $outdir/scalability_${totalNodes[$i]}_${collective}_${topology}_${allreduce}_error.log 2>&1 & \
done

wait