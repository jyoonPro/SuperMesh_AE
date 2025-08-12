import argparse
import copy
import sys
import os
import math
import numpy as np
from copy import deepcopy
import re
from collections import defaultdict

sys.path.append('{}/src/allreduce/network'.format(os.environ['SIMHOME']))

from network import construct_network
from allreduce import Allreduce


class FatMeshAllReduceTrees(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)
        self.number_of_nodes = int(math.sqrt(self.network.nodes))
        self.args = args
        # self.number_of_nodes = int(math.sqrt(args.num_hmcs))
        self.trees = None
        self.ring = []
        self.full_trees = None
        self.partial_trees = None
        self.rs_schedule = {}
        self.ag_schedule = {}
        self.rs2_final_dep = {}

    def get_lrtb(self, node, nodes_per_dim):
        col_idx = node % nodes_per_dim
        row_idx = math.floor(node / nodes_per_dim)
        if col_idx == 0:
            left = None
            right = node + 1
        elif col_idx == nodes_per_dim - 1:
            left = node - 1
            right = None
        else:
            left = node - 1
            right = node + 1

        if row_idx == 0:
            top = None
            bottom = node + nodes_per_dim
        elif row_idx == nodes_per_dim - 1:
            top = node - nodes_per_dim
            bottom = None
        else:
            top = node - nodes_per_dim
            bottom = node + nodes_per_dim
        return left, right, top, bottom

    def get_lrtb_nodes(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        left_nodes = {}
        right_nodes = {}
        top_nodes = {}
        bottom_nodes = {}
        for node in range(total_nodes):
            left, right, top, bottom = self.get_lrtb(node, per_dim_nodes)
            left_nodes[node] = left
            right_nodes[node] = right
            top_nodes[node] = top
            bottom_nodes[node] = bottom
        return left_nodes, right_nodes, top_nodes, bottom_nodes

    def get_neighbor(self, node, left_nodes, right_nodes, top_nodes, bottom_nodes, direction):
        if direction == 'top':
            return top_nodes[node]
        elif direction == 'bottom':
            return bottom_nodes[node]
        elif direction == 'left':
            return left_nodes[node]
        elif direction == 'right':
            return right_nodes[node]
        else:
            raise RuntimeError("Direction is wrong")

    def connect_nodes_to_uni_or_all_tree(self, first_direction, second_direction, root):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        left_nodes, right_nodes, top_nodes, bottom_nodes = self.get_lrtb_nodes()

        tree = []
        time_tracker = {}
        node_to_consider = root
        time_tracker[node_to_consider] = 0
        for_second_direction = []
        for_second_direction.append(node_to_consider)

        for i in range(per_dim_nodes - 1):
            timestep = time_tracker[node_to_consider]
            node = self.get_neighbor(node_to_consider, left_nodes, right_nodes, top_nodes, bottom_nodes, first_direction)
            tree.append((node, node_to_consider, timestep + 1, 0))
            time_tracker[node] = timestep + 1
            for_second_direction.append(node)
            node_to_consider = node
        for target_node in for_second_direction:
            node_to_consider = target_node
            for i in range(per_dim_nodes - 1):
                timestep = time_tracker[node_to_consider]
                node = self.get_neighbor(node_to_consider, left_nodes, right_nodes, top_nodes, bottom_nodes,
                                         second_direction)
                tree.append((node, node_to_consider, timestep + 1, 1))
                time_tracker[node] = timestep + 1
                node_to_consider = node
        return tree

    def build_trees_all(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        top_left_tree = self.connect_nodes_to_uni_or_all_tree('right', 'bottom', 0)
        top_right_tree = self.connect_nodes_to_uni_or_all_tree('bottom', 'left', per_dim_nodes - 1)
        bottom_right_tree = self.connect_nodes_to_uni_or_all_tree('left', 'top', total_nodes - 1)
        bottom_left_tree = self.connect_nodes_to_uni_or_all_tree('top', 'right', per_dim_nodes * (per_dim_nodes - 1))
        self.timesteps = 2 * per_dim_nodes - 2
        return top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree

    def build_trees_unidirectional_ag(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        top_left_tree = self.connect_nodes_to_uni_or_all_tree('right', 'bottom', 0)
        top_right_tree = self.connect_nodes_to_uni_or_all_tree('bottom', 'left', per_dim_nodes - 1)
        bottom_right_tree = self.connect_nodes_to_uni_or_all_tree('left', 'top', total_nodes - 1)
        bottom_left_tree = self.connect_nodes_to_uni_or_all_tree('top', 'right', per_dim_nodes * (per_dim_nodes - 1))
        self.timesteps = 2 * per_dim_nodes - 2
        return top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree

    def build_trees_unidirectional_rs(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        top_left_tree = self.connect_nodes_to_uni_or_all_tree('bottom', 'right', 0)
        top_right_tree = self.connect_nodes_to_uni_or_all_tree('left', 'bottom', per_dim_nodes - 1)
        bottom_right_tree = self.connect_nodes_to_uni_or_all_tree('top', 'left', total_nodes - 1)
        bottom_left_tree = self.connect_nodes_to_uni_or_all_tree('right', 'top', per_dim_nodes * (per_dim_nodes - 1))
        return top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree

    def connect_nodes_to_alternate_tree(self, first_direction, second_direction, root, even):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        left_nodes, right_nodes, top_nodes, bottom_nodes = self.get_lrtb_nodes()

        tree = []
        time_tracker = {}
        node_to_consider = root
        time_tracker[node_to_consider] = 0
        for_second_direction = []
        for_second_direction.append(node_to_consider)
        again_first_direction = []
        first_second_direction = []

        # TODO: Add comments
        for i in range(per_dim_nodes - 2):
            timestep = time_tracker[node_to_consider]
            node = self.get_neighbor(node_to_consider, left_nodes, right_nodes, top_nodes, bottom_nodes, first_direction)
            tree.append((node, node_to_consider, timestep + 1, 1))
            time_tracker[node] = timestep + 1
            for_second_direction.append(node)
            node_to_consider = node
        for index, target_node in enumerate(for_second_direction):
            node_to_consider = target_node
            if not even:
                if index == 0:
                    goto = per_dim_nodes - 1
                elif index % 2 == 1:
                    goto = per_dim_nodes - 1
                else:
                    goto = per_dim_nodes - 2
            else:
                if index % 2 == 0:
                    goto = per_dim_nodes - 1
                else:
                    goto = per_dim_nodes - 2
            for i in range(goto):
                timestep = time_tracker[node_to_consider]
                node = self.get_neighbor(node_to_consider, left_nodes, right_nodes, top_nodes, bottom_nodes, second_direction)
                tree.append((node, node_to_consider, timestep + 1, 1))
                time_tracker[node] = timestep + 1
                if index == per_dim_nodes - 2:
                    if i % 2 == 0:
                        first_second_direction.append(node_to_consider)
                node_to_consider = node
                if not even:
                    if index % 2 == 1 and i == goto - 1:
                        again_first_direction.append(node_to_consider)
                else:
                    if index % 2 == 0 and index < per_dim_nodes - 2 and i == goto - 1:
                        again_first_direction.append(node_to_consider)

        for target_node in again_first_direction:
            node_to_consider = target_node
            timestep = time_tracker[node_to_consider]
            node = self.get_neighbor(node_to_consider, left_nodes, right_nodes, top_nodes, bottom_nodes, first_direction)
            tree.append((node, node_to_consider, timestep + 1, 0))
            time_tracker[node] = timestep + 1

        for target_node in first_second_direction:
            node_to_consider = target_node
            timestep = time_tracker[node_to_consider]
            node = self.get_neighbor(node_to_consider, left_nodes, right_nodes, top_nodes, bottom_nodes, first_direction)
            tree.append((node, node_to_consider, timestep + 1, 1))
            time_tracker[node] = timestep + 1
            node_to_consider = node
            timestep = time_tracker[node_to_consider]
            node = self.get_neighbor(node_to_consider, left_nodes, right_nodes, top_nodes, bottom_nodes, second_direction)
            tree.append((node, node_to_consider, timestep + 1, 0))
            time_tracker[node] = timestep + 1

        return tree

    def build_trees_alternate_odd(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        top_left_tree = self.connect_nodes_to_alternate_tree('right', 'bottom', 0, False)
        top_right_tree = self.connect_nodes_to_alternate_tree('bottom', 'left', per_dim_nodes - 1, False)
        bottom_right_tree = self.connect_nodes_to_alternate_tree('left', 'top', total_nodes - 1, False)
        bottom_left_tree = self.connect_nodes_to_alternate_tree('top', 'right', per_dim_nodes * (per_dim_nodes - 1), False)
        self.timesteps = 2 * per_dim_nodes - 2
        return top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree

    def build_trees_alternate_even(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        top_left_tree = self.connect_nodes_to_alternate_tree('right', 'bottom', 0, True)
        top_right_tree = self.connect_nodes_to_alternate_tree('bottom', 'left', per_dim_nodes - 1, True)
        bottom_right_tree = self.connect_nodes_to_alternate_tree('left', 'top', total_nodes - 1, True)
        bottom_left_tree = self.connect_nodes_to_alternate_tree('top', 'right', per_dim_nodes * (per_dim_nodes - 1),
                                                                True)
        self.timesteps = 2 * per_dim_nodes - 2
        return top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree

    def compute_trees(self, kary=None, alternate=True, sort=False, verbose=False):
        if self.args.allreduce == 'fatmesh_all':
            top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree = self.build_trees_all()
        elif self.args.allreduce == 'fatmesh_alternate':
            if int(math.sqrt(self.args.num_hmcs)) % 2 == 0:
                top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree = self.build_trees_alternate_even()
            else:
                top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree = self.build_trees_alternate_odd()
        elif self.args.allreduce == 'fatmesh_unidirectional':
            ag_top_left_tree, ag_top_right_tree, ag_bottom_left_tree, ag_bottom_right_tree = self.build_trees_unidirectional_ag()
            rs_top_left_tree, rs_top_right_tree, rs_bottom_left_tree, rs_bottom_right_tree = self.build_trees_unidirectional_rs()

        if self.args.allreduce == 'fatmesh_unidirectional':
            self.rs_template_trees = {}
            self.rs_template_trees[0] = sorted(rs_top_left_tree, key=lambda x: x[2])
            self.rs_template_trees[self.number_of_nodes - 1] = sorted(rs_top_right_tree, key=lambda x: x[2])
            self.rs_template_trees[self.number_of_nodes * (self.number_of_nodes - 1)] = sorted(rs_bottom_left_tree, key=lambda x: x[2])
            self.rs_template_trees[self.args.num_hmcs - 1] = sorted(rs_bottom_right_tree, key=lambda x: x[2])
            self.ag_template_trees = {}
            self.ag_template_trees[0] = sorted(ag_top_left_tree, key=lambda x: x[2])
            self.ag_template_trees[self.number_of_nodes - 1] = sorted(ag_top_right_tree, key=lambda x: x[2])
            self.ag_template_trees[self.number_of_nodes * (self.number_of_nodes - 1)] = sorted(ag_bottom_left_tree, key=lambda x: x[2])
            self.ag_template_trees[self.args.num_hmcs - 1] = sorted(ag_bottom_right_tree, key=lambda x: x[2])
        else:
            self.template_trees = {}
            self.template_trees[0] = sorted(top_left_tree, key=lambda x: x[2])
            self.template_trees[self.number_of_nodes - 1] = sorted(top_right_tree, key=lambda x: x[2])
            self.template_trees[self.number_of_nodes * (self.number_of_nodes - 1)] = sorted(bottom_left_tree, key=lambda x: x[2])
            self.template_trees[self.args.num_hmcs - 1] = sorted(bottom_right_tree, key=lambda x: x[2])
        # edge_dict = {}
        # for i in range(self.args.num_hmcs):
        #     left, right, top, bottom = self.get_lrtb(i, self.number_of_nodes)
        #     if left is not None:
        #         edge_dict[(i, left)] = 0
        #     if right is not None:
        #         edge_dict[(i, right)] = 0
        #     if top is not None:
        #         edge_dict[(i, top)] = 0
        #     if bottom is not None:
        #         edge_dict[(i, bottom)] = 0
        #
        # self.edge_dict = edge_dict
        # self.edge_dict_ag = copy.deepcopy(edge_dict)
        if self.args.allreduce == 'fatmesh_unidirectional':
            self.rs_time_relative_links_last = {}
            for key in self.rs_template_trees.keys():
                tree = self.rs_template_trees[key]
                for edge in tree:
                    time = edge[2] - 1
                    if time not in self.rs_time_relative_links_last.keys():
                        self.rs_time_relative_links_last[time] = []
                    self.rs_time_relative_links_last[time].append((edge[0], edge[1], key, edge[3]))
            self.ag_time_relative_links_last = {}
            for key in self.ag_template_trees.keys():
                tree = self.ag_template_trees[key]
                for edge in tree:
                    time = edge[2] - 1
                    if time not in self.ag_time_relative_links_last.keys():
                        self.ag_time_relative_links_last[time] = []
                    self.ag_time_relative_links_last[time].append((edge[0], edge[1], key, edge[3]))
        else:
            self.time_relative_links_last = {}
            for key in self.template_trees.keys():
                tree = self.template_trees[key]
                for edge in tree:
                    time = edge[2] - 1
                    if time not in self.time_relative_links_last.keys():
                        self.time_relative_links_last[time] = []
                    self.time_relative_links_last[time].append((edge[0], edge[1], key, edge[3]))
        self.total_partial_trees = self.args.total_partial_trees

        self.tree_roots = []
        self.tree_roots.append(0)
        self.tree_roots.append(self.number_of_nodes - 1)
        self.tree_roots.append(self.number_of_nodes * (self.number_of_nodes - 1))
        self.tree_roots.append(self.args.num_hmcs - 1)
        if self.args.allreduce != 'fatmesh_unidirectional':
            self.trees = {}
            self.trees[0] = top_left_tree
            self.trees[self.number_of_nodes - 1] = top_right_tree
            self.trees[self.number_of_nodes * (self.number_of_nodes - 1)] = bottom_left_tree
            self.trees[self.args.num_hmcs - 1] = bottom_right_tree

    # def compute_trees(self, kary=None, alternate=True, sort=False, verbose=False)

    def get_dependency(self, tree, source):
        dependencies = []
        for dep in self.trees_children[tree][source]:
            dependencies.append(dep)
        return dependencies

    def get_ag_dependency(self, tree, source):
        dependencies = []
        if self.trees_parent[tree][source] is not None:
            dependencies.append(self.trees_parent[tree][source])
        return dependencies

    def get_uni_rs_dependency(self, tree, source):
        dependencies = []
        for dep in self.rs_trees_children[tree][source]:
            dependencies.append(dep)
        return dependencies

    def get_uni_ag_dependency(self, tree, source):
        dependencies = []
        if self.ag_trees_parent[tree][source] is not None:
            dependencies.append(self.ag_trees_parent[tree][source])
        return dependencies

    # def get_start_time(self, edge_dict, source, dest, dependencies):
    #     max_dep_time = 0
    #     for dep in dependencies:
    #         if edge_dict[(dep, source)] > max_dep_time:
    #             max_dep_time = edge_dict[(dep, source)]
    #     if max_dep_time > edge_dict[(source, dest)]:
    #         return max_dep_time
    #     else:
    #         return edge_dict[(source, dest)]

    def update_rs_final_dep(self, root, chunk_id):
        dependencies = self.get_dependency(root, root)
        if root not in self.rs2_final_dep.keys():
            self.rs2_final_dep[root] = []
        self.rs2_final_dep[root].append((chunk_id, dependencies))

    def update_rs_final_dep_uni(self, root, chunk_id):
        dependencies = self.get_uni_rs_dependency(root, root)
        if root not in self.rs2_final_dep.keys():
            self.rs2_final_dep[root] = []
        self.rs2_final_dep[root].append((chunk_id, dependencies))

    def add_reduce_scatter(self, chunk_id, total_message):
        if self.args.allreduce == 'fatmesh_unidirectional':
            for key in sorted(self.rs_time_relative_links_last.keys(), reverse=True):
                for edge in self.rs_time_relative_links_last[key]:
                    link = (edge[0], edge[1], edge[3])
                    if link not in self.rs_schedule.keys():
                        self.rs_schedule[link] = []
                    dependencies = self.get_uni_rs_dependency(tree=edge[2], source=edge[0])
                    # TODO: Fix NI logics based on extra links
                    # source_ni = self.get_ni(edge[0], edge[1])
                    # target_ni = self.get_ni(edge[1], edge[0])
                    if edge[3]:
                        second = False
                    else:
                        second = True
                    source_ni, target_ni = self.get_source_dest_NI(edge[0], edge[1], self.args.booksim_network, second)
                    # print("Source Ni " + str(source_ni) + " Destination NI" + str(target_ni))
                    tree = edge[2]
                    # if link not in self.edge_dict.keys():
                    #     self.edge_dict[link] = 0
                    # start_time = self.get_start_time(self.edge_dict, edge[0], edge[1], dependencies)
                    self.rs_schedule[link].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))
                    # self.edge_dict[link] = start_time + 1
            # TODO: Make sure that all gather starts after getting all data from reduce-scatter for root node.
            for root in self.tree_roots:
                self.update_rs_final_dep_uni(root, chunk_id)
        else:
            for key in sorted(self.time_relative_links_last.keys(), reverse=True):
                for edge in self.time_relative_links_last[key]:
                    link = (edge[0], edge[1], edge[3])
                    if link not in self.rs_schedule.keys():
                        self.rs_schedule[link] = []
                    dependencies = self.get_dependency(tree=edge[2], source=edge[0])
                    # TODO: Fix NI logics based on extra links
                    # source_ni = self.get_ni(edge[0], edge[1])
                    # target_ni = self.get_ni(edge[1], edge[0])
                    if edge[3]:
                        second = False
                    else:
                        second = True
                    source_ni, target_ni = self.get_source_dest_NI(edge[0], edge[1], self.args.booksim_network, second)
                    # print("Source Ni " + str(source_ni) + " Destination NI" + str(target_ni))
                    tree = edge[2]
                    # if link not in self.edge_dict.keys():
                    #     self.edge_dict[link] = 0
                    # start_time = self.get_start_time(self.edge_dict, edge[0], edge[1], dependencies)
                    self.rs_schedule[link].append(
                        (tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))
                    # self.edge_dict[link] = start_time + 1
            # TODO: Make sure that all gather starts after getting all data from reduce-scatter for root node.
            for root in self.tree_roots:
                self.update_rs_final_dep(root, chunk_id)

    def add_all_gather(self, chunk_id, total_message):
        if self.args.allreduce == 'fatmesh_unidirectional':
            for key in sorted(self.ag_time_relative_links_last.keys()):
                for edge in self.ag_time_relative_links_last[key]:
                    link = (edge[1], edge[0], edge[3])
                    if link not in self.ag_schedule.keys():
                        self.ag_schedule[link] = []
                    dependencies = self.get_uni_ag_dependency(tree=edge[2], source=edge[1])
                    # TODO: Fix NI logics based on extra links
                    # source_ni = self.get_ni(edge[1], edge[0])
                    # target_ni = self.get_ni(edge[0], edge[1])
                    if edge[3]:
                        second = False
                    else:
                        second = True
                    source_ni, target_ni = self.get_source_dest_NI(edge[1], edge[0], self.args.booksim_network, second)
                    tree = edge[2]
                    # if link not in self.edge_dict_ag.keys():
                    #     self.edge_dict_ag[link] = 0
                    self.ag_schedule[link].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))
                    # self.edge_dict_ag[link] = self.edge_dict_ag[link]
        else:
            for key in sorted(self.time_relative_links_last.keys()):
                for edge in self.time_relative_links_last[key]:
                    link = (edge[1], edge[0], edge[3])
                    if link not in self.ag_schedule.keys():
                        self.ag_schedule[link] = []
                    dependencies = self.get_ag_dependency(tree=edge[2], source=edge[1])
                    # TODO: Fix NI logics based on extra links
                    # source_ni = self.get_ni(edge[1], edge[0])
                    # target_ni = self.get_ni(edge[0], edge[1])
                    if edge[3]:
                        second = False
                    else:
                        second = True
                    source_ni, target_ni = self.get_source_dest_NI(edge[1], edge[0], self.args.booksim_network, second)
                    print(source_ni)
                    tree = edge[2]
                    # if link not in self.edge_dict_ag.keys():
                    #     self.edge_dict_ag[link] = 0
                    self.ag_schedule[link].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))
                    # self.edge_dict_ag[link] = self.edge_dict_ag[link]

    def get_ni(self, source_node, target_node):
        if target_node == source_node - 1:
            return 0
        elif target_node == source_node + 1:
            return 1
        elif target_node == source_node - self.number_of_nodes:
            return 2
        elif target_node == source_node + self.number_of_nodes:
            return 3
        else:
            raise RuntimeError('Error: NI info is wrong')

    def check_per_link_timestep_ordering(self, per_link_schedule):
        current_max_end = per_link_schedule[0][5] - 1
        for schedule in per_link_schedule:
            start = schedule[5]
            end = schedule[6]
            if end < start:
                raise RuntimeError("End time is earlier than start time")
            if start < current_max_end:
                raise RuntimeError("Start time is earlier than current max end time")
            # if start - current_max_end != 1:
            #     raise RuntimeError("Difference between start time and current max end time is not 1")
            current_max_end = end

    def get_source_dest_NI(self, source_node, dest_node, topology, second=False):
        nodes_in_dimension = int(math.sqrt(self.args.num_hmcs))
        row = source_node // nodes_in_dimension
        col = source_node % nodes_in_dimension
        if topology == 'torus':
            mesh = False
        else:
            mesh = True

        if topology == 'fatmesh_all':
            radix = 5
        else:
            radix = 4

        north = None
        south = None
        east = None
        west = None
        # TODO: Add comments
        if row == 0 and not mesh:
            if nodes_in_dimension > 2:
                north = source_node + nodes_in_dimension * (nodes_in_dimension - 1)
        elif row != 0:
            north = source_node - nodes_in_dimension

        if row == nodes_in_dimension - 1 and not mesh:
            if nodes_in_dimension > 2:
                south = source_node - nodes_in_dimension * (nodes_in_dimension - 1)
        elif row != nodes_in_dimension - 1:
            south = source_node + nodes_in_dimension

        if col == 0 and not mesh:
            if nodes_in_dimension > 2:
                west = source_node + nodes_in_dimension - 1
        elif col != 0:
            west = source_node - 1

        if col == nodes_in_dimension - 1 and not mesh:
            if nodes_in_dimension > 2:
                east = source_node - nodes_in_dimension + 1
        elif col != nodes_in_dimension - 1:
            east = source_node + 1

        assert (dest_node == north) or (dest_node == east) or (dest_node == south) or (dest_node == west)

        dest_ni = None
        src_ni = None
        if topology == 'torus' or topology == 'mesh':
            if dest_node == north:
                dest_ni = radix * dest_node + 2
                # src_ni = radix * source_node + 0
                src_ni = radix * source_node + 0
            elif dest_node == east:
                dest_ni = radix * dest_node + 3
                src_ni = radix * source_node + 1
            elif dest_node == south:
                dest_ni = radix * dest_node + 0
                src_ni = radix * source_node + 2
            elif dest_node == west:
                dest_ni = radix * dest_node + 1
                src_ni = radix * source_node + 3
        elif topology == 'fatmesh_unidirectional':
            if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension - 1:
                if row == 0 and col == 0:
                    if dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                        src_ni = radix * source_node + 1
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 0
                        src_ni = radix * source_node + 0
                    elif dest_node == south:
                        dest_ni = radix * dest_node + 0
                        src_ni = radix * source_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == 0 and col == nodes_in_dimension - 1:
                    if dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                        src_ni = radix * source_node + 2
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 1
                        src_ni = radix * source_node + 1
                    elif dest_node == west:
                        dest_ni = radix * dest_node + 1
                        src_ni = radix * source_node + 3
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                    if dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                        src_ni = radix * source_node + 3
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 2
                        src_ni = radix * source_node + 2
                    elif dest_node == north:
                        dest_ni = radix * dest_node + 2
                        src_ni = radix * source_node + 0
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == 0:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                        src_ni = radix * source_node + 0
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 3
                        src_ni = radix * source_node + 3
                    elif dest_node == east:
                        dest_ni = radix * dest_node + 3
                        src_ni = radix * source_node + 1
                    else:
                        raise RuntimeError("Wrong dest node")
                else:
                    if row == 0:
                        if dest_node == east and not second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        elif dest_node == east and second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 0
                        elif dest_node == south:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        elif dest_node == west:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == nodes_in_dimension - 1:
                        if dest_node == south and not second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        elif dest_node == south and second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 1
                        elif dest_node == west:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        elif dest_node == north:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1:
                        if dest_node == west and not second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        elif dest_node == west and second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 2
                        elif dest_node == north:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        elif dest_node == east:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == 0:
                        if dest_node == north and not second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        elif dest_node == north and second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 3
                        elif dest_node == east:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        elif dest_node == south:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        else:
                            raise RuntimeError("Wrong dest node")
            else:
                if dest_node == north:
                    dest_ni = radix * dest_node + 2
                    src_ni = radix * source_node + 0
                elif dest_node == east:
                    dest_ni = radix * dest_node + 3
                    src_ni = radix * source_node + 1
                elif dest_node == south:
                    dest_ni = radix * dest_node + 0
                    src_ni = radix * source_node + 2
                elif dest_node == west:
                    dest_ni = radix * dest_node + 1
                    src_ni = radix * source_node + 3
        elif topology == 'fatmesh_all':
            if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension - 1:
                if row == 0 and col == 0:
                    if dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                        src_ni = radix * source_node + 1
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 4
                        src_ni = radix * source_node + 0
                    elif dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                        src_ni = radix * source_node + 2
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 3
                        src_ni = radix * source_node + 3
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == 0 and col == nodes_in_dimension - 1:
                    if dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                        src_ni = radix * source_node + 3
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 0
                        src_ni = radix * source_node + 4
                    elif dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                        src_ni = radix * source_node + 2
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 4
                        src_ni = radix * source_node + 1
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                        src_ni = radix * source_node + 0
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 1
                        src_ni = radix * source_node + 4
                    elif dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                        src_ni = radix * source_node + 3
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 4
                        src_ni = radix * source_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == 0:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                        src_ni = radix * source_node + 0
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 4
                        src_ni = radix * source_node + 3
                    elif dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                        src_ni = radix * source_node + 1
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 2
                        src_ni = radix * source_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                else:
                    if row == 0:
                        if dest_node == east and not second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        elif dest_node == east and second:
                            dest_ni = radix * dest_node + 4
                            src_ni = radix * source_node + 0
                        elif dest_node == west and not second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        elif dest_node == west and second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 4
                        elif dest_node == south:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == nodes_in_dimension - 1:
                        if dest_node == north and not second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        elif dest_node == north and second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 4
                        elif dest_node == south and not second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        elif dest_node == south and second:
                            dest_ni = radix * dest_node + 4
                            src_ni = radix * source_node + 1
                        elif dest_node == west:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1:
                        if dest_node == east and not second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        elif dest_node == east and second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 4
                        elif dest_node == west and not second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        elif dest_node == west and second:
                            dest_ni = radix * dest_node + 4
                            src_ni = radix * source_node + 2
                        elif dest_node == north:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == 0:
                        if dest_node == south and not second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        elif dest_node == south and second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 4
                        elif dest_node == north and not second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        elif dest_node == north and second:
                            dest_ni = radix * dest_node + 4
                            src_ni = radix * source_node + 3
                        elif dest_node == east:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        else:
                            raise RuntimeError("Wrong dest node")
            else:
                if dest_node == north:
                    dest_ni = radix * dest_node + 2
                    src_ni = radix * source_node + 0
                elif dest_node == east:
                    dest_ni = radix * dest_node + 3
                    src_ni = radix * source_node + 1
                elif dest_node == south:
                    dest_ni = radix * dest_node + 0
                    src_ni = radix * source_node + 2
                elif dest_node == west:
                    dest_ni = radix * dest_node + 1
                    src_ni = radix * source_node + 3
        elif topology == 'fatmesh_alternate':
            if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension - 1:
                if nodes_in_dimension % 2 == 0:
                    if row == 0 and col == 0:
                        if dest_node == east and not second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        elif dest_node == east and second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 0
                        elif dest_node == south and not second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        elif dest_node == south and second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == 0 and col == nodes_in_dimension - 1:
                        if dest_node == west and not second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        elif dest_node == west and second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 0
                        elif dest_node == south and not second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        elif dest_node == south and second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 1
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                        if dest_node == north and not second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        elif dest_node == north and second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 1
                        elif dest_node == west and not second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        elif dest_node == west and second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == 0:
                        if dest_node == north and not second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        elif dest_node == north and second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 3
                        elif dest_node == east and not second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        elif dest_node == east and second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    else:
                        if row == 0:
                            if col % 2 == 0:
                                if dest_node == east and not second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == east and second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 0
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == west and not second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == west and second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 0
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == nodes_in_dimension - 1:
                            if row % 2 == 0:
                                if dest_node == south and not second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                elif dest_node == south and second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 1
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == north and not second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                elif dest_node == north and second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 1
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif row == nodes_in_dimension - 1:
                            if col % 2 == 0:
                                if dest_node == east and not second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == east and second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 2
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == west and not second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == west and second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 2
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == 0:
                            if row % 2 == 0:
                                if dest_node == south and not second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                elif dest_node == south and second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 3
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == north and not second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                elif dest_node == north and second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 3
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                else:
                    if row == 0 and col == 0:
                        if dest_node == east and not second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        elif dest_node == east and second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 0
                        elif dest_node == south:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == 0 and col == nodes_in_dimension - 1:
                        if dest_node == south and not second:
                            dest_ni = radix * dest_node + 0
                            src_ni = radix * source_node + 2
                        elif dest_node == south and second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 1
                        elif dest_node == west:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                        if dest_node == west and not second:
                            dest_ni = radix * dest_node + 1
                            src_ni = radix * source_node + 3
                        elif dest_node == west and second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 2
                        elif dest_node == north:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == 0:
                        if dest_node == north and not second:
                            dest_ni = radix * dest_node + 2
                            src_ni = radix * source_node + 0
                        elif dest_node == north and second:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 3
                        elif dest_node == east:
                            dest_ni = radix * dest_node + 3
                            src_ni = radix * source_node + 1
                        else:
                            raise RuntimeError("Wrong dest node")
                    else:
                        if row == 0:
                            if col % 2 == 0:
                                if dest_node == east and not second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == east and second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 0
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == west and not second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == west and second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 0
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == nodes_in_dimension - 1:
                            if row % 2 == 0:
                                if dest_node == south and not second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                elif dest_node == south and second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 1
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == north and not second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                elif dest_node == north and second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 1
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif row == nodes_in_dimension - 1:
                            if col % 2 == 0:
                                if dest_node == west and not second:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                elif dest_node == west and second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 2
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == east and not second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == east and second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 2
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                elif dest_node == west:
                                    dest_ni = radix * dest_node + 1
                                    src_ni = radix * source_node + 3
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == 0:
                            if row % 2 == 0:
                                if dest_node == north and not second:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                elif dest_node == north and second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 3
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                elif dest_node == south:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == south and not second:
                                    dest_ni = radix * dest_node + 0
                                    src_ni = radix * source_node + 2
                                elif dest_node == south and second:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 3
                                elif dest_node == north:
                                    dest_ni = radix * dest_node + 2
                                    src_ni = radix * source_node + 0
                                elif dest_node == east:
                                    dest_ni = radix * dest_node + 3
                                    src_ni = radix * source_node + 1
                                else:
                                    raise RuntimeError("Wrong dest node")
            else:
                if dest_node == north:
                    dest_ni = radix * dest_node + 2
                    src_ni = radix * source_node + 0
                elif dest_node == east:
                    dest_ni = radix * dest_node + 3
                    src_ni = radix * source_node + 1
                elif dest_node == south:
                    dest_ni = radix * dest_node + 0
                    src_ni = radix * source_node + 2
                elif dest_node == west:
                    dest_ni = radix * dest_node + 1
                    src_ni = radix * source_node + 3
        source_ni = src_ni - radix * source_node
        dst_ni = dest_ni - radix * dest_node
        return source_ni, dst_ni

    def check_timestep_ordering(self):
        for link in self.rs_schedule.keys():
            self.check_per_link_timestep_ordering(self.rs_schedule[link])
        for link in self.ag_schedule.keys():
            self.check_per_link_timestep_ordering(self.ag_schedule[link])

    '''
    generate_schedule()
    @verbose: print the generated schedules

    desc - generate reduce_scatter_schedule and all_gather_schedule from ring,
           verified with generate_schedule in MultiTree
    '''

    def generate_schedule(self, verbose=False):
        # compute parent-children dependency
        if self.args.allreduce == 'fatmesh_unidirectional':
            self.rs_trees_parent = {}
            self.rs_trees_children = {}
            for root in self.tree_roots:
                self.rs_trees_parent[root] = {}
                self.rs_trees_parent[root][root] = None
                self.rs_trees_children[root] = {}
                # TODO: Check whether all nodes are added or not for each root, Also make sure some values are not overwriting.
                for node in range(self.args.num_hmcs):
                    self.rs_trees_children[root][node] = []
                for edge in self.rs_template_trees[root]:
                    child = edge[0]
                    parent = edge[1]
                    self.rs_trees_parent[root][child] = parent
                    self.rs_trees_children[root][parent].append(child)
            self.ag_trees_parent = {}
            self.ag_trees_children = {}
            for root in self.tree_roots:
                self.ag_trees_parent[root] = {}
                self.ag_trees_parent[root][root] = None
                self.ag_trees_children[root] = {}
                # TODO: Check whether all nodes are added or not for each root, Also make sure some values are not overwriting.
                for node in range(self.args.num_hmcs):
                    self.ag_trees_children[root][node] = []
                for edge in self.ag_template_trees[root]:
                    child = edge[0]
                    parent = edge[1]
                    self.ag_trees_parent[root][child] = parent
                    self.ag_trees_children[root][parent].append(child)
        else:
            self.trees_parent = {}
            self.trees_children = {}
            for root in self.tree_roots:
                self.trees_parent[root] = {}
                self.trees_parent[root][root] = None
                self.trees_children[root] = {}
                # TODO: Check whether all nodes are added or not for each root, Also make sure some values are not overwriting.
                for node in range(self.args.num_hmcs):
                    self.trees_children[root][node] = []
                for edge in self.template_trees[root]:
                    child = edge[0]
                    parent = edge[1]
                    self.trees_parent[root][child] = parent
                    self.trees_children[root][parent].append(child)
        # print("Tree parents")
        # print(self.template_trees[12])
        # print(tree)
        # print(source)

        for i in range(self.total_partial_trees):
            self.add_reduce_scatter(chunk_id=i, total_message=self.args.partial_tree_message)
        for i in range(self.total_partial_trees):
            self.add_all_gather(chunk_id=i, total_message=self.args.partial_tree_message)

        # self.check_log = True
        # self.generate_trees_dotfile(str(self.args.num_hmcs) + "_" + self.args.allreduce + ".dot")

        # TODO: Is this important?
        # self.check_timestep_ordering()

        # TODO: Is this rs_schedule to final_reduce_scatter_schedule conversion is required?
        self.final_reduce_scatter_schedule = {}
        for i in range(self.args.num_hmcs):
            self.final_reduce_scatter_schedule[i] = {}
        # for link in self.edge_dict.keys():
        #     self.final_reduce_scatter_schedule[link[0]][link[1]] = []
        for link in self.rs_schedule.keys():
            source = link[0]
            dest = link[1]
            second = link[2]
            self.final_reduce_scatter_schedule[source][(dest, second)] = []
            for schedule in self.rs_schedule[link]:
                tree_id = schedule[0]
                chunk_id = schedule[1]
                dependencies = schedule[2]
                total_messages = schedule[3]
                order = schedule[4]
                source_ni = schedule[5]
                dest_ni = schedule[6]
                self.final_reduce_scatter_schedule[source][(dest, second)].append(
                    (tree_id, chunk_id, dependencies, total_messages, order, source_ni, dest_ni))
        self.reduce_scatter_schedule = self.final_reduce_scatter_schedule

        # TODO: Is this ag_schedule to final_ag_schedule conversion is required?
        self.final_ag_schedule = {}
        for i in range(self.args.num_hmcs):
            self.final_ag_schedule[i] = {}
        # for link in self.edge_dict.keys():
        #     self.final_ag_schedule[link[0]][link[1]] = []
        for link in self.ag_schedule.keys():
            source = link[0]
            dest = link[1]
            second = link[2]
            self.final_ag_schedule[source][(dest, second)] = []
            for schedule in self.ag_schedule[link]:
                tree_id = schedule[0]
                chunk_id = schedule[1]
                dependencies = schedule[2]
                total_messages = schedule[3]
                order = schedule[4]
                source_ni = schedule[5]
                dest_ni = schedule[6]
                self.final_ag_schedule[source][(dest, second)].append(
                    (tree_id, chunk_id, dependencies, total_messages, order, source_ni, dest_ni))
        self.all_gather_schedule = self.final_ag_schedule

    def generate_trees_dotfile(self, filename):
        file_path = '/home/sabuj/Sabuj/Research/FatMesh_DoubleLink/results/mesh_logs/outputs/bb/bb_fatmesh_alternate_16_fatmesh_alternate_AlphaGoZero_google.log'
        reduce_re = re.compile(r"(\d+) \| HMC-(\d+) \| start reducing for flow (\d+) \(from NI (\d+)\) to parent HMC-\((\d+), (\d+)\) \(to NI (\d+)\) for chunk (\d+)")
        receive_re = re.compile(r"(\d+) \| HMC-(\d+) \| receives full reduce for flow (\d+) from child HMC-(\d+)-(\d+) for chunk (\d+)")
        # color palette for ploting nodes of different tree levels
        colors = ['#ffffff', '#f7f4f9', '#e7e1ef', '#d4b9da', '#c994c7',
                  '#df65b0', '#e7298a', '#ce1256', '#980043', '#67001f']

        tree = 'digraph tree {\n'
        tree += '  rankdir = BT;\n'
        tree += '  subgraph {\n'

        # group nodes with same rank (same tree level/iteration)
        # and set up the map for node name and its rank in node_rank
        ranks = {}
        node_rank = {}
        for rank in range(self.timesteps + 1):
            ranks[rank] = []

        for root in self.tree_roots:
            minrank = self.timesteps
            for edge in self.trees[root]:
                child = '"{}-{}"'.format(root, edge[0])
                rank = edge[2]
                ranks[rank].append(child)
                node_rank[child] = rank
                if edge[1] == root and rank - 1 < minrank:
                    minrank = rank - 1
            ranks[minrank].append('"{}-{}"'.format(root, root))
            node_rank['"{}-{}"'.format(root, root)] = minrank

        for root in self.tree_roots:
            tree += '    /* tree {} */\n'.format(root)
            for edge in self.trees[root]:
                child = '"{}-{}"'.format(root, edge[0])
                parent = '"{}-{}"'.format(root, edge[1])
                cycle = self.timesteps - edge[2]
                print("Child " + str(edge[0]) + " parent " + str(edge[1]) + " flow " + str(root) + " isSecond " + str(edge[3]))
                minlen = node_rank[child] - node_rank[parent]  # for strict separation of ranks
                if self.check_log:
                    start = None
                    end = None
                    with open(file_path, 'r') as file:
                        for line in file:
                            reduce_match = reduce_re.match(line)
                            if reduce_match:
                                time, hmc_from, flow, source_ni, dest_hmc, dest_hmc_sub, dest_ni, chunk = reduce_match.groups()
                                print(str(hmc_from) + " " + str(dest_hmc) + " " + str(flow))
                                # if int(hmc_from) == 1 and int(dest_hmc) == 0:
                                #     print("Yoo")
                                if int(hmc_from) == edge[0] and int(dest_hmc) == edge[1] and int(flow) == root and int(dest_hmc_sub) == edge[3] and int(chunk) == 0:
                                    start = time
                                    break
                    with open(file_path, 'r') as file:
                        for line in file:
                            receive_match = receive_re.match(line)
                            if receive_match:
                                time, hmc_to, flow, hmc_from, hmc_from_sub, chunk = receive_match.groups()
                                if int(hmc_from) == edge[0] and int(hmc_to) == edge[1] and int(flow) == root and int(hmc_from_sub) == edge[3] and int(chunk) == 0:
                                    end = time
                                    break
                    assert start is not None
                    assert end is not None
                    tree += ''.join('    {} -> {} [ label="{}-{}({}-{})" minlen={} ];\n'.format(child, parent, cycle, edge[3], start, end, minlen))
                else:
                    tree += ''.join(
                        '    {} -> {} [ label="{}" minlen={} ];\n'.format(child, parent, cycle, minlen))

        tree += '    // note that rank is used in the subgraph\n'
        for rank in range(self.timesteps + 1):
            if ranks[rank]:
                level = '    {rank = same;'
                for node in ranks[rank]:
                    level += ' {};'.format(node)
                level += '}\n'
                tree += level

        tree += '    // node colors\n'
        style = '    {} [style="filled", fillcolor="{}"];\n'
        for rank in range(self.timesteps + 1):
            if ranks[rank]:
                tree += ''.join(style.format(node, colors[rank % len(colors)]) for node in ranks[rank])

        tree += '  } /* closing subgraph */\n'
        tree += '}\n'

        f = open(filename, 'w')
        f.write(tree)
        f.close()


def main(args):
    # network = construct_network(args)
    # network.to_nodes[1].clear() # test no solution case

    allreduce = FatMeshAllReduceTrees(args, None)
    allreduce.compute_trees(verbose=args.verbose)
    # allreduce.generate_schedule(verbose=args.verbose)
    # allreduce.max_num_concurrent_flows()
    if args.gendotfile:
    # allreduce.generate_ring_dotfile('ring.dot')
        name = 'allreduce_trees_' + str(args.num_hmcs)
        if args.all_link:
            name += '_all'
        allreduce.generate_trees_dotfile(name + '.dot')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--num-hmcs', default=16, type=int,
                        help='number of nodes, default is 16')
    parser.add_argument('--gendotfile', default=True, action='store_true',
                        help='generate tree dotfiles, default is False')
    parser.add_argument('--all_link', default=True, action='store_true',
                        help='generate tree dotfiles, default is False')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='detailed print')

    args = parser.parse_args()

    main(args)
