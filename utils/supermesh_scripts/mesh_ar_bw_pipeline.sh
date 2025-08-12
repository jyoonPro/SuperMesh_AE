#!/bin/bash

outdir=$SIMHOME/micro_2025_new/bandwidth/mesh
mkdir -p $outdir

mlperfdir=$SIMHOME/src/SCALE-Sim/topologies/mlperf
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets
modeldir=$SIMHOME/src/SCALE-Sim/topologies/CIFAR10_main_models

collective=AR
topology=mesh
allreduce=pipeline

syntheticDataSize=(262144 524288 1048576 2097152 4194304 8388608 16777216 33554432 67108864 134217728)
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

syntheticDataSize=(262144 524288 1048576 2097152 4194304 8388608 16777216 33554432 67108864 134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 25 \
      --num-vaults 16 \
      --mini-batch-size 400 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_25_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_25_error.log 2>&1 &
done

syntheticDataSize=(262144 524288 1048576 2097152 4194304 8388608 16777216 33554432 67108864 134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 64 \
      --num-vaults 16 \
      --mini-batch-size 1024 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_64_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_64_error.log 2>&1 &
done

syntheticDataSize=(262144 524288 1048576 2097152 4194304 8388608 16777216 33554432 67108864 134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 81 \
      --num-vaults 16 \
      --mini-batch-size 1296 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_81_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_81_error.log 2>&1 &
done

wait