import numpy as np
import math

# Predicts latency of current chunk based on chunksize, npus, bw and topology
def latency_predictor(datasize, current_npus, current_bw, current_topology):
    if current_topology == "mesh_1":
        return (current_npus-1)*(current_npus-1)*1/(current_npus)*datasize*(1/current_bw)
    elif current_topology == "mesh_2":
        return (2*current_npus-3)*1/(current_npus)*datasize*(1/current_bw)
    else:
        raise RuntimeError("TOPOLOGY UNDEFINED\nChoose one of these:mesh_1, mesh_2\n")

# Inter Dimension Scheduler - THEMIS Algorithm
def inter_scheduler(C, chunk_id, dim_wise_load, inter_schedule, D, N, B, T):
    # index sorted : lowest load to highest load, start with highest bandwidth for 1st chunk
    if chunk_id == 0:
        sorted_schedule = np.argsort(B)[::-1]
    else:
        sorted_schedule = np.argsort(dim_wise_load)

    # If difference between max and min is less than threshold, then assign load in order of decreasing bandwidth. Threshold as mentioned in THEMIS paper.
    # We set the Threshold to be the estimated runtime (predicted by the Latency Model) when running an RS/AG of size chunkSize/16 on the dimension with the lowest current load.
    threshold = latency_predictor(1/(16*C), N[sorted_schedule[0]], B[sorted_schedule[0]], T[sorted_schedule[0]])
    if max(dim_wise_load)-min(dim_wise_load) < threshold:
        sorted_schedule = np.argsort(B)[::-1]
    
    # Update schedule for each dimension by going through the sorted list of dimensions
    chunk_size = 1/C
    ag = D*2
    for i in range(D):
        # dimension of current chunk:
        d = sorted_schedule[i]
        # returns load for dimension d according to topology, bw and no. of npus
        load = latency_predictor(chunk_size, N[d], B[d], T[d])
        inter_schedule[d].append([d, chunk_id, i+1, chunk_size, load, 0])   #RS
        inter_schedule[d].append([d, chunk_id, ag, chunk_size, load, 1])    #AG
        ag = ag-1
        load = 2*load
        chunk_size = chunk_size/N[d]
        # updates load list
        dim_wise_load[d] = dim_wise_load[d] + load
    return

# Intra Scheduler
def intra_scheduler(inter_schedule, S, C, D):
    output = []
    done = []
    current_t = []
    for d in range(D):
        output.append([])       # final schedule with both intra and inter algos
        current_t.append(0)     # current time in dimension
    for c in range(C):
        done.append([0,0])      # chunk c has done 0 timesteps and is busy till 0.
    
    chunks_left = True          # bool to see if need to stop the algorithm or not
    while chunks_left:
        all_empty = True        # bool to check if all dimension are empty
        for d in range(D):
            if len(inter_schedule[d])!=0:
                all_empty = False   # if any dim non empty change all_empty bool
                available = []
                # find all chunks whose previous ts has already been scheduled
                for chunk in inter_schedule[d]:
                    if done[chunk[1]][0]+1 == chunk[2]:
                        # if this chunk is next in the order of timesteps
                        # available has the available chunks and when it can schedule it at the earliest
                        if done[chunk[1]][1] < current_t[d]:
                            done[chunk[1]][1] = current_t[d]
                        available.append([chunk, done[chunk[1]][1]])
                # if none of the chunks available now, move on to another dimensions
                if len(available) == 0:
                    continue
                # get chunks with minimum wait time
                # print(available)
                min_wait = min(x[1] for x in available)
                min_wait_chunks = [x[0] for x in available if x[1] == min_wait]
                if S:
                    # choose chunk with lowest timeload
                    min_timeload = min(x[4] for x in min_wait_chunks)
                    min_timeload_chunks = [x for x in min_wait_chunks if x[4] == min_timeload]
                    next = min_timeload_chunks[0]
                    output[d].append(next)
                    done[next[1]][0] = done[next[1]][0] + 1
                    done[next[1]][1] = min_wait + next[4]
                    current_t[d] = done[next[1]][1]
                    inter_schedule[d].remove(next)
                else:
                    # choose first chunk available
                    next = min_wait_chunks[0]
                    output[d].append(next)
                    done[next[1]][0] = done[next[1]][0] + 1
                    done[next[1]][1] = min_wait + next[4]
                    current_t[d] = done[next[1]][1]
                    inter_schedule[d].remove(next)
        if all_empty:
            chunks_left = False     # all chunks have been intra scheduled in all dimensions
    # print(done)
    last_end = 0
    for c in range(C):
        last_end = done[c][1] if done[c][1] > last_end else last_end
    # print("ALL CHUNKS FINISH AT " + str(last_end))
    return output

# Scheduler
def get_themis_schedule(C, D, N, B, T, S):
    # dim_wise_load : load
    dim_wise_load = np.zeros(D, dtype = float)
    # inter dimension schedule found using THEMIS algorithm
    inter_schedule = []
    for d in range(D):
        inter_schedule.append([])
    for chunk_id in range(C):
        inter_scheduler(C, chunk_id, dim_wise_load, inter_schedule, D, N, B, T)
    # print(dim_wise_load)
    # inter_schedule has : dimension, chunkid, timestep, datasize, timeload
    intra_schedule = intra_scheduler(inter_schedule, S, C, D)
    return intra_schedule

def get_theoretical_analysis(schedule, topology, npus, latencies, num_messages, flits_per_packet):
    per_dimension_time = []
    for d in range(len(schedule)):
        per_dimension_time.append(0)
        for chunk in schedule[d]:
            if topology[d] == "mesh_1":
                # FOR MESH TYPE 1 : Time = (number of messages) X (Datachunk to be handled/n) X (n-1)*(n-1)
                per_dimension_time[d] = per_dimension_time[d] + (flits_per_packet)*latencies[d]*math.ceil(num_messages*chunk[3])*(npus[d]-1)*(npus[d]-1)/npus[d]
            if topology[d] == "mesh_2":
                # FOR MESH TYPE 1 : Time = (number of messages) X (Datachunk to be handled/n) X (2n-3)
                per_dimension_time[d] = per_dimension_time[d] + (flits_per_packet)*latencies[d]*math.ceil(num_messages*chunk[3])*(2*npus[d]-3)/npus[d]
    return per_dimension_time

def two_dim_1(chunks, n1, n2, latency, num_messages, flits_per_packet):
    # n1 x n2 mesh with bandwidths bw1 x bw1 (homogenous) and using chunks take how many cycles
    themis_schedule = get_themis_schedule(chunks, 2, [n1, n2], [1, 1], ["mesh_1", "mesh_1"], 1)
    dim_wise_time = get_theoretical_analysis(themis_schedule, ["mesh_1", "mesh_1"], [n1, n2], [latency, latency], num_messages, flits_per_packet)
    return np.max(dim_wise_time)

def two_dim_2(chunks, n1, n2, latency, num_messages, flits_per_packet):
    # n1 x n2 mesh with bandwidths bw1 x bw1 (homogenous) and using chunks take how many cycles
    themis_schedule = get_themis_schedule(chunks, 2, [n1, n2], [1, 1], ["mesh_2", "mesh_2"], 1)
    dim_wise_time = get_theoretical_analysis(themis_schedule, ["mesh_2", "mesh_2"], [n1, n2], [latency, latency], num_messages, flits_per_packet)
    return np.max(dim_wise_time)

# chunks, n1, n2, latency, num_messages, flits_per_packet
# print(two_dim_1(4, 4, 4, 10, 100, 25))
# print(two_dim_2(4, 4, 4, 10, 100, 25))