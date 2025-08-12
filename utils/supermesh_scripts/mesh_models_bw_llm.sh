#!/bin/bash

outdir=$SIMHOME/micro_2025_new/llm_models/mesh/vaults16
mkdir -p $outdir
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets

collective=AR
topology=mesh
allreduce=pipeline

syntheticDataSize=(262144 234881024 50331648 134217728 268435456 201326592 83886080)
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

outdir=$SIMHOME/micro_2025_new/llm_models/mesh/vaults1
mkdir -p $outdir

syntheticDataSize=(262144 234881024 50331648 134217728 268435456 201326592 83886080)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 16 \
      --num-vaults 1 \
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