## Run Instructions

### Base 1(currently available on hetero-optimal-tree branch):
```
source setup_env.sh
cd utils/hetero_scripts
./launch_torus_multitree_base1.sh
```

### Base 2(currently available on hetero-optimal-tree branch):
```
source setup_env.sh
cd utils/hetero_scripts
./launch_torus_multitree_base2.sh
```

### Base 3(currently available on hetero-optimal-tree branch):
```
source setup_env.sh
cd utils/hetero_scripts
./launch_torus_multitree_base3.sh
```


### For TACOS:
```
./utils/build_docker_image.sh
./utils/start_docker_container.sh
./tacos.sh
```