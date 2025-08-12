# needs dimensions, number of chunks, number of npus in each dimesnion, bw of each dimension, topology of each dimension, scf/fifo

import math
import os
import numpy as np
from tabulate import tabulate
from mesh_multitree import multitree
from mesh_one_dim import one_dim
from mesh_two_dim import two_dim_1
from mesh_two_dim import two_dim_2
from mesh_fermat import fermat

import matplotlib.pyplot as plt
import numpy as np

message_size = 8192
flits_per_packet = 16


def get_latencies(bw):
    return math.ceil((message_size * 8 / flits_per_packet) / bw)


def run_it(model_size, nodes, multitree_timesteps, b):
    chunks = 4  # number of chunks
    n1 = nodes  # n1 x n2 mesh
    n2 = nodes

    latencies = get_latencies(b)
    num_messages = math.ceil((model_size * 4) / message_size)
    num_messages_tto = 4
    total_trees = math.ceil((model_size*4)/(num_messages_tto * message_size * 3))
    f = open(
        str(n1) + "_" + str(total_trees) + "/result_" + str(model_size) + ".txt",
        "w")

    f.write(
        "\n-------------------------------------------------------------------------------------------------------\n")
    f.write("CONFIGURATIONS")
    f.write(
        "\n-------------------------------------------------------------------------------------------------------\n")

    mydata = [["Chunks", str(chunks)],
              ["Mesh", str(n1) + " X " + str(n2)],
              ["Bandwidth", str(b)],
              ["Message Size", str(message_size)],
              ["Flits per Packet", str(flits_per_packet)],
              ["Latencies Calculated", str(latencies)],
              ["Parameters in Model", str(model_size)],
              ["Number of messages in Model", str(num_messages)]]

    f.write(tabulate(mydata, tablefmt="plain"))

    f.write(
        "\n\n-------------------------------------------------------------------------------------------------------\n")
    f.write("ANALYTICAL TIME CALCULATION")
    f.write(
        "\n-------------------------------------------------------------------------------------------------------\n")

    multitree_sim, multitree_timesteps = multitree(n1, n2, latencies, num_messages, flits_per_packet,
                                                   multitree_timesteps)
    # multitree_sim = 0
    one_dim_unidirectional_sim, one_dim_bidirectional_sim = one_dim(n1, n2, latencies, num_messages, flits_per_packet)
    two_dim_1_sim = two_dim_1(chunks, n1, n2, latencies, num_messages, flits_per_packet)
    two_dim_2_sim = two_dim_2(chunks, n1, n2, latencies, num_messages, flits_per_packet)
    tto_sim = fermat(n1, total_trees, latencies, num_messages_tto, flits_per_packet)
    f.write("Multitree All Reduce\t\t\t\t\t" + str(multitree_sim) + "\n")
    f.write("1D Ring All Reduce (Unidirectional)\t\t" + str(one_dim_unidirectional_sim) + "\n")
    f.write("1D Ring All Reduce (Bidirectional)\t\t" + str(one_dim_bidirectional_sim) + "\n")
    f.write("2D All Reduce O(n^2)\t\t\t\t\t" + str(two_dim_1_sim) + "\n")
    f.write("2D All Reduce optimized O(n)\t\t\t" + str(two_dim_2_sim) + "\n")
    f.write("TTO All Reduce\t\t\t\t\t" + str(tto_sim) + "\n")
    return multitree_timesteps, multitree_sim, one_dim_unidirectional_sim, one_dim_bidirectional_sim, two_dim_1_sim, two_dim_2_sim, fermat_hiererchical_sim, fermat_sim, fermat_sim_2


def make_model_analysis(multitree_list, fermat_v1_list, fermat_v2_list, training_time, fig_name):
    # species = ("16", "32", "128", "256", "16", "32", "128", "256")
    species = ("128", "256")
    penguin_means = {
        'Training time': training_time,
        'Allreduce time multitree': multitree_list,
        'Allreduce time hierarchical 1D overlap': fermat_v1_list,
        'Allreduce time hierarchical 2D overlap': fermat_v2_list,
        # 'Flipper Length': (189.95, 195.82, 217.19),
    }

    x = np.arange(len(species))  # the label locations
    width = 0.15  # the width of the bars
    multiplier = 0

    fig, ax = plt.subplots(layout='constrained')

    for attribute, measurement in penguin_means.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, label=attribute)
        ax.bar_label(rects, padding=3)
        multiplier += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Cycles')
    # ax.set_title('Penguin attributes by species')
    ax.set_xticks(x + width, species)
    ax.legend(loc='upper left')
    # ax.set_ylim(0, 250)

    # plt.show()
    plt.savefig(fig_name + ".png")



# for datasize in [26214400, 52428800, 78643200, 104857600, 131072000, 157286400, 183500800, 209715200, 235929600, 268435456]:
nodes = 7
total_trees = 86
bw = 200
# total_partial_trees = 8
# os.mkdir(str(nodes) + "_" + str(total_trees))
# data_array = [26214400, 52428800, 78643200, 104857600, 131072000, 157286400, 183500800, 209715200, 235929600, 268435456]
data_array = [2097152]
# data_array = [3745824, 1573620]
# data_array = [3745824]
multitree_list = []
one_dim_uni_list = []
one_dim_bi_list = []
two_dim_uni_list = []
two_dim_bi_list = []
fermat_v1_list = []
fermat_v2_list = []
fermat_v3_list = []
multitree_timesteps = None
for datasize in data_array:
    multitree_timesteps, multitree_sim, one_dim_unidirectional_sim, one_dim_bidirectional_sim, two_dim_1_sim, two_dim_2_sim, fermat_v1, fermat_v2, fermat_v3 = run_it(
        datasize, nodes, total_trees, multitree_timesteps, bw)
    multitree_list.append(multitree_sim)
    # multitree_list.append(multitree_sim)
    # multitree_list.append(multitree_sim)
    # multitree_list.append(multitree_sim)
    one_dim_uni_list.append(one_dim_unidirectional_sim)
    one_dim_bi_list.append(one_dim_bidirectional_sim)
    two_dim_uni_list.append(two_dim_1_sim)
    two_dim_bi_list.append(two_dim_2_sim)
    fermat_v1_list.append(fermat_v1)
    # fermat_v1_list.append(fermat_v1)
    # fermat_v1_list.append(fermat_v1)
    # fermat_v1_list.append(fermat_v1)
    fermat_v2_list.append(fermat_v2)
    # fermat_v2_list.append(fermat_v2)
    # fermat_v2_list.append(fermat_v2)
    # fermat_v2_list.append(fermat_v2)
    fermat_v3_list.append(fermat_v3)


# # training_time_tpu = [4210571, 43763, 1064149, 928096, 1152562, 1832399, 2151722]
# training_time_16 = [343080190, 4736220]
# training_time_32 = [94943410, 1251841]
# training_time_128 = [9927125, 102548]
# training_time_256 = [4210571, 43763]
# # training_time = [343080190, 94943410, 9927125, 4210571, 4736220, 1251841, 102548, 43763]
# training_time_alexnet = [9927125, 4210571]
# training_time_alpha = [102548, 43763]
#
# make_model_analysis(multitree_list, fermat_v1_list, fermat_v2_list, training_time_alexnet, "training_time_alex")

# first plot with X and Y data
plt.plot(np.array(data_array), np.array(multitree_list), label="multitree", marker='.')
if nodes % 2 == 0:
    plt.plot(np.array(data_array), np.array(one_dim_uni_list), label="one dim unidirectional", marker='o')
    plt.plot(np.array(data_array), np.array(one_dim_bi_list), label="one dim bidirectional", marker='v')
else:
    plt.plot(np.array(data_array), np.array(one_dim_uni_list), label="Proposed unidirectional", marker='o')
    plt.plot(np.array(data_array), np.array(one_dim_bi_list), label="Proposed bidirectional", marker='v')
# plt.plot(np.array(data_array), np.array(two_dim_uni_list), label="two dim unidirectional", marker='^')
plt.plot(np.array(data_array), np.array(two_dim_bi_list), label="two dim bidirectional", marker='s')
plt.plot(np.array(data_array), np.array(fermat_v1_list), label="Hiererchical overlap", marker='p')
plt.plot(np.array(data_array), np.array(fermat_v2_list), label="Default overlap", marker='*')
plt.plot(np.array(data_array), np.array(fermat_v3_list), label="Default overlap with 4 tree", marker='*')

plt.xlabel("Data size")
plt.ylabel("Analytically computed cycle number")
plt.title("nodes_" + str(nodes * nodes) + "_trees_" + str(total_trees))
plt.legend(loc="upper left")
# plt.show()
# plt.savefig(str(nodes) + "_" + str(total_trees) + ".png")
plt.savefig("test.png")
