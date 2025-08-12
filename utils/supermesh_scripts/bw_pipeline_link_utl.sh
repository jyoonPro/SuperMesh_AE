#!/bin/bash

mlperfdir=$SIMHOME/src/SCALE-Sim/topologies/mlperf
cnndir=$SIMHOME/src/SCALE-Sim/topologies/conv_nets
modeldir=$SIMHOME/src/SCALE-Sim/topologies/CIFAR10_main_models

outdir=$SIMHOME/micro_2025_new/link_utl/mesh
mkdir -p $outdir

allreduce=pipeline
collective=AR
topology=mesh

syntheticDataSize=(134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      --save-link-utilization \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

outdir=$SIMHOME/micro_2025_new/link_utl/SM_Bi
mkdir -p $outdir

collective=AR
topology=SM_Bi

syntheticDataSize=(134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      --save-link-utilization \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

collective=RS
topology=SM_Bi

syntheticDataSize=(134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      --save-link-utilization \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

collective=AG
topology=SM_Bi

syntheticDataSize=(134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      --save-link-utilization \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

outdir=$SIMHOME/micro_2025_new/link_utl/SM_Alter
mkdir -p $outdir

collective=AR
topology=SM_Alter

syntheticDataSize=(134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      --save-link-utilization \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

collective=RS
topology=SM_Alter

syntheticDataSize=(134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      --save-link-utilization \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

collective=AG
topology=SM_Alter

syntheticDataSize=(134217728)
for i in ${!syntheticDataSize[@]}; do
  python $SIMHOME/src/simulate.py \
      --arch-config $SIMHOME/src/SCALE-Sim/configs/express_128.cfg \
      --num-hmcs 36 \
      --num-vaults 16 \
      --mini-batch-size 576 \
      --network $cnndir/alexnet.csv \
      --run-name "bw_${syntheticDataSize[$i]}" \
      --outdir $outdir \
      --booksim-network $topology \
      --booksim-config $SIMHOME/src/booksim2/runfiles/mesh/anynet_${topology}_36_200.cfg \
      --allreduce $allreduce \
      --collective $collective \
      --message-buffer-size 32 \
      --message-size 4096 \
      --synthetic-data-size ${syntheticDataSize[$i]} \
      --bandwidth 100 \
      --load-tree \
      --save-link-utilization \
      > $outdir/bw_${syntheticDataSize[$i]}_${collective}_${topology}_${allreduce}_36_error.log 2>&1 &
done

wait