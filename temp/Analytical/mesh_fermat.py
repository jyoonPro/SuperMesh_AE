import numpy
import copy
import math

def compute_trees(total_nodes, total_full_trees, total_partial_trees):
    trees = {}
    template_trees = {}
    nodes_in_trees = {}
    node_queues = {}
    number_of_nodes = total_nodes
    connectivity = {}
    all_edge_list = []
    links_next_available = {}
    for i in range(total_nodes):
        trees[i] = []
        template_trees[i] = []
        nodes_in_trees[i] = [i]
        node_queues[i] = []
        node_queues[i].append(i)
        connectivity[i] = []
        if i == 0:
            connectivity[i].append(1)
            all_edge_list.append((0, 1))
            links_next_available[(0, 1)] = 0
        elif i == total_nodes - 1:
            connectivity[i].append(total_nodes - 2)
            all_edge_list.append((total_nodes - 1, total_nodes - 2))
            links_next_available[(i, total_nodes - 2)] = 0
        else:
            connectivity[i].append(i - 1)
            connectivity[i].append(i + 1)
            all_edge_list.append((i, i - 1))
            all_edge_list.append((i, i + 1))
            links_next_available[(i, i - 1)] = 0
            links_next_available[(i, i + 1)] = 0

    timestamp = 0
    unused_links = {}
    unused_links[0] = copy.deepcopy(all_edge_list)

    for t in range(total_nodes - 1):
        for i in range(total_nodes):
            # node_queue = []
            # node_queue.append(i)
            nodes_to_add = []
            while len(node_queues[i]) is not 0:
                taken_node = node_queues[i].pop(0)
                taken_connectivities = connectivity[taken_node]
                for con in taken_connectivities:
                    if con not in nodes_in_trees[i]:
                        template_trees[i].append((con, taken_node, timestamp))
                        nodes_in_trees[i].append(con)
                        nodes_to_add.append(con)
            for node in nodes_to_add:
                node_queues[i].append(node)
        timestamp += 1
    # self.template_trees = trees
    last_trees = {}
    last_trees[0] = template_trees[0]
    last_trees[total_nodes-1] = template_trees[total_nodes-1]
    # self.last_trees = last_trees

    # for node in connectivity.keys():
    #     neighbor_list = connectivity[node]
    #     for neighbor in neighbor_list:
    #         links_next_available[(node, neighbor)] = 0
    # print(links_next_available)
    time_relative_links = {}
    time_relative_links_last = {}
    for i in range(total_nodes - 1):
        time_relative_links[i] = []
        time_relative_links_last[i] = []
    for key in template_trees.keys():
        tree = template_trees[key]
        for edge in tree:
            time_relative_links[edge[2]].append((edge[0], edge[1], key))
        if key == 0 or key == total_nodes - 1:
            for edge in tree:
                time_relative_links_last[edge[2]].append((edge[0], edge[1], key))

    full_trees = []
    # total_full_trees = self.args.total_full_trees
    # self.total_full_trees = total_full_trees
    for cnt in range(total_full_trees):
        new_trees = {}
        for i in range(total_nodes):
            new_trees[i] = []
        for timestep in time_relative_links.keys():
            edges_in_timestep = time_relative_links[timestep]
            for edge in edges_in_timestep:
                next_free_time = links_next_available[(edge[0], edge[1])]
                new_trees[edge[2]].append((edge[0], edge[1], next_free_time))
                links_next_available[(edge[0], edge[1])] = next_free_time + 1
                if next_free_time not in unused_links.keys():
                    unused_links[next_free_time] = copy.deepcopy(all_edge_list)
                unused_links[next_free_time].remove((edge[0], edge[1]))
        full_trees.append(new_trees)
    print("Total unused links")
    for key in unused_links.keys():
        print("Timestamp " + str(key+1) + ": " + str(unused_links[key]))
    partial_trees = []
    # total_partial_trees = self.args.total_partial_trees
    # self.total_partial_trees = total_partial_trees
    data_partial_tree = math.ceil(total_nodes / 2)
    first_link = (1, 0)
    timesteps = 0
    for cnt in range(total_partial_trees):
        new_trees = {}
        new_trees[0] = []
        threshold = links_next_available[first_link]
        new_trees[total_nodes-1] = []
        for timestep in time_relative_links_last.keys():
            edges_in_timestep = time_relative_links_last[timestep]
            for edge in edges_in_timestep:
                for d in range(data_partial_tree):
                    next_free_time = links_next_available[(edge[0], edge[1])]
                    if threshold > next_free_time:
                        next_free_time = threshold
                    new_trees[edge[2]].append((edge[0], edge[1], next_free_time))
                    if next_free_time > timesteps:
                        timesteps = next_free_time
                    links_next_available[(edge[0], edge[1])] = next_free_time + 1
                    if next_free_time not in unused_links.keys():
                        unused_links[next_free_time] = copy.deepcopy(all_edge_list)
                    unused_links[next_free_time].remove((edge[0], edge[1]))
            threshold += data_partial_tree
        partial_trees.append(new_trees)
    # self.full_trees = full_trees
    # self.partial_trees = partial_trees
    timesteps += 1
    # print("Total unused links")
    # for key in unused_links.keys():
    #     print("Timestamp " + str(key+1) + ": " + str(unused_links[key]))
    return timesteps

# n1, n2, latencies, num_messages, flits_per_packet
def fermat(n1, total_trees, latency, num_messages_tto, flits_per_packet):
    # total_full_trees_hiererchical = math.floor(n1 / 2)
    # total_partial_trees_hiererchical = total_trees - total_full_trees_hiererchical
    # timesteps_hiererchical = compute_trees(n1, total_full_trees_hiererchical, total_partial_trees_hiererchical)
    # total_full_trees = math.ceil((n1*n1-1) / 3)
    # total_partial_trees = total_trees
    # time_for_full_tree = math.ceil((n1*n1) / 2) + 1
    # time_for_partial_tree = total_full_trees
    # timesteps = total_full_trees * time_for_full_tree + total_partial_trees * time_for_partial_tree
    timesteps = total_trees + 2 * n1 - 2
    tto = 2 * (num_messages_tto*flits_per_packet*latency*timesteps)
    # timesteps = 100

    # Time = number of messages/(n1*n2) x flits per packet x latency x timesteps x 2
    # return (num_messages*flits_per_packet*latency*timesteps*2)/(n1*n2)
    # fermat_hiererchical = 2 * ((num_messages_hiererchical*flits_per_packet*latency*timesteps_hiererchical) + ((num_messages_hiererchical/2)*flits_per_packet*latency*timesteps_hiererchical))
    # fermat_v2 = 2 * ((num_messages*flits_per_packet*latency*timesteps) + (num_messages*flits_per_packet*latency*((n1/2) - 1)*total_partial_trees) + ((num_messages/n1)*flits_per_packet*latency*timesteps))
    # return fermat_v1, fermat_v2
    # fermat = num_messages * flits_per_packet * latency * timesteps * 2
    # total_full_trees = math.ceil((n1 * n1) / 4)
    # total_partial_trees = total_trees
    # time_for_full_tree = 2 * (n1-1)
    # time_for_partial_tree = total_full_trees
    # timesteps_2 = total_partial_trees + 2 * n1 - 3
    # fermat_2 = 2 * (num_messages_v2 * flits_per_packet * latency * timesteps_2)
    return tto

# print(multitree(4, 4, 10, 100, 25))