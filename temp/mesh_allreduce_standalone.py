import argparse
import copy
import sys
import os
import math
import numpy as np
from copy import deepcopy

# sys.path.append('{}/src/allreduce/network'.format(os.environ['SIMHOME']))

# from network import construct_network
# from allreduce import Allreduce


class MeshAllreduce():
    def __init__(self, args, network):
        # super().__init__(args, network)
        self.args = args
        self.number_of_nodes = None
        self.trees = None
        self.ring = []
        self.full_trees = None
        self.partial_trees = None


    '''
    compute_trees() - computes allreduce rings (special tree) for the given network
    @kary: not used, skip
    @alternate: not used, skip
    @sort: not used, skip
    @verbose: print detailed info of ring construction process
    '''
    def compute_trees(self, kary=None, alternate=True, sort=False, verbose=False):
        trees = {}
        template_trees = {}
        nodes_in_trees = {}
        node_queues = {}
        self.number_of_nodes = self.args.num_hmcs
        connectivity = {}
        all_edge_list = []
        links_next_available = {}
        for i in range(self.number_of_nodes):
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
            elif i == self.number_of_nodes - 1:
                connectivity[i].append(self.number_of_nodes - 2)
                all_edge_list.append((self.number_of_nodes - 1, self.number_of_nodes - 2))
                links_next_available[(i, self.number_of_nodes - 2)] = 0
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

        for t in range(self.number_of_nodes - 1):
            for i in range(self.number_of_nodes):
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
        last_trees[self.number_of_nodes-1] = template_trees[self.number_of_nodes-1]
        # self.last_trees = last_trees

        # for node in connectivity.keys():
        #     neighbor_list = connectivity[node]
        #     for neighbor in neighbor_list:
        #         links_next_available[(node, neighbor)] = 0
        # print(links_next_available)
        time_relative_links = {}
        time_relative_links_last = {}
        for i in range(self.number_of_nodes - 1):
            time_relative_links[i] = []
            time_relative_links_last[i] = []
        for key in template_trees.keys():
            tree = template_trees[key]
            for edge in tree:
                time_relative_links[edge[2]].append((edge[0], edge[1], key))
            if key == 0 or key == self.number_of_nodes - 1:
                for edge in tree:
                    time_relative_links_last[edge[2]].append((edge[0], edge[1], key))

        full_trees = []
        total_full_trees = self.args.total_full_trees
        self.total_full_trees = total_full_trees
        for cnt in range(total_full_trees):
            new_trees = {}
            for i in range(self.number_of_nodes):
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
        total_partial_trees = self.args.total_partial_trees
        self.total_partial_trees = total_partial_trees
        data_partial_tree = math.ceil(self.number_of_nodes / 2)
        first_link = (1, 0)
        self.timesteps = 0
        for cnt in range(total_partial_trees):
            new_trees = {}
            new_trees[0] = []
            threshold = links_next_available[first_link]
            new_trees[self.number_of_nodes-1] = []
            for timestep in time_relative_links_last.keys():
                edges_in_timestep = time_relative_links_last[timestep]
                for edge in edges_in_timestep:
                    for d in range(data_partial_tree):
                        next_free_time = links_next_available[(edge[0], edge[1])]
                        if threshold > next_free_time:
                            next_free_time = threshold
                        new_trees[edge[2]].append((edge[0], edge[1], next_free_time))
                        if next_free_time > self.timesteps:
                            self.timesteps = next_free_time
                        links_next_available[(edge[0], edge[1])] = next_free_time + 1
                        if next_free_time not in unused_links.keys():
                            unused_links[next_free_time] = copy.deepcopy(all_edge_list)
                        unused_links[next_free_time].remove((edge[0], edge[1]))
                threshold += data_partial_tree
            partial_trees.append(new_trees)
        self.full_trees = full_trees
        self.partial_trees = partial_trees
        self.timesteps += 1
        print("Total unused links")
        for key in unused_links.keys():
            print("Timestamp " + str(key+1) + ": " + str(unused_links[key]))
    # def compute_trees(self, kary=None, alternate=True, sort=False, verbose=False)


    '''
    generate_schedule()
    @verbose: print the generated schedules

    desc - generate reduce_scatter_schedule and all_gather_schedule from ring,
           verified with generate_schedule in MultiTree
    '''
    def generate_schedule(self, verbose=False):
        # compute parent-children dependency
        self.trees_parent = {}
        self.trees_children = {}
        for root in range(self.network.nodes):
            self.trees_parent[root] = {}
            self.trees_parent[root][root] = None
            self.trees_children[root] = {}
            for node in range(self.network.nodes):
                self.trees_children[root][node] = []
            for edge in self.full_trees[0][root]:
                child = edge[0]
                parent = edge[1]
                self.trees_parent[root][child] = parent
                self.trees_children[root][parent].append(child)

        # initialize the schedules
        reduce_scatter_schedule = {}
        all_gather_schedule = {}

        # construct schedules for each node from trees
        for node in range(self.network.nodes):
            reduce_scatter_schedule[node] = {}
            all_gather_schedule[node] = {}

        reduce_scatter_ni = np.zeros((self.network.nodes, self.timesteps), dtype=int)
        all_gather_ni = np.zeros((self.network.nodes, self.timesteps), dtype=int)
        for t in range(self.total_full_trees):
            for root in range(self.network.nodes):
                for edge in self.full_trees[t][root]:
                    # reduce-scatter
                    rs_child = edge[0]
                    rs_parent = edge[1]
                    rs_timestep = self.timesteps - edge[2] - 1

                    # send from rs_child to rs_parent for tree root at rs_timestep
                    if rs_timestep not in reduce_scatter_schedule[rs_child].keys():
                        reduce_scatter_schedule[rs_child][rs_timestep] = {}
                    flow_children = [(root, child) for child in self.trees_children[root][rs_child]]
                    reduce_scatter_schedule[rs_child][rs_timestep][root] = (
                        (rs_parent, reduce_scatter_ni[rs_parent][rs_timestep]), flow_children, 1, rs_timestep)
                    reduce_scatter_ni[rs_parent][rs_timestep] = (reduce_scatter_ni[rs_parent][
                                                                     rs_timestep] + 1) % self.args.radix

                    # all-gather
                    ag_child = edge[0]
                    ag_parent = edge[1]
                    ag_timestep = edge[2]

                    # send from ag_parent to ag_child for tree root at ag_timestep
                    if ag_timestep not in all_gather_schedule[ag_parent].keys():
                        all_gather_schedule[ag_parent][ag_timestep] = {}
                    if root not in all_gather_schedule[ag_parent][ag_timestep].keys():
                        if ag_parent == root:
                            assert self.trees_parent[root][ag_parent] == None
                            all_gather_schedule[ag_parent][ag_timestep][root] = (
                                [], None, 1, self.timesteps + ag_timestep + 1)
                        else:
                            all_gather_schedule[ag_parent][ag_timestep][root] = (
                                [], (root, self.trees_parent[root][ag_parent]), 1, ag_timestep + self.timesteps + 1)
                    all_gather_schedule[ag_parent][ag_timestep][root][0].append(
                        (ag_child, all_gather_ni[ag_child][ag_timestep]))
                    all_gather_ni[ag_child][ag_timestep] = (all_gather_ni[ag_child][ag_timestep] + 1) % self.args.radix

        print(reduce_scatter_schedule)
        partial_tree_roots = [0, self.network.nodes-1]
        for t in range(self.total_partial_trees):
            for root in partial_tree_roots:
                ni_selector = {}
                for edge in self.partial_trees[t][root]:
                    # reduce-scatter
                    rs_child = edge[0]
                    rs_parent = edge[1]
                    rs_timestep = self.timesteps - edge[2] - 1

                    # send from rs_child to rs_parent for tree root at rs_timestep
                    if rs_timestep not in reduce_scatter_schedule[rs_child].keys():
                        reduce_scatter_schedule[rs_child][rs_timestep] = {}
                    flow_children = [(root, child) for child in self.trees_children[root][rs_child]]
                    if (rs_child, rs_parent) in ni_selector.keys():
                        reduce_scatter_schedule[rs_child][rs_timestep][root] = (
                            (rs_parent, ni_selector[(rs_child, rs_parent)]), flow_children, 1, rs_timestep)
                    else:
                        reduce_scatter_schedule[rs_child][rs_timestep][root] = (
                            (rs_parent, reduce_scatter_ni[rs_parent][rs_timestep]), flow_children, 1, rs_timestep)
                        ni_selector[(rs_child, rs_parent)] = reduce_scatter_ni[rs_parent][rs_timestep]
                        reduce_scatter_ni[rs_parent][rs_timestep] = (reduce_scatter_ni[rs_parent][
                                                                         rs_timestep] + 1) % self.args.radix

                    # all-gather
                    ag_child = edge[0]
                    ag_parent = edge[1]
                    ag_timestep = edge[2]

                    # send from ag_parent to ag_child for tree root at ag_timestep
                    if ag_timestep not in all_gather_schedule[ag_parent].keys():
                        all_gather_schedule[ag_parent][ag_timestep] = {}
                    if root not in all_gather_schedule[ag_parent][ag_timestep].keys():
                        if ag_parent == root:
                            assert self.trees_parent[root][ag_parent] == None
                            all_gather_schedule[ag_parent][ag_timestep][root] = (
                                [], None, 1, self.timesteps + ag_timestep + 1)
                        else:
                            all_gather_schedule[ag_parent][ag_timestep][root] = (
                                [], (root, self.trees_parent[root][ag_parent]), 1, ag_timestep + self.timesteps + 1)
                    all_gather_schedule[ag_parent][ag_timestep][root][0].append(
                        (ag_child, all_gather_ni[ag_child][ag_timestep]))
                    all_gather_ni[ag_child][ag_timestep] = (all_gather_ni[ag_child][ag_timestep] + 1) % self.args.radix
        print(reduce_scatter_schedule)

        # initialize the schedules
        self.reduce_scatter_schedule = {}
        self.all_gather_schedule = {}

        for node in range(self.network.nodes):
            self.reduce_scatter_schedule[node] = []
            self.all_gather_schedule[node] = []
            if verbose:
                print('Accelerator {}:'.format(node))
                print('  reduce-scatter schedule:')
            for timestep in range(self.timesteps):
                if timestep in reduce_scatter_schedule[node].keys():
                    self.reduce_scatter_schedule[node].append(reduce_scatter_schedule[node][timestep])
                    if verbose:
                        print('    timestep {}: {}'.format(timestep, reduce_scatter_schedule[node][timestep]))
                else:
                    self.reduce_scatter_schedule[node].append(None)
                    if verbose:
                        print('    timestep {}: no scheduled communication in this timestep'.format(timestep))
            flow_children = [(node, child) for child in self.trees_children[node][node]]
            self.reduce_scatter_schedule[node].append({node: ((None, None), flow_children, 0, self.timesteps)})
            if verbose:
                print('    root children: {}'.format(self.reduce_scatter_schedule[node][-1]))

            if verbose:
                print('  all-gather schedule:')
            for timestep in range(self.timesteps):
                if timestep in all_gather_schedule[node].keys():
                    self.all_gather_schedule[node].append(all_gather_schedule[node][timestep])
                    if verbose:
                        print('    timestep {}: {}'.format(timestep, all_gather_schedule[node][timestep]))
                else:
                    self.all_gather_schedule[node].append(None)
                    if verbose:
                        print('    timestep {}: no scheduled communication in this timestep'.format(timestep))

        if verbose:
            print('\nSchedule Tables:')
            for node in range(self.network.nodes):
                print(' Accelerator {}:'.format(node))
                for timestep in range(self.timesteps):
                    if self.reduce_scatter_schedule[node][timestep] == None:
                        print('   - NoOp')
                    else:
                        for flow, schedule in self.reduce_scatter_schedule[node][timestep].items():
                            print('   - Reduce, FlowID {}, Parent {}, Children {}, Step {}'.format(flow, schedule[0][0],
                                                                                                   [ele[1] for ele in
                                                                                                    schedule[1]],
                                                                                                   timestep))

                for timestep in range(self.timesteps):
                    if self.all_gather_schedule[node][timestep] == None:
                        print('   - NoOp')
                    else:
                        for flow, schedule in self.all_gather_schedule[node][timestep].items():
                            if schedule[1] == None:
                                parent = 'nil'
                            else:
                                parent = schedule[1][1]
                            print('   - Gather, FlowID {}, Parent {}, Children {}, Step {}'.format(flow, parent,
                                                                                                   [ele[0] for ele in
                                                                                                    schedule[0]],
                                                                                                   self.timesteps + timestep))

            print('\nAggregation Table:')
            aggregation_table = {}
            for node in range(self.network.nodes):
                aggregation_table[node] = {}

            for timestep in range(self.timesteps):
                for node in range(self.network.nodes):
                    if self.reduce_scatter_schedule[node][timestep] != None:
                        for flow, schedule in self.reduce_scatter_schedule[node][timestep].items():
                            parent = schedule[0][0]
                            if timestep not in aggregation_table[parent].keys():
                                aggregation_table[parent][timestep] = {flow: [node]}
                            elif flow not in aggregation_table[parent][timestep]:
                                aggregation_table[parent][timestep][flow] = [node]
                            else:
                                aggregation_table[parent][timestep][flow].append(node)

            for node in range(self.network.nodes):
                print(' Accelerator {}:'.format(node))
                for timestep in sorted(aggregation_table[node].keys()):
                    for flow, children in aggregation_table[node][timestep].items():
                        print('   - FlowID {}, Children {}, Step {}'.format(flow, children, timestep))
        print("Done")
    # def generate_schedule(self, verbose=False)


    '''
    generate_ring_dotfile() - generate dotfile for computed rings
    @filename: name of dotfile
    '''
    def generate_ring_dotfile(self, filename):
        # color palette for ploting nodes of different tree levels
        colors = ['#f7f4f9', '#e7e1ef', '#d4b9da', '#c994c7', '#df65b0',
                '#e7298a', '#ce1256', '#980043', '#67001f']

        ring = 'digraph ring {\n'
        ring += '  rankdir = BT;\n'
        ring += '  /* ring */\n'

        for tree_no in range(len(self.full_trees)):
            trees = self.full_trees[tree_no]
            for i in range(self.number_of_nodes):
                for edge in trees[i]:
                    ring += '  {} -> {} [ label="{}"];\n'.format('"' + str(tree_no) + "-" + str(i) + '-' + str(edge[0]) + '"', '"' + str(tree_no) + "-" + str(i) + '-' + str(edge[1]) + '"', edge[2]+1)
        # ring += '  {} -> {};\n'.format(self.ring[-1], self.ring[0])

        # ring += '  // note that rank is used in the subgraph\n'
        # ring += '  subgraph {\n'
        # ring += '    {rank = same; ' + str(self.ring[0]) + ';}\n'
        # for i in range(1, self.network.nodes // 2):
        #     ring += '    {rank = same; '
        #     ring += '{}; {};'.format(self.ring[i], self.ring[self.network.nodes - i])
        #     ring += '}\n'
        # ring += '    {rank = same; ' + str(self.ring[self.network.nodes // 2]) + ';}\n'

        # ring += '  } /* closing subgraph */\n'
        ring += '}\n'

        f = open(filename, 'w')
        f.write(ring)
        f.close()
    # def generate_ring_dotfile(self, filename)


def main(args):
    # network = construct_network(args)
    # network.to_nodes[1].clear() # test no solution case

    allreduce = MeshAllreduce(args, None)
    allreduce.compute_trees(verbose=args.verbose)
    # allreduce.generate_schedule(verbose=args.verbose)
    # allreduce.max_num_concurrent_flows()
    # if args.gendotfile:
    # allreduce.generate_ring_dotfile('ring.dot')
    #     allreduce.generate_trees_dotfile('ring_trees.dot')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--num-hmcs', default=4, type=int,
                        help='number of nodes, default is 16')
    parser.add_argument('--bigraph-m', default=8, type=int,
                        help='logical groups size (# sub-node per switch), default 8')
    parser.add_argument('--bigraph-n', default=2, type=int,
                        help='# switches, default 2')
    parser.add_argument('--gendotfile', default=False, action='store_true',
                        help='generate tree dotfiles, default is False')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='detailed print')
    parser.add_argument('--booksim-network', default='torus',
                        help='network topology (torus | mesh | dgx2), default is torus')
    parser.add_argument('--kary', default=2, type=int,
                        help='generay kary tree, default is 2 (binary)')
    parser.add_argument('--total-full-trees', default=2, type=int,
                        help='Total number of full trees in mesh')
    parser.add_argument('--total-partial-trees', default=8, type=int,
                        help='Total number of partial trees in mesh')

    args = parser.parse_args()

    main(args)
