import math

import matplotlib.pyplot as plt
import numpy as np

from mesh_fermat import fermat
from mesh_multitree import multitree
from mesh_one_dim import one_dim
from mesh_two_dim import two_dim_1
from mesh_two_dim import two_dim_2
from fatmesh_multitree_all import fatmesh_multitree_all
from fatmesh_multitree_alternate import fatmesh_multitree_alternate
from fatmesh_multitree_unidirectional import fatmesh_multitree_unidirectional

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
    multitree_results, _ = multitree(nodes, nodes, latency, num_messages, flits_per_packet, None)
    print(multitree_results)
    return multitree_results, None


def get_tto_results(model_size):
    num_messages_tto = 4
    total_treesets = math.ceil((model_size * 4) / (num_messages_tto * message_size * 3))
    tto_results = fermat(nodes, total_treesets, latency, num_messages_tto, flits_per_packet)
    return tto_results


def get_tto_results_fatmesh(model_size):
    num_messages_tto = 4
    total_treesets = math.ceil((model_size * 4) / (num_messages_tto * message_size * 4))
    tto_results = fermat(nodes, total_treesets, latency, num_messages_tto, flits_per_packet)
    return tto_results


def get_multitree_fatmesh_all_results(model_size):
    num_messages = math.ceil((model_size * 4) / message_size)
    multitree_fatmesh_all_results, _ = fatmesh_multitree_all(nodes, nodes, latency, num_messages, flits_per_packet, None)
    print(multitree_fatmesh_all_results)
    return multitree_fatmesh_all_results, None


def get_multitree_fatmesh_alternate_results(model_size):
    num_messages = math.ceil((model_size * 4) / message_size)
    multitree_fatmesh_alternate_results, _ = fatmesh_multitree_alternate(nodes, nodes, latency, num_messages, flits_per_packet, None)
    print(multitree_fatmesh_alternate_results)
    return multitree_fatmesh_alternate_results, None


def get_multitree_fatmesh_unidirectional_results(model_size):
    num_messages = math.ceil((model_size * 4) / message_size)
    multitree_fatmesh_unidirectional_results, _ = fatmesh_multitree_unidirectional(nodes, nodes, latency, num_messages, flits_per_packet, None)
    print(multitree_fatmesh_unidirectional_results)
    return multitree_fatmesh_unidirectional_results, None


def get_results(model_size, multitree_timesteps):
    one_dim_unidirectional_result, one_dim_bidirectional_result = get_one_dim_ring_results(model_size)
    two_dim_1_result, two_dim_2_result = get_two_dim_ring_results(model_size)
    multitree_results, multitree_timesteps = get_multitree_results(model_size, multitree_timesteps)
    tto_results = get_tto_results(model_size)
    tto_fatmesh_results = get_tto_results_fatmesh(model_size)
    multitree_fatmesh_all_results, _ = get_multitree_fatmesh_all_results(model_size)
    multitree_fatmesh_alternate_results, _ = get_multitree_fatmesh_alternate_results(model_size)
    multitree_fatmesh_unidirectional_results, _ = get_multitree_fatmesh_unidirectional_results(model_size)
    return one_dim_unidirectional_result, one_dim_bidirectional_result, two_dim_1_result, two_dim_2_result, multitree_results, tto_results, tto_fatmesh_results, multitree_fatmesh_all_results, multitree_fatmesh_alternate_results, multitree_fatmesh_unidirectional_results



data_array = [26214400, 52428800, 78643200, 104857600, 131072000, 157286400, 183500800, 209715200, 235929600, 268435456]
one_dim_uni_list = []
one_dim_bi_list = []
two_dim_uni_list = []
two_dim_bi_list = []
multitree_list = []
tto_list = []
tto_fatmesh_list = []
multitree_fatmesh_all_list = []
multitree_fatmesh_alternate_list = []
multitree_fatmesh_unidirectional_list = []
multitree_timesteps = None
for datasize in data_array:
    one_dim_unidirectional_result, one_dim_bidirectional_result, two_dim_1_result, two_dim_2_result, multitree_results, tto_results, tto_fatmesh_results, multitree_fatmesh_all_results, multitree_fatmesh_alternate_results, multitree_fatmesh_unidirectional_results = get_results(model_size=datasize, multitree_timesteps=multitree_timesteps)
    one_dim_uni_list.append(one_dim_unidirectional_result)
    one_dim_bi_list.append(one_dim_bidirectional_result)
    two_dim_uni_list.append(two_dim_1_result)
    two_dim_bi_list.append(two_dim_2_result)
    multitree_list.append(multitree_results)
    tto_list.append(tto_results)
    tto_fatmesh_list.append(tto_fatmesh_results)
    multitree_fatmesh_all_list.append(multitree_fatmesh_all_results)
    multitree_fatmesh_alternate_list.append(multitree_fatmesh_alternate_results)
    multitree_fatmesh_unidirectional_list.append(multitree_fatmesh_unidirectional_results)



# plt.plot(np.array(data_array), np.array(one_dim_uni_list), label="one dim unidirectional", marker='o')
plt.plot(np.array(data_array), np.array(one_dim_bi_list), label="one dim bidirectional", marker='v')
# plt.plot(np.array(data_array), np.array(two_dim_uni_list), label="two dim unidirectional", marker='^')
# plt.plot(np.array(data_array), np.array(two_dim_bi_list), label="two dim bidirectional", marker='s')
plt.plot(np.array(data_array), np.array(multitree_list), label="multitree_mesh", marker='.')
plt.plot(np.array(data_array), np.array(multitree_fatmesh_all_list), label="MultiTree_fatmesh_all", marker='*')
plt.plot(np.array(data_array), np.array(multitree_fatmesh_alternate_list), label="MultiTree_fatmesh_alternate", marker='*')
plt.plot(np.array(data_array), np.array(multitree_fatmesh_unidirectional_list), label="MultiTree_fatmesh_unidirectional", marker='*')
plt.plot(np.array(data_array), np.array(tto_list), label="TTO_mesh", marker='p')
plt.plot(np.array(data_array), np.array(tto_fatmesh_list), label="TTO_fatmesh_all", marker='o')
plt.plot(np.array(data_array), np.array(tto_fatmesh_list), label="TTO_fatmesh_alternate", marker='^')
plt.plot(np.array(data_array), np.array(tto_fatmesh_list), label="TTO_fatmesh_unidirectional", marker='s')

plt.xlabel("Data size")
plt.ylabel("Analytically computed cycle number")
plt.title("nodes_" + str(nodes * nodes))
plt.legend(loc="upper left")
plt.savefig("allreduce_scheme_1_2_3.png")
