import json
import math




# Path to the JSON file
file_path = 'Alltoall.n8-NDv2-NDv2_1MB-steps4-tacclsol-improve-1721938333_taccl.sccl.json'

schedules = []
total_nodes = 4
input_map = {}
output_map = {}
# Read and parse the JSON file
with open(file_path, 'r') as file:
    data = json.load(file)
    steps = data['steps']
    timestep = 0
    time = 0
    temp_input_map = data['input_map']
    for key in temp_input_map.keys():
        input_map[int(key)] = temp_input_map[key]
    temp_output_map = data['output_map']
    for key in temp_output_map.keys():
        output_map[int(key)] = temp_output_map[key]
    for step in steps:
        sends_list = step['sends']
        for send in sends_list:
            if send[3] != time:
                assert send[3] > time
                time = send[3]
                timestep += 1
            schedules.append([send[0], send[1], send[2], timestep])

    chunk_wise_path = {}
    for schedule in schedules:
        if schedule[0] not in chunk_wise_path:
            chunk_wise_path[schedule[0]] = {}
            chunk_wise_path[schedule[0]]['src'] = schedule[1]
            chunk_wise_path[schedule[0]]['dest'] = [schedule[2]]
            chunk_wise_path[schedule[0]]['time'] = [schedule[3]]
            chunk_wise_path[schedule[0]]['final_dest'] = schedule[2]
        else:
            assert schedule[1] == chunk_wise_path[schedule[0]]['dest'][-1]
            assert schedule[3] >= chunk_wise_path[schedule[0]]['time'][-1]
            chunk_wise_path[schedule[0]]['dest'].append(schedule[2])
            chunk_wise_path[schedule[0]]['time'].append(schedule[3])
            chunk_wise_path[schedule[0]]['final_dest'] = schedule[2]

print(schedules)