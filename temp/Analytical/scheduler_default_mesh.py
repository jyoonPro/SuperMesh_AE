import math

import matplotlib.pyplot as plt
import numpy as np

from mesh_fermat import fermat
from mesh_multitree import multitree
from mesh_one_dim import one_dim
from mesh_two_dim import two_dim_1
from mesh_two_dim import two_dim_2

message_size = 8192
flits_per_packet = 16
bw = 200
nodes = 4


def get_latencies():
    return math.ceil((message_size * 8 / flits_per_packet) / bw)


latency = get_latencies()


def get_one_dim_ring_results(model_size):
    num_messages = math.ceil((model_size * 4) / message_size)
    unidirectional_result, bidirectional_result = one_dim(nodes, nodes, latency, num_messages, flits_per_packet)
    return unidirectional_result, bidirectional_result


def get_two_dim_ring_results(model_size):
    chunks = 4  # number of chunks
    num_messages = math.ceil((model_size * 4) / message_size)
    two_dim_1_result = two_dim_1(chunks, nodes, nodes, latency, num_messages, flits_per_packet)
    two_dim_2_result = two_dim_2(chunks, nodes, nodes, latency, num_messages, flits_per_packet)
    return two_dim_1_result, two_dim_2_result


def get_multitree_results(model_size, multitree_timesteps):
    num_messages = math.ceil((model_size * 4) / message_size)
    multitree_results, multitree_timesteps = multitree(nodes, nodes, latency, num_messages, flits_per_packet, multitree_timesteps)
    return multitree_results, multitree_timesteps


def get_tto_results(model_size):
    num_messages_tto = 4
    total_treesets = math.ceil((model_size * 4) / (num_messages_tto * message_size * 3))
    tto_results = fermat(nodes, total_treesets, latency, num_messages_tto, flits_per_packet)
    return tto_results


def get_results(model_size, multitree_timesteps):
    one_dim_unidirectional_result, one_dim_bidirectional_result = get_one_dim_ring_results(model_size)
    two_dim_1_result, two_dim_2_result = get_two_dim_ring_results(model_size)
    multitree_results, multitree_timesteps = get_multitree_results(model_size, multitree_timesteps)
    tto_results = get_tto_results(model_size)
    return one_dim_unidirectional_result, one_dim_bidirectional_result, two_dim_1_result, two_dim_2_result, multitree_results, tto_results



data_array = [26214400, 52428800, 78643200, 104857600, 131072000, 157286400, 183500800, 209715200, 235929600, 268435456]
one_dim_uni_list = []
one_dim_bi_list = []
two_dim_uni_list = []
two_dim_bi_list = []
multitree_list = []
tto_list = []
multitree_timesteps = None
for datasize in data_array:
    one_dim_unidirectional_result, one_dim_bidirectional_result, two_dim_1_result, two_dim_2_result, multitree_results, tto_results = get_results(model_size=datasize, multitree_timesteps=multitree_timesteps)
    one_dim_uni_list.append(one_dim_unidirectional_result)
    one_dim_bi_list.append(one_dim_bidirectional_result)
    two_dim_uni_list.append(two_dim_1_result)
    two_dim_bi_list.append(two_dim_2_result)
    multitree_list.append(multitree_results)
    tto_list.append(tto_results)


plt.plot(np.array(data_array), np.array(one_dim_uni_list), label="one dim unidirectional", marker='o')
plt.plot(np.array(data_array), np.array(one_dim_bi_list), label="one dim bidirectional", marker='v')
plt.plot(np.array(data_array), np.array(two_dim_uni_list), label="two dim unidirectional", marker='^')
plt.plot(np.array(data_array), np.array(two_dim_bi_list), label="two dim bidirectional", marker='s')
plt.plot(np.array(data_array), np.array(multitree_list), label="multitree", marker='.')
plt.plot(np.array(data_array), np.array(tto_list), label="TTO", marker='p')

plt.xlabel("Data size")
plt.ylabel("Analytically computed cycle number")
plt.title("nodes_" + str(nodes * nodes))
plt.legend(loc="upper left")
plt.savefig("test.png")
