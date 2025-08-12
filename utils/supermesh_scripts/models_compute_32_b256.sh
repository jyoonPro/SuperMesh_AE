#!/bin/bash

outdir=$SIMHOME/micro_2025_new/compute_short_32_b256
mkdir -p $outdir

mlperfdir=$SIMHOME/src/SCALE-Sim/topologies/mlperf
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets
modeldir=$SIMHOME/src/SCALE-Sim/topologies/CIFAR10_main_models

collective=Compute
topology=mesh
allreduce=multitree

for nnpath in $modeldir/densenet201 $modeldir/Resnet152 $modeldir/vgg19 $modeldir/inceptionv4
do
  nn=$(basename $nnpath)
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express.cfg \
      --num-hmcs 16 \
      --num-vaults 16 \
      --mini-batch-size 256 \
      --network $nnpath.csv \
      --run-name ${nn} \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_16_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size 0 \
      --bandwidth 100 \
      --load-tree \
      > $outdir/${nn}_${collective}_${topology}_${allreduce}_16_error.log 2>&1 &
done

wait