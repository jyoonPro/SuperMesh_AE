#!/bin/bash

#SBATCH --job-name=latency_test      #Set the job name to "JobExample1"
#SBATCH --time=72:00:00              #Set the wall clock limit to 1hr and 30min
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=32GB                  #Request 2560MB (2.5GB) per node
#SBATCH --output=latency_test.%j

module load GCCcore/11.2.0 Python/3.9.6
source venv/bin/activate
source setup_env.sh

outdir=$SIMHOME/results/latency_test/bandwidth
mkdir -p $outdir

mlperfdir=$SIMHOME/src/SCALE-Sim/topologies/mlperf
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets
modeldir=$SIMHOME/src/SCALE-Sim/topologies/CIFAR10_main_models

collective=AG
topology=mesh
allreduce=tacos

syntheticDataSize=(16777216)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 16 \
      --num-vaults 16 \
      --mini-batch-size 256 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_16_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_16_error.log 2>&1 &
done

#topology=mesh
#allreduce=pipeline
#
#syntheticDataSize=(16777216)
#for i in ${!syntheticDataSize[@]}; do
#  python $SIMHOME/src/simulate.py \
#      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
#      --num-hmcs 16 \
#      --num-vaults 16 \
#      --mini-batch-size 256 \
#      --network $cnndir/alexnet.csv \
#      --run-name "bw_${syntheticDataSize[$i]}" \
#      --outdir $outdir \
#      --booksim-network $topology \
#      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_16_200.cfg \
#      --allreduce $allreduce \
#      --collective $collective \
#      --message-buffer-size 32 \
#      --message-size 4096 \
#      --synthetic-data-size ${syntheticDataSize[$i]} \
#      --bandwidth 100 \
#      --load-tree \
#      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_16_error.log 2>&1 &
#done

topology=mesh
allreduce=multitree

syntheticDataSize=(16777216)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 16 \
      --num-vaults 16 \
      --mini-batch-size 256 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_16_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_16_error.log 2>&1 &
done

topology=SM_Alter
allreduce=pipeline

syntheticDataSize=(16777216)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 16 \
      --num-vaults 16 \
      --mini-batch-size 256 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_16_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_16_error.log 2>&1 &
done

topology=SM_Bi
allreduce=pipeline

syntheticDataSize=(16777216)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 16 \
      --num-vaults 16 \
      --mini-batch-size 256 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_16_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_16_error.log 2>&1 &
done

topology=SM_Uni
allreduce=pipeline

syntheticDataSize=(16777216)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 16 \
      --num-vaults 16 \
      --mini-batch-size 256 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_16_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_16_error.log 2>&1 &
done

wait