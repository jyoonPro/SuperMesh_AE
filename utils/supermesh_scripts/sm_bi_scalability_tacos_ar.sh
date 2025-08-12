#!/bin/bash

totalNodes=(9 16 25 36 49 64 81 100 121 144 169 196 225 256)
outdir=$SIMHOME/micro_2025_new/scalability/SM_Bi
mkdir -p $outdir

mlperfdir=$SIMHOME/src/SCALE-Sim/topologies/mlperf
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets
modeldir=$SIMHOME/src/SCALE-Sim/topologies/CIFAR10_main_models

collective=AR
topology=SM_Bi
allreduce=tacos

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
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_${totalNodes[$i]}_200_v2.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size $((96000*totalNodes[$i])) \
      --bandwidth 100 \
      --load-tree \
      > $outdir/scalability_${totalNodes[$i]}_${collective}_${topology}_${allreduce}_error.log 2>&1 & \
done

wait