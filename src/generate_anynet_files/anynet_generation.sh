#!/bin/bash

totalNodes=(9 16 25 36 49 64 81 100 121 144 169 196 225 256)
for i in ${!totalNodes[@]}; do
  python anynet_file_generate.py \
    --nodes ${totalNodes[$i]} \
    --topology mesh
done

totalNodes=(9 16 25 36 49 64 81 100 121 144 169 196 225 256)
for i in ${!totalNodes[@]}; do
  python anynet_file_generate.py \
    --nodes ${totalNodes[$i]} \
    --topology SM_Bi \
    --radix 5
done

totalNodes=(16 36 64 100 144 196 256)
for i in ${!totalNodes[@]}; do
  python anynet_file_generate.py \
    --nodes ${totalNodes[$i]} \
    --topology SM_Alter \
    --radix 4
done

totalNodes=(9 25 49 81 121 169 225)
for i in ${!totalNodes[@]}; do
  python anynet_file_generate.py \
    --nodes ${totalNodes[$i]} \
    --topology SM_Alter \
    --radix 4
done

totalNodes=(9 16 25 36 49 64 81 100 121 144 169 196 225 256)
for i in ${!totalNodes[@]}; do
  python anynet_file_generate_v2.py \
    --nodes ${totalNodes[$i]} \
    --topology SM_Bi \
    --radix 5
done

totalNodes=(16 36 64 100 144 196 256)
for i in ${!totalNodes[@]}; do
  python anynet_file_generate_v2.py \
    --nodes ${totalNodes[$i]} \
    --topology SM_Alter \
    --radix 4
done

totalNodes=(9 25 49 81 121 169 225)
for i in ${!totalNodes[@]}; do
  python anynet_file_generate_v2.py \
    --nodes ${totalNodes[$i]} \
    --topology SM_Alter \
    --radix 4
done