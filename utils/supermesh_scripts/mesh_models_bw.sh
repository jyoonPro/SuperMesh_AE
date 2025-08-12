#!/bin/bash

outdir=$SIMHOME/micro_2025_new/models/mesh
mkdir -p $outdir

mlperfdir=$SIMHOME/src/SCALE-Sim/topologies/mlperf
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets
modeldir=$SIMHOME/src/SCALE-Sim/topologies/CIFAR10_main_models

collective=AR
topology=mesh
allreduce=pipeline

for nnpath in $modeldir/densenet201 $modeldir/Resnet152 $modeldir/vgg19 $modeldir/inceptionv4
do
  nn=$(basename $nnpath)
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $nnpath.csv \
      --run-name ${nn} \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size 0 \
      --bandwidth 100 \
      --load-tree \
      > $outdir/${nn}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

wait