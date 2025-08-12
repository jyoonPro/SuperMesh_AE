## Paper Title: SuperMesh: Energy-Efficient Collective Communications for Accelerators

### Directory Structure
1. micro_2025: Contains the results of all the simulation. This results can be used to reproduce the graphs presented in the paper.
2. src: Contains al the source code
   - allreduce: This subdirectory contains all the AllReduce algortims presented in the paper.
   - booksim2: BookSim2 simulator source code
   - generate_anynet_files: Contains files to generate anynet files of different topologies.
   - SavedTrees: As it takes some time to build the trees when number of accelerators are large, we initially build the tree and load during simulation.
   - SCALE-Sim: Stores code for scale-sim
   - tacos: Contains tacos codes
   - teccl: Contains TE-CCL schedules. We have generated TE-CCL schedules by running their code from github repo and changed the topology.
3. utils: Contains python and shell scripts to reproduce the results.
   - python_scripts: Contains python scripts to reproduce graphs in the paper. It uses results from HPCA_2024_final directory.
   - run_scripts: Contains shell scripts to run the simulations.

### Software Requirements
1. Ubuntu 22.04(Other Ubuntu version should work as well)
2. Python 3.9.5
3. ScaleSim + BookSim(We have included both the simulators with this repository)

### Setup
Create a new virtual environment

`python3 -m venv venv`

Activate the virtual environment

`source venv/bin/activate`

Install the required dependencies from requirements.txt file (If required upgrade the pip)

`pip install -r requirements.txt`

Run the following commands to finalize the environment setup.

`source setup_env.sh`

The above command should show "source successfully" message.

`cd src`

`cd booksim2`

`cd src`

`make clean` 

`make lib`

It binds booksim with python code. Now go back to the root folder.

Run the following commands to update config files topology directory.

`cd src`

`python update_cfg_files.py`

It will update the config file by appending the root directory of your system.
You need to run this just once. After that you can reuse the updated config files for your experiment. Then go back to root folder.



To reproduce the results, we have two options:

1. **Generate Figures from Existing JSONs**:
   All result JSON files are in the `micro_2025` folder. Running the provided Python scripts will generate the paper’s figures from these files.

2. **Regenerate JSON Files via Experiments**:
   If we want to generate the json files as well, scripts are provided to run the experiments in parallel, which may take several days. Each script launches multiple runs. Outputs will be saved in a new folder `micro_2025_new`. To enable plotting, ensure its folder structure matches `micro_2025`.


Now we will explain each of the options in details.

### Option 1: Reproduce the results of the paper using already provided json files.

We are providing all the simulation output files in **micro_2025** folder.
To reproduce the graphs from the papers, first go to the **supermesh_python_scripts** folder

`cd utils/supermesh_python_scripts`

1. To reproduce the results for Figure 9, run the following command. Running the following script will generate a file named *fig_9_bandwidth_pipeline_allreduce.pdf*.
   - `python fig_9_plot_bandwidth_ar.py`
2. To reproduce the results for Figure 10, run the following command. Running the following script will generate a file named *fig_10_bandwidth_rs_ag.pdf*.
   - `python fig_10_plot_bandwidth_rs_ag.py`
3. To reproduce the results for Figure 11, run the following command. Running the following script will generate a file named *fig_11_scalability_both.pdf*.
   - `python fig_11_plot_scalability_both.py`
4. To reproduce the results for Figure 12, run the following command. Running the following script will generate a file named *fig_12_models_dnn_results.pdf*.
   - `python fig_12_plot_model_results.py`
5. To reproduce the results for Figure 13, run the following command. Running the following script will generate a file named *fig_13_llm_models_vaults1.pdf*.
   - `python fig_13_plot_model_results_llm.py`
6. To reproduce the results for Figure 14 & 15, run the following command. Running the following script will generate a file named *fig_14_data_size_power_energy_64.pdf* & *fig_15_data_size_all_topo_energy_64.pdf*.
   - `python fig_14_15_plot_data_size_power_energy.py`
7. To reproduce the results for Figure 16, run the following command. Running the following script will generate a file named *fig_16_bandwidth_others.pdf*.
   - `python fig_16_plot_bandwidth_others.py`
8. To reproduce the results for Figure 17, run the following command. Running the following script will generate a file named *fig_17_bandwidth_fixed_topo.pdf*.
   - `python fig_17_plot_bandwidth_fixed_topo.py`
9. To reproduce the results for Figure 18, run the following command. Running the following script will generate a file named *fig_18_link_utl_134217728_updated_new.pdf*.
   - `python fig_18_plot_link_utilization.py`
10. To reproduce the results for Figure 19, run the following command. Running the following script will generate a file named *fig_19_bandwidth_different_topo_updated.pdf*.
    - `python fig_19_plot_bandwidth_different_topo.py`
11. To reproduce the results for Figure 20, run the following command. Running the following script will generate a file named *fig_20_bandwidth_fixed_topo_partial.pdf*.
    - `python fig_20_plot_bandwidth_fixed_topo_partial.py`
12. To reproduce the results for Figure 21, run the following command. Running the following script will generate a file named *fig_21_bandwidth_a2a_9.pdf*.
    - `python fig_21_plot_bandwidth_a2a.py`
13. To reproduce the results for Figure 22, run the following command. Running the following script will generate a file named *fig_22_injection_vs_latency_tornado.pdf* & *fig_23_injection_vs_latency_uniform.pdf*.
    - `python fig_22_random_comm_results.py`


## Option 2: Reproduce the json files


This step involves reproducing the JSON files, which requires running actual simulations using BookSim. Each script file can launch over 50 parallel Python programs and may take 2–4 days to complete.
**Before running these scripts**, make sure to activate the virtual environment and source `setup_env.sh`.

The scripts are provided in the `utils/supermesh_scripts` folder and are used to reproduce all results.
Note that most scripts execute multiple simulations in parallel, so running them on a machine with limited cores may consume significant system resources.

Executing the scripts will create a `micro_2025_new` folder in the root directory, where all outputs will be stored. Each simulation will generate a log file and a JSON file—the JSON files (containing the results) will be in the `json` folder, and the logs in the `logs` folder.

The number of simulation cycles can be found in the `results/performance` section of each JSON file.