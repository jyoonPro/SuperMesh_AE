import argparse
import copy
import random

import numpy as np
from copy import deepcopy
import sys
import os
import time
import pickle

sys.path.append('{}/src/allreduce/network'.format(os.environ['SIMHOME']))

from network import construct_network
from allreduce import Allreduce

import logging
logger = logging.getLogger(__name__)

class PipelinedRSAG(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)

    def compute_trees_from_timestep(self, local_tree_nodes, local_sorted_roots, local_trees):
        time_tracker = {}
        changed_tracker = {}
        highest_length = {}
        for root in local_sorted_roots:
            changed_tracker[root] = False
            time_tracker[root] = {}
            time_tracker[root][root] = 0
            highest_length[root] = 0
        finished = False
        switch_to_switch = deepcopy(self.network.switch_to_switch)
        turns = 0
        while not finished:
            root = local_sorted_roots[turns % len(local_sorted_roots)]
            if len(local_tree_nodes[root]) < self.network.nodes:
                added = False
                for parent in local_tree_nodes[root]:
                    neighbor_switches = deepcopy(switch_to_switch[parent])
                    for child in neighbor_switches:
                        if child not in local_tree_nodes[root]:
                            switch_to_switch[parent].remove(child)
                            local_tree_nodes[root].append(child)
                            local_trees[root].append((child, parent, time_tracker[root][parent] + 1))
                            time_tracker[root][child] = time_tracker[root][parent] + 1
                            if time_tracker[root][child] > highest_length[root]:
                                highest_length[root] = time_tracker[root][child]
                            changed_tracker[root] = True
                            added = True
                            break
                    if added:
                        break
            turns += 1
            if turns % len(local_sorted_roots) == 0:
                if any(list(changed_tracker.values())):
                    finished = False
                    for root in local_sorted_roots:
                        changed_tracker[root] = False
                else:
                    finished = True
        num_trees = 0
        for root in local_sorted_roots:
            if len(local_tree_nodes[root]) == self.network.nodes:
                num_trees += 1
        if num_trees != len(local_sorted_roots):
            print("Tree formation impossible")
        else:
            print("Tree formation successful")
            for root in local_sorted_roots:
                print("Tree " + str(root) + " height: " + str(highest_length[root]))
        return local_trees


    '''
    compute_trees() - computes allreduce spanning trees for the given network
    @kary: build kary-trees
    @alternate: Ture - allocate the links by alternating trees every allocation
                False - allocating links for one tree as much as possble
    @sort: Whether sort the trees for link allocation based on conflicts from
           last allocation iteration
    @verbose: print detailed info of tree construction process
    '''
    def compute_trees(self, kary, alternate=True, sort=False, verbose=False):
        # sort = False
        saved_treepath = '{}/src/SavedTrees_2/'.format(os.environ['SIMHOME'])
        saved_tree_name = saved_treepath + str(self.args.allreduce) + "_" + str(self.args.num_hmcs)
        if self.args.load_tree:
            save_object = pickle.load(open(saved_tree_name, 'rb'))
            self.trees = save_object['tree']
            self.timesteps = save_object['timesteps']
        else:
            starting_code_time = time.time()
            assert kary > 1

            trees = {}
            tree_nodes = {}
            for node in range(self.network.nodes):
                trees[node] = []
                tree_nodes[node] = [node]
                if verbose:
                    print('initialized tree {}: {}'.format(node, tree_nodes[node]))

            # tree construction
            global_timesteps = 0
            sorted_roots = [4, 8, 7]
            minimum_timesteps = 10000000000
            minimum_trees = None
            for iter in range(10):
                shuffled_sorted_roots = copy.deepcopy(sorted_roots)
                random.shuffle(shuffled_sorted_roots)
                temp_trees = self.compute_trees_from_timestep(copy.deepcopy(tree_nodes), shuffled_sorted_roots, copy.deepcopy(trees))
            # minimum_trees = copy.deepcopy(temp_trees)
            # minimum_timesteps = temp_timesteps

            # verify that there is no link conflicts
            # for root in range(self.network.nodes):
            #     for i in range(root + 1, self.network.nodes):
            #         intersection = set(self.trees[root]) & set(self.trees[i])
            #         if len(intersection) != 0:
            #             print('tree {} and tree {} have link conflicts {}'.format(root, i, intersection))
            #             print('tree {}: {}'.format(root, self.trees[root]))
            #             print('tree {}: {}'.format(i, self.trees[i]))
            #             exit()

            end_code_time = time.time()
            self.timesteps = minimum_timesteps
            self.trees = minimum_trees
            logger.info("Time difference " + str(end_code_time - starting_code_time))
            if verbose:
                print('Total timesteps for network size of {}: {}'.format(self.network.nodes, self.timesteps))
            save_object = {}
            save_object['tree'] = self.trees
            save_object['timesteps'] = self.timesteps
            pickle.dump(save_object, open(saved_tree_name, "wb"))

            '''
            1. Start from last timestep if current length is not equal to the optimal height.
            2. Take a link (child, parent, t)
            3. Find all the links which can connect child to different nodes. child_link_list = [(child, parent1), (child, parent2)]
            4. For each link in child_link_list, find all the trees which use that link at timestep t-1. 
            5. In those trees try to connect child using any of the remaining unused links of t-1 timestep.
            '''

    # def compute_trees(self, kary, alternate=False, sort=True, verbose=False)

    '''
    generate_schedule()
    @verbose: print the generated schedules

    desc - generate reduce_scatter_schedule and all_gather_schedule from trees
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
            for edge in self.trees[root]:
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
        for root in range(self.network.nodes):
            for edge in self.trees[root]:
                # reduce-scatter
                rs_child = edge[0]
                rs_parent = edge[1]
                rs_timestep = self.timesteps - edge[2] - 1

                # send from rs_child to rs_parent for tree root at rs_timestep
                if rs_timestep not in reduce_scatter_schedule[rs_child].keys():
                    reduce_scatter_schedule[rs_child][rs_timestep] = {}
                flow_children = [(root, child) for child in self.trees_children[root][rs_child]]
                reduce_scatter_schedule[rs_child][rs_timestep][root] = ((rs_parent, reduce_scatter_ni[rs_parent][rs_timestep]), flow_children, 1, rs_timestep)
                reduce_scatter_ni[rs_parent][rs_timestep] = (reduce_scatter_ni[rs_parent][rs_timestep] + 1) % self.args.radix

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
                        all_gather_schedule[ag_parent][ag_timestep][root] = ([], None, 1, self.timesteps + ag_timestep + 1)
                    else:
                        all_gather_schedule[ag_parent][ag_timestep][root] = ([], (root, self.trees_parent[root][ag_parent]), 1, ag_timestep + self.timesteps + 1)
                all_gather_schedule[ag_parent][ag_timestep][root][0].append((ag_child, all_gather_ni[ag_child][ag_timestep]))
                all_gather_ni[ag_child][ag_timestep] = (all_gather_ni[ag_child][ag_timestep] + 1) % self.args.radix

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
                            print('   - Reduce, FlowID {}, Parent {}, Children {}, Step {}'.format(flow, schedule[0][0], [ele[1] for ele in schedule[1]], timestep))

                for timestep in range(self.timesteps):
                    if self.all_gather_schedule[node][timestep] == None:
                        print('   - NoOp')
                    else:
                        for flow, schedule in self.all_gather_schedule[node][timestep].items():
                            if schedule[1] == None:
                                parent = 'nil'
                            else:
                                parent = schedule[1][1]
                            print('   - Gather, FlowID {}, Parent {}, Children {}, Step {}'.format(flow, parent, [ele[0] for ele in schedule[0]], self.timesteps + timestep))

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

    # def generate_schedule(self, verbose=False)

def test(args):
    network = construct_network(args)

    kary = args.kary
    allreduce = MultiTreeAllreduce(args, network)
    # NOTE: sorted doesn't help for multitree since it only considers available links
    allreduce.compute_trees(kary, alternate=True, sort=False, verbose=args.verbose)
    if args.gendotfile:
        allreduce.generate_trees_dotfile('multitree.dot')
    timesteps = allreduce.timesteps
    allreduce.generate_schedule(verbose=args.verbose)
    allreduce.compute_trees(kary, alternate=True, sort=True, verbose=args.verbose)
    if args.gendotfile:
        allreduce.generate_trees_dotfile('multitree_sort.dot')
        #allreduce.generate_per_tree_dotfile('multitreedot')
    sort_timesteps = allreduce.timesteps
    allreduce.generate_schedule()
    #allreduce.max_num_concurrent_flows()
    if timesteps > sort_timesteps:
        compare = 'Better'
    elif timesteps == sort_timesteps:
        compare = 'Same'
    else:
        compare = 'Worse'
    print('MultiTreeAllreduce takes {} timesteps (no sort), and {} timesteps (sort), {}'.format(
        timesteps, sort_timesteps, compare))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--num-hmcs', default=32, type=int,
                        help='number of nodes, default is 32')
    parser.add_argument('--kary', default=2, type=int,
                        help='generay kary tree, default is 2 (binary)')
    parser.add_argument('--radix', default=4, type=int,
                        help='node radix, default is 4')
    parser.add_argument('--gendotfile', default=False, action='store_true',
                        help='generate tree dotfiles, default is False')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='detailed print')
    parser.add_argument('--bigraph-m', default=4, type=int,
                        help='logical groups size (# sub-node per switch')
    parser.add_argument('--bigraph-n', default=8, type=int,
                        help='# switches')
    parser.add_argument('--booksim-network', default='bigraph',
                        help='network topology (torus | mesh | bigraph), default is torus')

    args = parser.parse_args()

    test(args)
