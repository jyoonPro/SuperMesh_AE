import argparse
import copy

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


class HeterogeneousOptimalMultiTreeAllreduce(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)
        self.mesh = False
        if args.booksim_network == 'hetero_mesh':
            self.mesh = True
            for topology in self.args.topology_in_dimension:
                if topology != 'Ring':
                    raise RuntimeError('Error: For mesh, all dimension topology should be Ring')

    def next_possible_free_time(self, child, parent, reserved_links, cur_time):
        while (child, parent, cur_time) in reserved_links:
            cur_time += 1
        return cur_time

    def next_possible_free_time_for_switch(self, child, parent, switch, reserved_node_to_switch,
                                           reserved_switch_to_node, cur_time):
        while ((parent, switch, cur_time) in reserved_node_to_switch) or (
                (switch, child, cur_time) in reserved_switch_to_node):
            cur_time += 1
        return cur_time

    def check_in_reserved_links(self, child, parent, reserved_links, cur_time):
        if (child, parent, cur_time) in reserved_links:
            return True
        else:
            return False

    def get_unutilized_links(self, d):
        unutilized_links = 0
        for n in range(self.network.nodes):
            unutilized_links += len(d[n])
        return unutilized_links

    def get_first_dimension_nodes(self, node):
        nodes_in_first_dim = self.args.nodes_in_dimension[0]
        row_index = node // nodes_in_first_dim
        row_start_index = row_index * nodes_in_first_dim
        node_list = []
        for i in range(nodes_in_first_dim):
            node_list.append(row_start_index + i)
        return node_list

    def get_second_dimension_nodes(self, node):
        nodes_in_first_dim = self.args.nodes_in_dimension[0]
        nodes_in_second_dim = self.args.nodes_in_dimension[1]
        col_index = node % nodes_in_first_dim
        offset = 0
        if self.args.total_dimensions > 2:
            offset = (node // (nodes_in_first_dim * nodes_in_second_dim)) * (nodes_in_first_dim * nodes_in_second_dim)
        node_list = []
        for i in range(nodes_in_second_dim):
            node_list.append(offset + nodes_in_first_dim * i + col_index)
        return node_list

    def get_third_dimension_nodes(self, node):
        nodes_in_first_dim = self.args.nodes_in_dimension[0]
        nodes_in_second_dim = self.args.nodes_in_dimension[1]
        nodes_in_third_dim = self.args.nodes_in_dimension[2]
        col_index = node % (nodes_in_first_dim * nodes_in_second_dim)
        offset = 0
        if self.args.total_dimensions > 3:
            offset = (node // (nodes_in_first_dim * nodes_in_second_dim * nodes_in_third_dim)) * (
                        nodes_in_first_dim * nodes_in_second_dim * nodes_in_third_dim)
        node_list = []
        for i in range(nodes_in_third_dim):
            node_list.append(offset + (nodes_in_first_dim * nodes_in_second_dim) * i + col_index)
        return node_list

    def get_fourth_dimension_nodes(self, node):
        nodes_in_first_dim = self.args.nodes_in_dimension[0]
        nodes_in_second_dim = self.args.nodes_in_dimension[1]
        nodes_in_third_dim = self.args.nodes_in_dimension[2]
        nodes_in_fourth_dim = self.args.nodes_in_dimension[3]
        col_index = node % (nodes_in_first_dim * nodes_in_second_dim * nodes_in_third_dim)
        node_list = []
        for i in range(nodes_in_fourth_dim):
            node_list.append((nodes_in_first_dim * nodes_in_second_dim * nodes_in_third_dim) * i + col_index)
        return node_list

    def get_dimension_nodes(self, node, d):
        if d == 0:
            return self.get_first_dimension_nodes(node)
        elif d == 1:
            return self.get_second_dimension_nodes(node)
        elif d == 2:
            return self.get_third_dimension_nodes(node)
        elif d == 3:
            return self.get_fourth_dimension_nodes(node)
        else:
            raise RuntimeError('Error: Dimension {} is not supported yet'.format(d))

    def get_immediate_next_node(self, node, d):
        if d == 0:
            dimension_nodes = self.get_first_dimension_nodes(node)
        elif d == 1:
            dimension_nodes = self.get_second_dimension_nodes(node)
        elif d == 2:
            dimension_nodes = self.get_third_dimension_nodes(node)
        elif d == 3:
            dimension_nodes = self.get_fourth_dimension_nodes(node)
        else:
            raise RuntimeError('Error: Dimension {} is not supported yet'.format(d))
        node_index = dimension_nodes.index(node)
        if node_index == 0:
            if self.mesh:
                return dimension_nodes[1], None
            else:
                return dimension_nodes[1], dimension_nodes[-1]
        if node_index == len(dimension_nodes) - 1:
            if self.mesh:
                return None, dimension_nodes[node_index - 1]
            else:
                return dimension_nodes[0], dimension_nodes[node_index - 1]
        else:
            return dimension_nodes[node_index + 1], dimension_nodes[node_index - 1]


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
        if self.args.load_tree:
            save_object = pickle.load(open(self.args.saved_tree_name, 'rb'))
            self.trees = save_object['tree']
            self.timesteps = save_object['timesteps']

            link_reservation_checker_node = {}
            link_reservation_checker_switch_to_node = {}
            link_reservation_checker_node_to_switch = {}
            for i in range(self.timesteps):
                link_reservation_checker_node[i] = copy.deepcopy(self.network.hiererchical_connection)
                link_reservation_checker_switch_to_node[i] = copy.deepcopy(self.network.switch_connections_to_node)
                link_reservation_checker_node_to_switch[i] = copy.deepcopy(self.network.node_connections_to_switch)

            for node in range(self.network.nodes):
                edges = self.trees[node]
                for edge in edges:
                    child = edge[0]
                    parent = edge[1]
                    start_time = edge[2]
                    distance = edge[3]
                    neighbor_switch = edge[4]
                    # print(str(node) + " " + str(child) + " " + str(parent) + " " + str(start_time) + " " + str(distance))
                    # print(neighbor_switch)
                    # print("Neighbor switch")
                    for i in range(distance):
                        # print(i)
                        if neighbor_switch is None:
                            link_reservation_checker_node[start_time + i][parent].remove(child)
                        else:
                            link_reservation_checker_node_to_switch[start_time + i][parent].remove(neighbor_switch)
                            print("Removed " + str(neighbor_switch) + " from node " + str(
                                parent) + " at timestamp " + str(start_time + i))
                            link_reservation_checker_switch_to_node[start_time + i][neighbor_switch].remove(child)

            logger.info("There is no conflict")
            logger.info("Total possible links " + str(self.network.total_possible_links))
            for i in range(self.timesteps):
                logger.info("Unutilized link at timestep " + str(i) + " is " + str(
                    self.get_unutilized_links(link_reservation_checker_node[i])))

        else:
            starting_code_time = time.time()
            assert kary > 1

            # initialize empty trees
            self.trees = {}
            leaves = {}
            already_included = {}
            topology = {}
            node_to_node = deepcopy(self.network.node_to_node)
            for key in node_to_node:
                topology[key] = node_to_node[key]

            self.timesteps = 0
            leaves_activation_time = {}
            trees = {}

            latency_dim_list = []
            for idx, x in enumerate(self.args.latency_multiplier):
                latency_dim_list.append((x, idx))
            latency_dim_list = sorted(latency_dim_list)
            sorted_dim = []
            for latency_dim in latency_dim_list:
                sorted_dim.append(latency_dim[1])
            reserved_links = []
            reserved_node_to_switch = []
            reserved_switch_to_node = []
            current_max_timestep = 0

            for node in range(self.network.nodes):
                trees[node] = []
                leaves[node] = [node]
                already_included[node] = [node]
                leaves_activation_time[node] = {}
                leaves_activation_time[node][node] = 0
                second_dimension_nodes = []

                if self.args.topology_in_dimension_list == "Ring_Ring_Ring":
                    dim = 2
                    node_queue = []
                    node_queue.append(node)
                    while len(node_queue) > 0:
                        leaf = node_queue.pop(0)
                        next_node, prev_node = self.get_immediate_next_node(leaf, dim)
                        if next_node is not None and next_node not in already_included[node]:
                            leaves[node].append(next_node)
                            already_included[node].append(next_node)
                            leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                      self.args.latency_multiplier[dim]
                            trees[node].append((next_node, leaf, leaves_activation_time[node][leaf],
                                                self.args.latency_multiplier[dim], None))
                            if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[
                                dim]:
                                current_max_timestep = leaves_activation_time[node][leaf] + \
                                                       self.args.latency_multiplier[dim]
                            node_queue.append(next_node)
                            for d in range(self.args.latency_multiplier[dim]):
                                reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + d))
                            # if self.args.total_dimensions == 3 and dim == sorted_dim[2]:
                            if not self.mesh:
                                second_dimension_nodes.append(next_node)

                        if prev_node is not None and prev_node not in already_included[node]:
                            leaves[node].append(prev_node)
                            already_included[node].append(prev_node)
                            leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                      self.args.latency_multiplier[dim]
                            trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf],
                                                self.args.latency_multiplier[dim], None))
                            node_queue.append(prev_node)
                            if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[
                                dim]:
                                current_max_timestep = leaves_activation_time[node][leaf] + \
                                                       self.args.latency_multiplier[dim]
                            for d in range(self.args.latency_multiplier[dim]):
                                reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + d))
                            # if self.args.total_dimensions == 3 and dim == sorted_dim[2]:
                            if not self.mesh:
                                second_dimension_nodes.append(prev_node)
                    # for dim in range(self.args.total_dimensions):
                    dim = 1
                    next_step_time = 0
                    node_queue = []
                    node_queue.append(node)
                    while len(node_queue) > 0:
                        leaf = node_queue.pop(0)
                        next_node, prev_node = self.get_immediate_next_node(leaf, dim)
                        if next_node is not None and next_node not in already_included[node]:
                            leaves[node].append(next_node)
                            already_included[node].append(next_node)
                            leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                      self.args.latency_multiplier[dim]
                            trees[node].append((next_node, leaf, leaves_activation_time[node][leaf],
                                                self.args.latency_multiplier[dim], None))
                            if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[
                                dim]:
                                current_max_timestep = leaves_activation_time[node][leaf] + \
                                                       self.args.latency_multiplier[dim]
                            if next_step_time < leaves_activation_time[node][leaf] + self.args.latency_multiplier[dim]:
                                next_step_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[dim]
                            node_queue.append(next_node)
                            for d in range(self.args.latency_multiplier[dim]):
                                reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + d))

                        if prev_node is not None and prev_node not in already_included[node]:
                            leaves[node].append(prev_node)
                            already_included[node].append(prev_node)
                            leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                      self.args.latency_multiplier[dim]
                            trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf],
                                                self.args.latency_multiplier[dim], None))
                            node_queue.append(prev_node)
                            if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[
                                dim]:
                                current_max_timestep = leaves_activation_time[node][leaf] + \
                                                       self.args.latency_multiplier[dim]
                            if next_step_time < leaves_activation_time[node][leaf] + self.args.latency_multiplier[dim]:
                                next_step_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[dim]
                            for d in range(self.args.latency_multiplier[dim]):
                                reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + d))
                    if len(second_dimension_nodes) > 0:
                        initial_time = leaves_activation_time[node][second_dimension_nodes[0]]
                        added_in_node_queue_down = 0
                        added_in_node_queue_up = 0
                        added_in_node_queue_average = 0
                        while len(second_dimension_nodes) > 0:
                            prev_step_time = next_step_time
                            node_queue_down = []
                            node_queue_up = []
                            node_queue_average = []
                            # tracked_node = None
                            if len(second_dimension_nodes) > 1:
                                node_queue_down.append(second_dimension_nodes.pop(0))
                                added_in_node_queue_down += 1
                                node_queue_up.append(second_dimension_nodes.pop(0))
                                added_in_node_queue_up += 1
                                tracked_node = node_queue_down[0]
                            else:
                                node_queue_average.append(second_dimension_nodes.pop(0))
                                added_in_node_queue_average += 1
                                tracked_node = node_queue_average[0]
                                # node_queue_down.append(second_dimension_nodes.pop(0))
                                # added_in_node_queue_down += 1
                                # tracked_node = node_queue_down[0]
                            time_diff = prev_step_time - leaves_activation_time[node][tracked_node]
                            while len(node_queue_down) > 0:
                                leaf = node_queue_down.pop(0)
                                next_node, prev_node = self.get_immediate_next_node(leaf, sorted_dim[1])
                                if next_node is not None and next_node not in already_included[node]:
                                    leaves[node].append(next_node)
                                    already_included[node].append(next_node)
                                    if added_in_node_queue_down > 0:
                                        leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]] + time_diff
                                        trees[node].append((next_node, leaf,
                                                            leaves_activation_time[node][leaf] + time_diff,
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        node_queue_down.append(next_node)
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[
                                                                       sorted_dim[1]] + time_diff
                                        if next_step_time < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[dim]:
                                            next_step_time = leaves_activation_time[node][leaf] + \
                                                             self.args.latency_multiplier[dim]
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (next_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                                        initial_time = leaves_activation_time[node][leaf] + \
                                                       self.args.latency_multiplier[sorted_dim[1]] + time_diff
                                        added_in_node_queue_down -= 1
                                    else:
                                        leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]]
                                        trees[node].append((next_node, leaf, leaves_activation_time[node][leaf],
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        node_queue_down.append(next_node)
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]]:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[sorted_dim[1]]
                                        if next_step_time < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[dim]:
                                            next_step_time = leaves_activation_time[node][leaf] + \
                                                             self.args.latency_multiplier[dim]
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (next_node, leaf, leaves_activation_time[node][leaf] + d))
                                        initial_time = leaves_activation_time[node][leaf] + \
                                                       self.args.latency_multiplier[sorted_dim[1]]

                            while len(node_queue_up) > 0:
                                leaf = node_queue_up.pop(0)
                                next_node, prev_node = self.get_immediate_next_node(leaf, sorted_dim[1])
                                if prev_node not in already_included[node]:
                                    leaves[node].append(prev_node)
                                    already_included[node].append(prev_node)
                                    if added_in_node_queue_up > 0:
                                        leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]] + time_diff
                                        trees[node].append((prev_node, leaf,
                                                            leaves_activation_time[node][leaf] + time_diff,
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[
                                                                       sorted_dim[1]] + time_diff
                                        # if next_step_time < leaves_activation_time[node][leaf] + \
                                        #         self.args.latency_multiplier[dim]:
                                        #     next_step_time = leaves_activation_time[node][leaf] + \
                                        #                      self.args.latency_multiplier[dim]
                                        node_queue_up.append(prev_node)
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (prev_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                                        # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                                        added_in_node_queue_up -= 1
                                    else:
                                        leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]]
                                        trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf],
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]]:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[sorted_dim[1]]
                                        # if next_step_time < leaves_activation_time[node][leaf] + \
                                        #         self.args.latency_multiplier[dim]:
                                        #     next_step_time = leaves_activation_time[node][leaf] + \
                                        #                      self.args.latency_multiplier[dim]
                                        node_queue_up.append(prev_node)
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (prev_node, leaf, leaves_activation_time[node][leaf] + d))
                                        # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]

                            while len(node_queue_average) > 0:
                                leaf = node_queue_average.pop(0)
                                next_node, prev_node = self.get_immediate_next_node(leaf, sorted_dim[1])
                                if prev_node not in already_included[node]:
                                    leaves[node].append(prev_node)
                                    already_included[node].append(prev_node)
                                    if added_in_node_queue_average > 0:
                                        leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]] + time_diff
                                        trees[node].append((prev_node, leaf,
                                                            leaves_activation_time[node][leaf] + time_diff,
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        node_queue_average.append(prev_node)
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[
                                                                       sorted_dim[1]] + time_diff
                                        # if next_step_time < leaves_activation_time[node][leaf] + \
                                        #         self.args.latency_multiplier[dim]:
                                        #     next_step_time = leaves_activation_time[node][leaf] + \
                                        #                      self.args.latency_multiplier[dim]
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (prev_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                                        # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                                        # added_in_node_queue_average -= 1
                                    else:
                                        leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]]
                                        trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf],
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        node_queue_average.append(prev_node)
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]]:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[sorted_dim[1]]
                                        # if next_step_time < leaves_activation_time[node][leaf] + \
                                        #         self.args.latency_multiplier[dim]:
                                        #     next_step_time = leaves_activation_time[node][leaf] + \
                                        #                      self.args.latency_multiplier[dim]
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (prev_node, leaf, leaves_activation_time[node][leaf] + d))
                                if next_node not in already_included[node]:
                                    leaves[node].append(next_node)
                                    already_included[node].append(next_node)
                                    if added_in_node_queue_average > 0:
                                        leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]] + time_diff
                                        trees[node].append((next_node, leaf,
                                                            leaves_activation_time[node][leaf] + time_diff,
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        node_queue_average.append(next_node)
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[
                                                                       sorted_dim[1]] + time_diff
                                        # if next_step_time < leaves_activation_time[node][leaf] + \
                                        #         self.args.latency_multiplier[dim]:
                                        #     next_step_time = leaves_activation_time[node][leaf] + \
                                        #                      self.args.latency_multiplier[dim]
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (next_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                                        # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                                        # added_in_node_queue_average -= 1
                                    else:
                                        leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                                  self.args.latency_multiplier[
                                                                                      sorted_dim[1]]
                                        trees[node].append((next_node, leaf, leaves_activation_time[node][leaf],
                                                            self.args.latency_multiplier[sorted_dim[1]], None))
                                        node_queue_average.append(next_node)
                                        if current_max_timestep < leaves_activation_time[node][leaf] + \
                                                self.args.latency_multiplier[sorted_dim[1]]:
                                            current_max_timestep = leaves_activation_time[node][leaf] + \
                                                                   self.args.latency_multiplier[sorted_dim[1]]
                                        # if next_step_time < leaves_activation_time[node][leaf] + \
                                        #         self.args.latency_multiplier[dim]:
                                        #     next_step_time = leaves_activation_time[node][leaf] + \
                                        #                      self.args.latency_multiplier[dim]
                                        for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                                            reserved_links.append(
                                                (next_node, leaf, leaves_activation_time[node][leaf] + d))
                                added_in_node_queue_average -= 1
                elif self.args.topology_in_dimension_list == "Ring_Ring":
                    for dim in range(self.args.total_dimensions):
                        node_queue = []
                        node_queue.append(node)
                        while len(node_queue) > 0:
                            leaf = node_queue.pop(0)
                            next_node, prev_node = self.get_immediate_next_node(leaf, dim)
                            if next_node is not None and next_node not in already_included[node]:
                                leaves[node].append(next_node)
                                already_included[node].append(next_node)
                                leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                          self.args.latency_multiplier[dim]
                                trees[node].append((next_node, leaf, leaves_activation_time[node][leaf],
                                                    self.args.latency_multiplier[dim], None))
                                if current_max_timestep < leaves_activation_time[node][leaf] + \
                                        self.args.latency_multiplier[dim]:
                                    current_max_timestep = leaves_activation_time[node][leaf] + \
                                                           self.args.latency_multiplier[dim]
                                node_queue.append(next_node)
                                for d in range(self.args.latency_multiplier[dim]):
                                    reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + d))
                                # if self.args.total_dimensions == 3 and dim == sorted_dim[2]:
                                #     second_dimension_nodes.append(next_node)

                            if prev_node is not None and prev_node not in already_included[node]:
                                leaves[node].append(prev_node)
                                already_included[node].append(prev_node)
                                leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                          self.args.latency_multiplier[dim]
                                trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf],
                                                    self.args.latency_multiplier[dim], None))
                                node_queue.append(prev_node)
                                if current_max_timestep < leaves_activation_time[node][leaf] + \
                                        self.args.latency_multiplier[dim]:
                                    current_max_timestep = leaves_activation_time[node][leaf] + \
                                                           self.args.latency_multiplier[dim]
                                for d in range(self.args.latency_multiplier[dim]):
                                    reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + d))
                                # if self.args.total_dimensions == 3 and dim == sorted_dim[2]:
                                #     second_dimension_nodes.append(prev_node)
                    # if len(second_dimension_nodes) > 0:
                    #     initial_time = leaves_activation_time[node][second_dimension_nodes[0]]
                    #     added_in_node_queue_down = 0
                    #     added_in_node_queue_up = 0
                    #     added_in_node_queue_average = 0
                    #     while len(second_dimension_nodes) > 0:
                    #         node_queue_down = []
                    #         node_queue_up = []
                    #         node_queue_average = []
                    #         # tracked_node = None
                    #         if len(second_dimension_nodes) > 1:
                    #             node_queue_down.append(second_dimension_nodes.pop(0))
                    #             added_in_node_queue_down += 1
                    #             node_queue_up.append(second_dimension_nodes.pop(0))
                    #             added_in_node_queue_up += 1
                    #             tracked_node = node_queue_down[0]
                    #         else:
                    #             node_queue_average.append(second_dimension_nodes.pop(0))
                    #             added_in_node_queue_average += 1
                    #             tracked_node = node_queue_average[0]
                    #             # node_queue_down.append(second_dimension_nodes.pop(0))
                    #             # added_in_node_queue_down += 1
                    #             # tracked_node = node_queue_down[0]
                    #         time_diff = initial_time - leaves_activation_time[node][tracked_node]
                    #         while len(node_queue_down) > 0:
                    #             leaf = node_queue_down.pop(0)
                    #             next_node, prev_node = self.get_immediate_next_node(leaf, sorted_dim[1])
                    #             if next_node not in already_included[node]:
                    #                 leaves[node].append(next_node)
                    #                 already_included[node].append(next_node)
                    #                 if added_in_node_queue_down > 0:
                    #                     leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     trees[node].append((next_node, leaf, leaves_activation_time[node][leaf] + time_diff, self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     node_queue_down.append(next_node)
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                    #                     initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     added_in_node_queue_down -= 1
                    #                 else:
                    #                     leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     trees[node].append((next_node, leaf, leaves_activation_time[node][leaf], self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     node_queue_down.append(next_node)
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + d))
                    #                     initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #
                    #         while len(node_queue_up) > 0:
                    #             leaf = node_queue_up.pop(0)
                    #             next_node, prev_node = self.get_immediate_next_node(leaf, sorted_dim[1])
                    #             if prev_node not in already_included[node]:
                    #                 leaves[node].append(prev_node)
                    #                 already_included[node].append(prev_node)
                    #                 if added_in_node_queue_up > 0:
                    #                     leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf] + time_diff, self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     node_queue_up.append(prev_node)
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                    #                     # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     added_in_node_queue_up -= 1
                    #                 else:
                    #                     leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf], self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     node_queue_up.append(prev_node)
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + d))
                    #                     # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #
                    #         while len(node_queue_average) > 0:
                    #             leaf = node_queue_average.pop(0)
                    #             next_node, prev_node = self.get_immediate_next_node(leaf, sorted_dim[1])
                    #             if prev_node not in already_included[node]:
                    #                 leaves[node].append(prev_node)
                    #                 already_included[node].append(prev_node)
                    #                 if added_in_node_queue_average > 0:
                    #                     leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf] + time_diff, self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     node_queue_average.append(prev_node)
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                    #                     # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     # added_in_node_queue_average -= 1
                    #                 else:
                    #                     leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf], self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     node_queue_average.append(prev_node)
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + d))
                    #             if next_node not in already_included[node]:
                    #                 leaves[node].append(next_node)
                    #                 already_included[node].append(next_node)
                    #                 if added_in_node_queue_average > 0:
                    #                     leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     trees[node].append((next_node, leaf, leaves_activation_time[node][leaf] + time_diff, self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     node_queue_average.append(next_node)
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + time_diff + d))
                    #                     # initial_time = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]] + time_diff
                    #                     # added_in_node_queue_average -= 1
                    #                 else:
                    #                     leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     trees[node].append((next_node, leaf, leaves_activation_time[node][leaf], self.args.latency_multiplier[sorted_dim[1]], None))
                    #                     node_queue_average.append(next_node)
                    #                     if current_max_timestep < leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]:
                    #                         current_max_timestep = leaves_activation_time[node][leaf] + self.args.latency_multiplier[sorted_dim[1]]
                    #                     for d in range(self.args.latency_multiplier[sorted_dim[1]]):
                    #                         reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + d))
                    #             added_in_node_queue_average -= 1
                else:
                    node_queue = []
                    node_queue.append(node)
                    dim = self.args.total_dimensions - 1
                    last_dim_topology = self.args.topology_in_dimension[-1]
                    while len(node_queue) > 0:
                        leaf = node_queue.pop(0)
                        if last_dim_topology == 'Ring' or last_dim_topology == 'SW':
                            next_node, prev_node = self.get_immediate_next_node(leaf, dim)
                            if next_node is not None and next_node not in already_included[node]:
                                neighbor_switch = None
                                if last_dim_topology == 'SW':
                                    for child in topology[leaf]:
                                        if child[0] == next_node:
                                            neighbor_switch = child[4]
                                leaves[node].append(next_node)
                                already_included[node].append(next_node)
                                leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                          self.args.latency_multiplier[dim]
                                trees[node].append((next_node, leaf, leaves_activation_time[node][leaf],
                                                    self.args.latency_multiplier[dim], neighbor_switch))
                                if current_max_timestep < leaves_activation_time[node][leaf] + \
                                        self.args.latency_multiplier[dim]:
                                    current_max_timestep = leaves_activation_time[node][leaf] + \
                                                           self.args.latency_multiplier[dim]
                                node_queue.append(next_node)
                                for d in range(self.args.latency_multiplier[dim]):
                                    reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + d))
                                    if last_dim_topology == 'SW':
                                        reserved_node_to_switch.append(
                                            (leaf, neighbor_switch, leaves_activation_time[node][leaf] + d))
                                        reserved_switch_to_node.append(
                                            (neighbor_switch, next_node, leaves_activation_time[node][leaf] + d))

                            if last_dim_topology == 'Ring':
                                if prev_node is not None and prev_node not in already_included[node]:
                                    leaves[node].append(prev_node)
                                    already_included[node].append(prev_node)
                                    leaves_activation_time[node][prev_node] = leaves_activation_time[node][leaf] + \
                                                                              self.args.latency_multiplier[dim]
                                    trees[node].append((prev_node, leaf, leaves_activation_time[node][leaf],
                                                        self.args.latency_multiplier[dim], None))
                                    if current_max_timestep < leaves_activation_time[node][leaf] + \
                                            self.args.latency_multiplier[dim]:
                                        current_max_timestep = leaves_activation_time[node][leaf] + \
                                                               self.args.latency_multiplier[dim]
                                    node_queue.append(prev_node)
                                    for d in range(self.args.latency_multiplier[dim]):
                                        reserved_links.append((prev_node, leaf, leaves_activation_time[node][leaf] + d))
                        else:
                            last_dimension_nodes = self.get_dimension_nodes(leaf, dim)
                            for next_node in last_dimension_nodes:
                                if next_node not in already_included[node]:
                                    leaves[node].append(next_node)
                                    already_included[node].append(next_node)
                                    leaves_activation_time[node][next_node] = leaves_activation_time[node][leaf] + \
                                                                              self.args.latency_multiplier[dim]
                                    trees[node].append((next_node, leaf, leaves_activation_time[node][leaf],
                                                        self.args.latency_multiplier[dim], None))
                                    if current_max_timestep < leaves_activation_time[node][leaf] + \
                                            self.args.latency_multiplier[dim]:
                                        current_max_timestep = leaves_activation_time[node][leaf] + \
                                                               self.args.latency_multiplier[dim]
                                    for d in range(self.args.latency_multiplier[dim]):
                                        reserved_links.append((next_node, leaf, leaves_activation_time[node][leaf] + d))

            # self.timesteps = current_max_timestep
            #
            # link_reservation_checker_node = {}
            # link_reservation_checker_switch_to_node = {}
            # link_reservation_checker_node_to_switch = {}
            # for i in range(self.timesteps):
            #     link_reservation_checker_node[i] = copy.deepcopy(self.network.hiererchical_connection)
            #     link_reservation_checker_switch_to_node[i] = copy.deepcopy(self.network.switch_connections_to_node)
            #     link_reservation_checker_node_to_switch[i] = copy.deepcopy(self.network.node_connections_to_switch)
            #
            # for node in range(self.network.nodes):
            #     edges = trees[node]
            #     for edge in edges:
            #         child = edge[0]
            #         parent = edge[1]
            #         start_time = edge[2]
            #         distance = edge[3]
            #         neighbor_switch = edge[4]
            #         print(
            #             str(node) + " " + str(child) + " " + str(parent) + " " + str(start_time) + " " + str(distance))
            #         # print(neighbor_switch)
            #         # print("Neighbor switch")
            #         for i in range(distance):
            #             # print(i)
            #             if neighbor_switch is None:
            #                 link_reservation_checker_node[start_time + i][parent].remove(child)
            #             else:
            #                 link_reservation_checker_node_to_switch[start_time + i][parent].remove(neighbor_switch)
            #                 print("Removed " + str(neighbor_switch) + " from node " + str(
            #                     parent) + " at timestamp " + str(start_time + i))
            #                 link_reservation_checker_switch_to_node[start_time + i][neighbor_switch].remove(child)

            self.timesteps = 0
            total_timesteps = 0
            possible_links = []
            num_trees = 0
            while num_trees < self.network.nodes:
                while True:
                    added_in_full_cycle = False
                    for root_idx in range(self.network.nodes):
                        current_tree_leaves = copy.deepcopy(leaves[root_idx])  # list of current leaves in that tree
                        for leaf in current_tree_leaves:
                            if total_timesteps < leaves_activation_time[root_idx][leaf]:
                                continue
                            for child in topology[leaf]:
                                if child[3] == 'Ring' or child[3] == 'FC':
                                    if child[0] not in already_included[
                                        root_idx] and not self.check_inside_possible_links(child[0], leaf, root_idx,
                                                                                           possible_links):
                                        # if self.args.topology_in_dimension_list == "Ring_Ring" or self.args.topology_in_dimension_list == "Ring_Ring_Ring" :
                                        adding_time = self.next_possible_free_time(child[0], leaf, reserved_links,
                                                                                   total_timesteps)
                                        # else:
                                        #     adding_time = total_timesteps
                                        possible_links.append((child[0], leaf, root_idx, adding_time,
                                                               adding_time + child[1], child[1], child[2],
                                                               child[3], child[4]))
                                        added_in_full_cycle = True

                            for d in range(self.args.total_dimensions):
                                if self.args.topology_in_dimension[d] == 'SW':
                                    next_node, prev_node = self.get_immediate_next_node(leaf, d)
                                    if next_node not in already_included[
                                        root_idx] and not self.check_inside_possible_links(next_node, leaf, root_idx,
                                                                                           possible_links):
                                        for child in topology[leaf]:
                                            if child[0] == next_node:
                                                adding_time = self.next_possible_free_time_for_switch(child[0], leaf,
                                                                                                      child[4],
                                                                                                      reserved_node_to_switch,
                                                                                                      reserved_switch_to_node,
                                                                                                      total_timesteps)
                                                possible_links.append((child[0], leaf, root_idx, adding_time,
                                                                       adding_time + child[1], child[1], child[2],
                                                                       child[3], child[4]))
                                                added_in_full_cycle = True
                                    if prev_node not in already_included[
                                        root_idx] and not self.check_inside_possible_links(prev_node, leaf, root_idx,
                                                                                           possible_links):
                                        for child in topology[leaf]:
                                            if child[0] == prev_node:
                                                adding_time = self.next_possible_free_time_for_switch(child[0], leaf,
                                                                                                      child[4],
                                                                                                      reserved_node_to_switch,
                                                                                                      reserved_switch_to_node,
                                                                                                      total_timesteps)
                                                possible_links.append((child[0], leaf, root_idx, adding_time,
                                                                       adding_time + child[1], child[1], child[2],
                                                                       child[3], child[4]))
                                                added_in_full_cycle = True

                            leaves[root_idx].remove(leaf)

                    if not added_in_full_cycle:
                        break
                total_timesteps += 1
                print(total_timesteps)

                added_in_tree = True
                while added_in_tree:
                    added_in_tree = False
                    for root_idx in range(self.network.nodes):
                        child = None
                        parent = None
                        tree_idx = None
                        start_time = None
                        end_time = None
                        distance = None
                        dim = None
                        topology_type = None
                        neighbor_switch = None
                        target_link = None
                        for link in possible_links:
                            if link[4] == total_timesteps and link[2] == root_idx:
                                child = link[0]
                                parent = link[1]
                                tree_idx = link[2]
                                start_time = link[3]
                                end_time = link[4]
                                distance = link[5]
                                dim = link[6]
                                topology_type = link[7]
                                neighbor_switch = link[8]
                                target_link = link
                                break
                        if child is not None and parent is not None:
                            added_in_tree = True
                            possible_links.remove(target_link)
                            removable_links = []
                            for link in possible_links:
                                if link[0] == child and link[2] == tree_idx:
                                    removable_links.append(link)
                            for link in removable_links:
                                possible_links.remove(link)
                            new_possible_links = []
                            for link in possible_links:
                                if child == link[0] and parent == link[1] and link[3] < total_timesteps:
                                    if self.args.topology_in_dimension_list == "Ring_Ring" or self.args.topology_in_dimension_list == "Ring_Ring_Ring":
                                        adding_time = self.next_possible_free_time(link[0], link[1], reserved_links,
                                                                                   total_timesteps)
                                    else:
                                        adding_time = total_timesteps
                                    new_possible_links.append(
                                        (
                                        link[0], link[1], link[2], adding_time, adding_time + link[5], link[5], link[6],
                                        link[7], link[8]))
                                elif topology_type == 'SW':
                                    if (link[1] == parent and link[3] >= start_time and link[6] == dim) or (
                                            link[0] == child and link[3] >= start_time and link[6] == dim):
                                        new_possible_links.append(
                                            (link[0], link[1], link[2], total_timesteps, total_timesteps + link[5],
                                             link[5],
                                             link[6], link[7], link[8]))
                                    else:
                                        new_possible_links.append(link)
                                else:
                                    new_possible_links.append(link)
                            possible_links = copy.deepcopy(new_possible_links)
                            leaves[tree_idx].append(child)
                            already_included[tree_idx].append(child)
                            leaves_activation_time[tree_idx][child] = total_timesteps
                            trees[tree_idx].append((child, parent, start_time, distance, neighbor_switch))
                num_trees = 0
                for root_idx in range(self.network.nodes):
                    if len(already_included[root_idx]) == self.network.nodes:
                        num_trees += 1
                # print(possible_links)
            self.trees = copy.deepcopy(trees)
            self.timesteps = total_timesteps
            if self.timesteps < current_max_timestep:
                self.timesteps = current_max_timestep

            link_reservation_checker_node = {}
            link_reservation_checker_switch_to_node = {}
            link_reservation_checker_node_to_switch = {}
            for i in range(self.timesteps):
                link_reservation_checker_node[i] = copy.deepcopy(self.network.hiererchical_connection)
                link_reservation_checker_switch_to_node[i] = copy.deepcopy(self.network.switch_connections_to_node)
                link_reservation_checker_node_to_switch[i] = copy.deepcopy(self.network.node_connections_to_switch)

            for node in range(self.network.nodes):
                edges = self.trees[node]
                for edge in edges:
                    child = edge[0]
                    parent = edge[1]
                    start_time = edge[2]
                    distance = edge[3]
                    neighbor_switch = edge[4]
                    # print(str(node) + " " + str(child) + " " + str(parent) + " " + str(start_time) + " " + str(distance))
                    # print(neighbor_switch)
                    # print("Neighbor switch")
                    for i in range(distance):
                        # print(i)
                        if neighbor_switch is None:
                            link_reservation_checker_node[start_time + i][parent].remove(child)
                        else:
                            link_reservation_checker_node_to_switch[start_time + i][parent].remove(neighbor_switch)
                            print("Removed " + str(neighbor_switch) + " from node " + str(
                                parent) + " at timestamp " + str(start_time + i))
                            link_reservation_checker_switch_to_node[start_time + i][neighbor_switch].remove(child)

            logger.info("There is no conflict")
            logger.info("Total possible links " + str(self.network.total_possible_links))
            for i in range(self.timesteps):
                logger.info("Unutilized link at timestep " + str(i) + " is " + str(
                    self.get_unutilized_links(link_reservation_checker_node[i])))

            end_code_time = time.time()
            logger.info("Time difference " + str(end_code_time - starting_code_time))
            print('Total timesteps for network size of {}: {}'.format(self.network.nodes, self.timesteps))
            save_object = {}
            save_object['tree'] = self.trees
            save_object['timesteps'] = self.timesteps
            if self.args.save_object:
                save_object['hiererchical_connection'] = self.network.hiererchical_connection
                save_object['switch_connections_to_node'] = self.network.switch_connections_to_node
                save_object['node_connections_to_switch'] = self.network.node_connections_to_switch
                save_object['nodes'] = self.network.nodes
                save_object['total_links'] = self.network.total_possible_links

            pickle.dump(save_object, open(self.args.saved_tree_name, "wb"))

            tree_lengths = []
            tree_lengths_2 = []
            for root_idx in range(self.network.nodes):
                max_time = 0
                for edge in trees[root_idx]:
                    if edge[2] + edge[3] > max_time:
                        max_time = edge[2] + edge[3]
                tree_lengths_2.append(max_time)
                tree_lengths.append(round(100/max_time))
            self.data_percentage_in_flows = self.round_to_100_percent(tree_lengths)
            print("Yo")

    def round_to_100_percent(self, number_set):
        """
            This function take a list of number and return a list of percentage, which represents the portion of each number in sum of all numbers
            Moreover, those percentages are adding up to 100%!!!
            Notice: the algorithm we are using here is 'Largest Remainder'
            The down-side is that the results won't be accurate, but they are never accurate anyway:)
        """

        unround_numbers = [x / float(sum(number_set)) * 100 for x in number_set]
        decimal_part_with_index = sorted([(index, unround_numbers[index] % 1) for index in range(len(unround_numbers))],
                                         key=lambda y: y[1], reverse=True)
        remainder = 100 - sum([int(x) for x in unround_numbers])
        index = 0
        while remainder > 0:
            unround_numbers[decimal_part_with_index[index][0]] += 1
            remainder -= 1
            index = (index + 1) % len(number_set)
        return [int(x) / 100 for x in unround_numbers]


    # def compute_trees(self, kary, alternate=False, sort=True, verbose=False)

    def check_inside_possible_links(self, child, parent, root_idx, possible_links):
        for link in possible_links:
            if link[0] == child and link[1] == parent and link[2] == root_idx:
                return True
        return False

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
                rs_timestep = self.timesteps - edge[2] - edge[3]

                # send from rs_child to rs_parent for tree root at rs_timestep
                if rs_timestep not in reduce_scatter_schedule[rs_child].keys():
                    reduce_scatter_schedule[rs_child][rs_timestep] = {}
                flow_children = [(root, child) for child in self.trees_children[root][rs_child]]
                reduce_scatter_schedule[rs_child][rs_timestep][root] = (
                (rs_parent, reduce_scatter_ni[rs_parent][rs_timestep], edge[3]), flow_children, 1, rs_timestep)
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
                    (ag_child, all_gather_ni[ag_child][ag_timestep], edge[3]))
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
        # allreduce.generate_per_tree_dotfile('multitreedot')
    sort_timesteps = allreduce.timesteps
    allreduce.generate_schedule()
    # allreduce.max_num_concurrent_flows()
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
