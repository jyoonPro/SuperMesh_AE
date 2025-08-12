import argparse
import copy
import sys
import os
import math
import numpy as np
from copy import deepcopy

sys.path.append('{}/src/allreduce/network'.format(os.environ['SIMHOME']))

from network import construct_network
from allreduce import Allreduce


class HierarchicalOverlapAllreduce(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)
        self.per_dim_nodes = int(math.sqrt(self.network.nodes))
        self.trees = None
        self.total_full_trees = args.total_full_trees
        self.total_partial_trees = args.total_partial_trees
        self.template_trees = None
        self.hierarchical_rs_schedule = {}
        self.hierarchical_ag_schedule = {}
        self.rs1_final_dep = {}
        self.rs2_final_dep = {}
        self.full_tree_roots = None
        self.partial_tree_roots = None
        self.edge_dict = None
        self.edge_dict_ag = None
        self.time_relative_links = None
        self.time_relative_links_last = None


    '''
    compute_trees() - computes allreduce rings (special tree) for the given network
    @kary: not used, skip
    @alternate: not used, skip
    @sort: not used, skip
    @verbose: print detailed info of ring construction process
    '''
    def compute_trees(self, kary=None, alternate=True, sort=False, verbose=False):
        # trees = {}
        self.template_trees = {}
        nodes_in_trees = {}
        node_queues = {}
        connectivity = {}
        all_edge_list = []
        # links_next_available = {}
        node_parent = {}
        leaf_tracker = {}
        self.edge_dict = {}
        for i in range(self.per_dim_nodes):
            # trees[i] = []
            self.template_trees[i] = []
            nodes_in_trees[i] = [i]
            node_queues[i] = []
            node_queues[i].append(i)
            connectivity[i] = []
            # node_parent[i] = {}
            # node_parent[i][i] = None
            # leaf_tracker[i] = {}
            if i == 0:
                connectivity[i].append(1)
                all_edge_list.append((0, 1))
                # links_next_available[(0, 1)] = 0
                self.edge_dict[(0, 1)] = 0
            elif i == self.per_dim_nodes - 1:
                connectivity[i].append(self.per_dim_nodes - 2)
                all_edge_list.append((self.per_dim_nodes - 1, self.per_dim_nodes - 2))
                # links_next_available[(i, self.per_dim_nodes - 2)] = 0
                self.edge_dict[(i, self.per_dim_nodes - 2)] = 0
            else:
                connectivity[i].append(i - 1)
                connectivity[i].append(i + 1)
                all_edge_list.append((i, i - 1))
                all_edge_list.append((i, i + 1))
                # links_next_available[(i, i - 1)] = 0
                # links_next_available[(i, i + 1)] = 0
                self.edge_dict[(i, i - 1)] = 0
                self.edge_dict[(i, i + 1)] = 0

        # self.edge_dict = edge_dict
        self.edge_dict_ag = copy.deepcopy(self.edge_dict)

        # timestamp = 0
        # unused_links = {}
        # unused_links[0] = copy.deepcopy(all_edge_list)

        for t in range(self.per_dim_nodes - 1):
            for i in range(self.per_dim_nodes):
                nodes_to_add = []
                while len(node_queues[i]) is not 0:
                    taken_node = node_queues[i].pop(0)
                    taken_connectivities = connectivity[taken_node]
                    for con in taken_connectivities:
                        if con not in nodes_in_trees[i]:
                            self.template_trees[i].append((con, taken_node, t))
                            nodes_in_trees[i].append(con)
                            nodes_to_add.append(con)
                            # node_parent[i][con] = taken_node
                            # parent_of_parent = node_parent[i][taken_node]
                            # if parent_of_parent is not None:
                            #     leaf_tracker[i][taken_node, parent_of_parent] = (con, taken_node)
                            # print(i)
                            # print(con)
                            # print(taken_node)
                            # leaf_tracker[i][con, taken_node] = None
                for node in nodes_to_add:
                    node_queues[i].append(node)
            # timestamp += 1
        # self.template_trees = template_trees

        self.full_tree_roots = []
        for i in range(self.per_dim_nodes):
            self.full_tree_roots.append(i)
        self.partial_tree_roots = []
        self.partial_tree_roots.append(0)
        self.partial_tree_roots.append(self.per_dim_nodes - 1)

        # last_trees = {}
        # last_trees[0] = self.template_trees[0]
        # last_trees[self.per_dim_nodes - 1] = self.template_trees[self.per_dim_nodes - 1]
        self.time_relative_links = {}
        self.time_relative_links_last = {}
        for i in range(self.per_dim_nodes - 1):
            self.time_relative_links[i] = []
            self.time_relative_links_last[i] = []
        for key in self.template_trees.keys():
            tree = self.template_trees[key]
            for edge in tree:
                self.time_relative_links[edge[2]].append((edge[0], edge[1], key))
            if key == 0 or key == self.per_dim_nodes - 1:
                for edge in tree:
                    self.time_relative_links_last[edge[2]].append((edge[0], edge[1], key))
        # self.time_relative_links = time_relative_links
        # self.time_relative_links_last = time_relative_links_last



        # full_trees = []
        # total_full_trees = self.args.total_full_trees
        # self.total_full_trees = total_full_trees
        # for cnt in range(total_full_trees):
        #     new_trees = {}
        #     for i in range(self.number_of_nodes):
        #         new_trees[i] = []
        #     for timestep in time_relative_links.keys():
        #         edges_in_timestep = time_relative_links[timestep]
        #         for edge in edges_in_timestep:
        #             next_free_time = links_next_available[(edge[0], edge[1])]
        #             new_trees[edge[2]].append((edge[0], edge[1], next_free_time))
        #             links_next_available[(edge[0], edge[1])] = next_free_time + 1
        #             if next_free_time not in unused_links.keys():
        #                 unused_links[next_free_time] = copy.deepcopy(all_edge_list)
        #             unused_links[next_free_time].remove((edge[0], edge[1]))
        #     full_trees.append(new_trees)
        # # print("Total unused links")
        # # for key in unused_links.keys():
        # #     print("Timestamp " + str(key+1) + ": " + str(unused_links[key]))
        # partial_trees = []
        # total_partial_trees = self.args.total_partial_trees
        # self.total_partial_trees = total_partial_trees
        # data_partial_tree = math.ceil(self.number_of_nodes / 2)
        # first_link = (1, 0)
        # self.timesteps = 0
        # for cnt in range(total_partial_trees):
        #     new_trees = {}
        #     new_trees[0] = []
        #     threshold = links_next_available[first_link]
        #     new_trees[self.number_of_nodes-1] = []
        #     for timestep in time_relative_links_last.keys():
        #         edges_in_timestep = time_relative_links_last[timestep]
        #         for edge in edges_in_timestep:
        #             for d in range(data_partial_tree):
        #                 next_free_time = links_next_available[(edge[0], edge[1])]
        #                 if threshold > next_free_time:
        #                     next_free_time = threshold
        #                 new_trees[edge[2]].append((edge[0], edge[1], next_free_time))
        #                 if next_free_time > self.timesteps:
        #                     self.timesteps = next_free_time
        #                 links_next_available[(edge[0], edge[1])] = next_free_time + 1
        #                 if next_free_time not in unused_links.keys():
        #                     unused_links[next_free_time] = copy.deepcopy(all_edge_list)
        #                 unused_links[next_free_time].remove((edge[0], edge[1]))
        #         threshold += data_partial_tree
        #     partial_trees.append(new_trees)
        # self.full_trees = full_trees
        # self.partial_trees = partial_trees
        # self.timesteps += 1
        # print("Total unused links")
        # for key in unused_links.keys():
        #     print("Timestamp " + str(key+1) + ": " + str(unused_links[key]))
    # def compute_trees(self, kary=None, alternate=True, sort=False, verbose=False)

    def get_mapped_dependency(self, mapping, tree, source):
        dependencies = []
        for dep in self.trees_children[tree][source]:
            dependencies.append(mapping[dep])
        return dependencies

    def get_ag_mapped_dependency(self, mapping, tree, source):
        dependencies = []
        if self.trees_parent[tree][source] is not None:
            dependencies.append(mapping[self.trees_parent[tree][source]])
        return dependencies

    def get_current_max_timestep(self, edge_dict):
        max_timestep = 0
        for key in edge_dict.keys():
            if edge_dict[key] > max_timestep:
                max_timestep = edge_dict[key]
        return max_timestep

    def get_start_time(self, edge_dict, source, dest, dependencies):
        max_dep_time = 0
        for dep in dependencies:
            if edge_dict[(dep, source)] > max_dep_time:
                max_dep_time = edge_dict[(dep, source)]
        if max_dep_time > edge_dict[(source, dest)]:
            return max_dep_time
        else:
            return edge_dict[(source, dest)]

    def update_rs_final_dep(self, root, mapping, order, chunk_id):
        mapped_dependencies = self.get_mapped_dependency(mapping, root, root)
        if order == 0:
            if mapping[root] not in self.rs1_final_dep.keys():
                self.rs1_final_dep[mapping[root]] = []
            self.rs1_final_dep[mapping[root]].append((chunk_id, mapped_dependencies))
        else:
            if mapping[root] not in self.rs2_final_dep.keys():
                self.rs2_final_dep[mapping[root]] = []
            self.rs2_final_dep[mapping[root]].append((chunk_id, mapped_dependencies))

    def add_reduce_scatter(self, mapping, total_multiplied, chunk_id, total_message, order, is_partial):
        if is_partial:
            updated_relative_links = self.time_relative_links_last
        else:
            updated_relative_links = self.time_relative_links
        for key in sorted(updated_relative_links.keys(), reverse=True):
            for edge in updated_relative_links[key]:
                link = (mapping[edge[0]], mapping[edge[1]])
                if link not in self.hierarchical_rs_schedule.keys():
                    self.hierarchical_rs_schedule[link] = []
                mapped_dependencies = self.get_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[0])
                source_ni = self.get_ni(mapping[edge[0]], mapping[edge[1]])
                target_ni = self.get_ni(mapping[edge[1]], mapping[edge[0]])
                tree = mapping[edge[2]]
                if link not in self.edge_dict.keys():
                    self.edge_dict[link] = 0
                start_time = self.get_start_time(self.edge_dict, mapping[edge[0]], mapping[edge[1]], mapped_dependencies)
                self.hierarchical_rs_schedule[link].append((tree, chunk_id, mapped_dependencies, total_message,
                                                            total_multiplied, start_time, start_time + total_multiplied - 1,
                                                            order, source_ni, target_ni))
                self.edge_dict[link] = start_time + total_multiplied
        if is_partial:
            for root in self.partial_tree_roots:
                self.update_rs_final_dep(root, mapping, order, chunk_id)
        else:
            for root in self.full_tree_roots:
                self.update_rs_final_dep(root, mapping, order, chunk_id)

    def add_all_gather(self, mapping, total_multiplied, chunk_id, total_message, order, is_partial):
        if is_partial:
            updated_relative_links = self.time_relative_links_last
        else:
            updated_relative_links = self.time_relative_links
        for key in sorted(updated_relative_links.keys()):
            for edge in updated_relative_links[key]:
                link = (mapping[edge[1]], mapping[edge[0]])
                if link not in self.hierarchical_ag_schedule.keys():
                    self.hierarchical_ag_schedule[link] = []
                mapped_dependencies = self.get_ag_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[1])
                source_ni = self.get_ni(mapping[edge[1]], mapping[edge[0]])
                target_ni = self.get_ni(mapping[edge[0]], mapping[edge[1]])
                tree = mapping[edge[2]]
                if link not in self.edge_dict_ag.keys():
                    self.edge_dict_ag[link] = 0
                start_time = self.get_start_time(self.edge_dict_ag, mapping[edge[1]], mapping[edge[0]], mapped_dependencies)
                self.hierarchical_ag_schedule[link].append((tree, chunk_id, mapped_dependencies, total_message,
                                                                total_multiplied, start_time, start_time + total_multiplied - 1, order,
                                                                source_ni, target_ni))
                self.edge_dict_ag[link] = self.edge_dict_ag[link] + total_multiplied

    # def add_reduce_scatter_full(self, mapping, is_first, total_multiplied, chunk_id, total_message, order):
    #     if is_first:
    #         # TODO: validate is_first logic in full
    #         max_timestep = self.get_current_max_timestep(self.edge_dict)
    #         track = 0
    #         for key in sorted(self.updated_time_relative_links.keys(), reverse=True):
    #             for edge in self.updated_time_relative_links[key]:
    #                 if (mapping[edge[0]], mapping[edge[1]]) not in self.hierarchical_rs_schedule.keys():
    #                     self.hierarchical_rs_schedule[(mapping[edge[0]], mapping[edge[1]])] = []
    #                 mapped_dependencies = self.get_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[0])
    #                 source_ni = self.get_ni_v2(mapping[edge[0]], mapping[edge[1]])
    #                 target_ni = self.get_ni_v2(mapping[edge[1]], mapping[edge[0]])
    #                 self.hierarchical_rs_schedule[(mapping[edge[0]], mapping[edge[1]])].append((mapping[edge[2]], chunk_id, mapped_dependencies, total_message, total_multiplied, max_timestep + total_multiplied * track, max_timestep + total_multiplied * (track + 1) - 1, order, source_ni, target_ni))
    #                 self.edge_dict[(mapping[edge[0]], mapping[edge[1]])] = max_timestep + total_multiplied * (track+1) - 1
    #             track += 1
    #     else:
    #         for key in sorted(self.updated_time_relative_links.keys(), reverse=True):
    #             for edge in self.updated_time_relative_links[key]:
    #                 mapped_dependencies = self.get_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[0])
    #                 source_ni = self.get_ni_v2(mapping[edge[0]], mapping[edge[1]])
    #                 target_ni = self.get_ni_v2(mapping[edge[1]], mapping[edge[0]])
    #                 self.hierarchical_rs_schedule[(mapping[edge[0]], mapping[edge[1]])].append((mapping[edge[2]], chunk_id, mapped_dependencies, total_message, total_multiplied, self.edge_dict[(mapping[edge[0]], mapping[edge[1]])] + 1, self.edge_dict[(mapping[edge[0]], mapping[edge[1]])] + total_multiplied, order, source_ni, target_ni))
    #                 self.edge_dict[(mapping[edge[0]], mapping[edge[1]])] = self.edge_dict[(mapping[edge[0]], mapping[edge[1]])] + total_multiplied
    #     for root in self.full_tree_roots:
    #         mapped_dependencies = self.get_mapped_dependency(mapping, root, root)
    #         if order == 0:
    #             if mapping[root] not in self.rs1_final_dep.keys():
    #                 self.rs1_final_dep[mapping[root]] = []
    #             self.rs1_final_dep[mapping[root]].append((chunk_id, mapped_dependencies))
    #         else:
    #             if mapping[root] not in self.rs2_final_dep.keys():
    #                 self.rs2_final_dep[mapping[root]] = []
    #             self.rs2_final_dep[mapping[root]].append((chunk_id, mapped_dependencies))



    # def add_ag_partial(self, mapping, is_first, total_multiplied, chunk_id, total_message, order):
    #     if is_first:
    #         # TODO: validate is_first logic in partial
    #         max_timestep = 0
    #         for key in self.edge_dict_ag.keys():
    #             if self.edge_dict_ag[key] > max_timestep:
    #                 max_timestep = self.edge_dict_ag[key]
    #         track = 0
    #         for key in sorted(self.updated_time_relative_links_last.keys()):
    #             for edge in self.updated_time_relative_links_last[key]:
    #                 if (mapping[edge[1]], mapping[edge[0]]) not in self.hierarchical_ag_schedule.keys():
    #                     self.hierarchical_ag_schedule[(mapping[edge[1]], mapping[edge[0]])] = []
    #                 mapped_dependencies = self.get_ag_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[1])
    #                 source_ni = self.get_ni_v2(mapping[edge[1]], mapping[edge[0]])
    #                 target_ni = self.get_ni_v2(mapping[edge[0]], mapping[edge[1]])
    #                 self.hierarchical_ag_schedule[(mapping[edge[1]], mapping[edge[0]])].append((mapping[edge[2]], chunk_id, mapped_dependencies, total_message, total_multiplied, max_timestep + total_multiplied * track, max_timestep + total_multiplied * (track + 1) - 1, order, source_ni, target_ni))
    #                 self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] = total_multiplied * (track+1) - 1
    #             track += 1
    #     else:
    #         for key in sorted(self.updated_time_relative_links_last.keys(),):
    #             for edge in self.updated_time_relative_links_last[key]:
    #                 # if (edge[0], edge[1]) not in self.reduce_scatter_schedule_hierarchical.keys():
    #                 #     self.reduce_scatter_schedule_hierarchical[(edge[0], edge[1])] = []
    #                 mapped_dependencies = self.get_ag_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[1])
    #                 source_ni = self.get_ni_v2(mapping[edge[1]], mapping[edge[0]])
    #                 target_ni = self.get_ni_v2(mapping[edge[0]], mapping[edge[1]])
    #                 self.hierarchical_ag_schedule[(mapping[edge[1]], mapping[edge[0]])].append((mapping[edge[2]], chunk_id, mapped_dependencies, total_message, total_multiplied, self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] + 1, self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] + total_multiplied, order, source_ni, target_ni))
    #                 self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] = self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] + total_multiplied
    #
    #
    # def add_ag_full(self, mapping, is_first, total_multiplied, chunk_id, total_message, order):
    #     if is_first:
    #         # TODO: validate is_first logic in full
    #         max_timestep = 0
    #         for key in self.edge_dict_ag.keys():
    #             if self.edge_dict_ag[key] > max_timestep:
    #                 max_timestep = self.edge_dict_ag[key]
    #         track = 0
    #         for key in sorted(self.updated_time_relative_links.keys()):
    #             for edge in self.updated_time_relative_links[key]:
    #                 if (mapping[edge[1]], mapping[edge[0]]) not in self.hierarchical_ag_schedule.keys():
    #                     self.hierarchical_ag_schedule[(mapping[edge[1]], mapping[edge[0]])] = []
    #                 mapped_dependencies = self.get_ag_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[1])
    #                 source_ni = self.get_ni_v2(mapping[edge[1]], mapping[edge[0]])
    #                 target_ni = self.get_ni_v2(mapping[edge[0]], mapping[edge[1]])
    #                 self.hierarchical_ag_schedule[(mapping[edge[1]], mapping[edge[0]])].append((mapping[edge[2]], chunk_id, mapped_dependencies, total_message, total_multiplied, max_timestep + total_multiplied * track, max_timestep + total_multiplied * (track + 1) - 1, order, source_ni, target_ni))
    #                 self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] = max_timestep + total_multiplied * (track+1) - 1
    #             track += 1
    #     else:
    #         for key in sorted(self.updated_time_relative_links.keys()):
    #             for edge in self.updated_time_relative_links[key]:
    #                 mapped_dependencies = self.get_ag_mapped_dependency(mapping=mapping, tree=edge[2], source=edge[1])
    #                 source_ni = self.get_ni_v2(mapping[edge[1]], mapping[edge[0]])
    #                 target_ni = self.get_ni_v2(mapping[edge[0]], mapping[edge[1]])
    #                 self.hierarchical_ag_schedule[(mapping[edge[1]], mapping[edge[0]])].append((mapping[edge[2]], chunk_id, mapped_dependencies, total_message, total_multiplied, self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] + 1, self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] + total_multiplied, order, source_ni, target_ni))
    #                 self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] = self.edge_dict_ag[(mapping[edge[1]], mapping[edge[0]])] + total_multiplied

    # def get_ni(self, source_node, target_node):
    #     if target_node == source_node + 1:
    #         return 0
    #     elif target_node == source_node - 1:
    #         return 1
    #     else:
    #         raise RuntimeError('Error: NI info is wrong')

    def get_ni(self, source_node, target_node):
        if target_node == source_node - 1:
            return 0
        elif target_node == source_node + 1:
            return 1
        elif target_node == source_node - self.per_dim_nodes:
            return 2
        elif target_node == source_node + self.per_dim_nodes:
            return 3
        else:
            raise RuntimeError('Error: NI info is wrong')

    # def generate_mapping(self):
    #     dim_x_mapping = []
    #     for i in range(self.number_of_nodes):
    #         mapping = {}
    #         for j in range(self.number_of_nodes):
    #             mapping[self.number_of_nodes * i + j] = j
    #         dim_x_mapping.append(mapping)
    #     dim_y_mapping = []
    #     for i in range(self.number_of_nodes):
    #         mapping = {}
    #         for j in range(self.number_of_nodes):
    #             mapping[self.number_of_nodes * j + i] = j
    #         dim_y_mapping.append(mapping)
    #     return dim_x_mapping, dim_y_mapping

    def generate_mapping(self):
        dim_x_mapping = []
        for i in range(self.per_dim_nodes):
            mapping = {}
            for j in range(self.per_dim_nodes):
                mapping[j] = self.per_dim_nodes * i + j
            dim_x_mapping.append(mapping)
        dim_y_mapping = []
        for i in range(self.per_dim_nodes):
            mapping = {}
            for j in range(self.per_dim_nodes):
                mapping[j] = self.per_dim_nodes * j + i
            dim_y_mapping.append(mapping)
        return dim_x_mapping, dim_y_mapping

    # def get_reverse_mapping(self, mapping):
    #     reverse_mapping = {}
    #     for key in mapping:
    #         reverse_mapping[mapping[key]] = key
    #     return reverse_mapping

    # def update_rs_schedule(self, mapping, rs_schedule):
    #     updated_rs_schedule = {}
    #     reverse_mapping = self.get_reverse_mapping(mapping)
    #     for node in rs_schedule.keys():
    #         node_schedule = rs_schedule[node]
    #         updated_node_schedule = {}
    #         for timestep in node_schedule.keys():
    #             timestep_schedule = node_schedule[timestep]
    #             updated_timestep_schedule = {}
    #             for tree in timestep_schedule.keys():
    #                 edge = timestep_schedule[tree]
    #                 parent = edge[0][0]
    #                 updated_timestep_schedule[reverse_mapping[tree]] = ((reverse_mapping[parent], edge[0][1]), copy.deepcopy(edge[1]), edge[2], edge[3])
    #             updated_node_schedule[timestep] = updated_timestep_schedule
    #         updated_rs_schedule[reverse_mapping[node]] = updated_node_schedule
    #     return updated_rs_schedule

    # def update_ag_schedule(self, mapping, ag_schedule):
    #     updated_ag_schedule = {}
    #     reverse_mapping = self.get_reverse_mapping(mapping)
    #     for node in ag_schedule.keys():
    #         node_schedule = ag_schedule[node]
    #         updated_node_schedule = {}
    #         for timestep in node_schedule.keys():
    #             timestep_schedule = node_schedule[timestep]
    #             updated_timestep_schedule = {}
    #             for tree in timestep_schedule.keys():
    #                 edge = timestep_schedule[tree]
    #                 updated_send_list = []
    #                 for t in edge[0]:
    #                     parent = t[0]
    #                     updated_send_list.append((reverse_mapping[parent], t[1]))
    #                 updated_timestep_schedule[reverse_mapping[tree]] = (updated_send_list, copy.deepcopy(edge[1]), edge[2], edge[3])
    #             updated_node_schedule[timestep] = updated_timestep_schedule
    #         updated_ag_schedule[reverse_mapping[node]] = updated_node_schedule
    #     return updated_ag_schedule

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

    def check_timestep_ordering(self):
        for link in self.hierarchical_rs_schedule.keys():
            self.check_per_link_timestep_ordering(self.hierarchical_rs_schedule[link])


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
        for root in range(self.per_dim_nodes):
            self.trees_parent[root] = {}
            self.trees_parent[root][root] = None
            self.trees_children[root] = {}
            for node in range(self.per_dim_nodes):
                self.trees_children[root][node] = []
            for edge in self.template_trees[root]:
                child = edge[0]
                parent = edge[1]
                self.trees_parent[root][child] = parent
                self.trees_children[root][parent].append(child)

        # # total_timestep = self.per_dim_nodes - 2
        # updated_time_relative_links_last = {}
        # # updated_ag_time_relative_links_last = {}
        # for key in self.time_relative_links_last.keys():
        #     updated_time_relative_links_last[key] = []
        #     # updated_ag_time_relative_links_last[total_timestep - key] = []
        #     for edge in self.time_relative_links_last[key]:
        #         updated_time_relative_links_last[key].append((edge[0], edge[1], edge[2]))
        #         # updated_ag_time_relative_links_last[total_timestep - key].append((edge[0], edge[1], edge[2]))
        # self.updated_time_relative_links_last = updated_time_relative_links_last
        # # self.updated_ag_time_relative_links_last = updated_ag_time_relative_links_last
        #
        # updated_time_relative_links = {}
        # # updated_ag_time_relative_links = {}
        # for key in self.time_relative_links.keys():
        #     updated_time_relative_links[key] = []
        #     # updated_ag_time_relative_links[total_timestep - key] = []
        #     for edge in self.time_relative_links[key]:
        #         updated_time_relative_links[key].append((edge[0], edge[1], edge[2]))
        #         # updated_ag_time_relative_links[total_timestep - key].append((edge[0], edge[1], edge[2]))
        # self.updated_time_relative_links = updated_time_relative_links
        # # self.updated_ag_time_relative_links = updated_ag_time_relative_links

        dim_x_mapping, dim_y_mapping = self.generate_mapping()
        partial_dim_x_mapping = []
        partial_dim_x_mapping.append(dim_x_mapping[0])
        partial_dim_x_mapping.append(dim_x_mapping[-1])
        partial_dim_y_mapping = []
        partial_dim_y_mapping.append(dim_y_mapping[0])
        partial_dim_y_mapping.append(dim_y_mapping[-1])

        ## Type 1 dnd type 2: First dim reduce scatter with partial trees and full trees
        for mapping in dim_x_mapping:
            for i in range(self.total_partial_trees):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=self.args.total_multiplied, chunk_id=i,
                                        total_message=self.args.partial_tree_message_rs1, order=0,
                                        is_partial=True)
            for i in range(self.total_full_trees):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=1, chunk_id=self.total_partial_trees + i,
                                        total_message=self.args.full_tree_message_rs1, order=0,
                                        is_partial=False)
        for mapping in dim_y_mapping:
            for i in range(self.total_partial_trees):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=self.args.total_multiplied,
                                        chunk_id=self.args.per_dim_chunks+i,
                                        total_message=self.args.partial_tree_message_rs1, order=0,
                                        is_partial=True)
            for i in range(self.total_full_trees):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=1,
                                        chunk_id=self.args.per_dim_chunks+self.total_partial_trees+i,
                                        total_message=self.args.full_tree_message_rs1, order=0,
                                        is_partial=False)

        ## Type 3: Second dim reduce scatter for first dim full trees
        chunk_id_start = self.args.per_dim_chunks - self.args.total_full_trees
        for mapping in dim_y_mapping:
            for i in range(self.total_full_trees):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start + i,
                                        total_message=self.args.full_tree_message_rs2_for_full_tree, order=1,
                                        is_partial=False)
        chunk_id_start = 2 * self.args.per_dim_chunks - self.args.total_full_trees
        for mapping in dim_x_mapping:
            for i in range(self.total_full_trees):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start + i,
                                        total_message=self.args.full_tree_message_rs2_for_full_tree, order=1,
                                        is_partial=False)

        ## Type 4 and type 5: Second dim reduce scatter for first dim partial trees with partial trees and full trees
        second_dim_partial_tree = self.total_partial_trees - self.total_full_trees
        if self.total_partial_trees >= self.total_full_trees:
            second_dim_full_tree_2 = self.total_full_trees
            chunk_id_start = self.total_partial_trees - self.total_full_trees
        else:
            second_dim_full_tree_2 = self.total_partial_trees
            chunk_id_start = 0
        for mapping in partial_dim_y_mapping:
            for i in range(second_dim_partial_tree):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=self.args.total_multiplied, chunk_id=i,
                                        total_message=self.args.partial_tree_message_rs2, order=1,
                                        is_partial=True)
            for i in range(second_dim_full_tree_2):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start + i,
                                        total_message=self.args.full_tree_message_rs2_for_partial_tree, order=1,
                                        is_partial=False)
        chunk_id_start_x = self.args.per_dim_chunks + chunk_id_start
        for mapping in partial_dim_x_mapping:
            for i in range(second_dim_partial_tree):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=self.args.total_multiplied,
                                        chunk_id=self.args.per_dim_chunks + i,
                                        total_message=self.args.partial_tree_message_rs2, order=1,
                                        is_partial=True)
            for i in range(second_dim_full_tree_2):
                self.add_reduce_scatter(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start_x + i,
                                        total_message=self.args.full_tree_message_rs2_for_partial_tree, order=1,
                                        is_partial=False)

        ## Type 3: Second dim all gather for first dim full trees
        chunk_id_start = self.args.per_dim_chunks - self.args.total_full_trees
        for mapping in dim_y_mapping:
            for i in range(self.total_full_trees):
                self.add_all_gather(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start + i,
                                    total_message=self.args.full_tree_message_rs2_for_full_tree, order=0, is_partial=False)
        chunk_id_start = 2 * self.args.per_dim_chunks - self.args.total_full_trees
        for mapping in dim_x_mapping:
            for i in range(self.total_full_trees):
                self.add_all_gather(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start + i,
                                    total_message=self.args.full_tree_message_rs2_for_full_tree, order=0, is_partial=False)

        ## Type 4 and type 5: Second dim all-gather for first dim partial trees with full trees and partial trees
        second_dim_partial_tree = self.total_partial_trees - self.total_full_trees
        if self.total_partial_trees >= self.total_full_trees:
            second_dim_full_tree_2 = self.total_full_trees
            chunk_id_start = self.total_partial_trees - self.total_full_trees
        else:
            second_dim_full_tree_2 = self.total_partial_trees
            chunk_id_start = 0
        # chunk_id_start = self.total_partial_trees - self.total_full_trees
        for mapping in partial_dim_y_mapping:
            for i in range(second_dim_full_tree_2):
                self.add_all_gather(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start + i,
                                    total_message=self.args.full_tree_message_rs2_for_partial_tree, order=0,
                                    is_partial=False)
            for i in range(second_dim_partial_tree):
                self.add_all_gather(mapping=mapping, total_multiplied=self.args.total_multiplied, chunk_id=i,
                                    total_message=self.args.partial_tree_message_rs2, order=0, is_partial=True)
        # chunk_id_start = self.args.per_dim_chunks + self.total_partial_trees - self.total_full_trees
        chunk_id_start_x = self.args.per_dim_chunks + chunk_id_start
        for mapping in partial_dim_x_mapping:
            for i in range(second_dim_full_tree_2):
                self.add_all_gather(mapping=mapping, total_multiplied=1, chunk_id=chunk_id_start_x + i,
                                    total_message=self.args.full_tree_message_rs2_for_partial_tree, order=0, is_partial=False)

            for i in range(second_dim_partial_tree):
                self.add_all_gather(mapping=mapping, total_multiplied=self.args.total_multiplied,
                                    chunk_id=self.args.per_dim_chunks + i,
                                    total_message=self.args.partial_tree_message_rs2, order=0, is_partial=True)

        ## Type 1 dnd type 2: First dim all gather with full trees and partial trees
        for mapping in dim_x_mapping:
            for i in range(self.total_full_trees):
                self.add_all_gather(mapping=mapping, total_multiplied=1, chunk_id=self.total_partial_trees + i,
                                    total_message=self.args.full_tree_message_rs1, order=1, is_partial=False)
            for i in range(self.total_partial_trees):
                self.add_all_gather(mapping=mapping, total_multiplied=self.args.total_multiplied, chunk_id=i,
                                    total_message=self.args.partial_tree_message_rs1, order=1, is_partial=True)
        for mapping in dim_y_mapping:
            for i in range(self.total_full_trees):
                self.add_all_gather(mapping=mapping, total_multiplied=1,
                                    chunk_id=self.args.per_dim_chunks+self.total_partial_trees+i,
                                    total_message=self.args.full_tree_message_rs1, order=1, is_partial=False)
            for i in range(self.total_partial_trees):
                self.add_all_gather(mapping=mapping, total_multiplied=self.args.total_multiplied,
                                    chunk_id=self.args.per_dim_chunks+i,
                                    total_message=self.args.partial_tree_message_rs1, order=1, is_partial=True)

        self.check_timestep_ordering()

        self.final_reduce_scatter_schedule = {}
        message_dict = {}
        total_rs_message = 0
        for i in range(self.args.num_hmcs):
            self.final_reduce_scatter_schedule[i] = {}
            message_dict[i] = 0
        for link in self.edge_dict.keys():
            self.final_reduce_scatter_schedule[link[0]][link[1]] = []
        for link in self.hierarchical_rs_schedule.keys():
            source = link[0]
            dest = link[1]
            for schedule in self.hierarchical_rs_schedule[link]:
                tree_id = schedule[0]
                chunk_id = schedule[1]
                dependencies = schedule[2]
                total_messages = schedule[3]
                order = schedule[7]
                source_ni = schedule[8]
                dest_ni = schedule[9]
                message_dict[source] = message_dict[source] + total_messages
                total_rs_message += total_messages
                self.final_reduce_scatter_schedule[source][dest].append((tree_id, chunk_id, dependencies, total_messages, order, source_ni, dest_ni))
        self.reduce_scatter_schedule = self.final_reduce_scatter_schedule

        # for i in range(self.args.num_hmcs):
        #     print("Reduce scatter ")
        #     print("For HMC " + str(i) + " total message " + str(message_dict[i]))

        total_ag_message = 0
        self.final_ag_schedule = {}
        for i in range(self.args.num_hmcs):
            self.final_ag_schedule[i] = {}
        for link in self.edge_dict.keys():
            self.final_ag_schedule[link[0]][link[1]] = []
        for link in self.hierarchical_ag_schedule.keys():
            source = link[0]
            dest = link[1]
            for schedule in self.hierarchical_ag_schedule[link]:
                tree_id = schedule[0]
                chunk_id = schedule[1]
                dependencies = schedule[2]
                total_messages = schedule[3]
                order = schedule[7]
                source_ni = schedule[8]
                dest_ni = schedule[9]
                message_dict[source] = message_dict[source] + total_messages
                # if source == 10:
                #     print("Source " + str(source) + " dest " + str(dest) + " sending " + str(total_messages) + " for chunk " + str(chunk_id) + " in tree " + str(tree_id))
                total_ag_message += total_messages
                self.final_ag_schedule[source][dest].append(
                    (tree_id, chunk_id, dependencies, total_messages, order, source_ni, dest_ni))
        self.all_gather_schedule = self.final_ag_schedule
        assert total_rs_message == total_ag_message

        # for i in range(self.args.num_hmcs):
        #     print("All gather ")
        #     print("For HMC " + str(i) + " total message " + str(message_dict[i]))

        #TODO: How to aggregate, how to resolve dependency, how to make sure when to send data, which information to propagate



        # for mapping in dim_y_mapping:
        #     for i in range(self.total_full_trees):
        #         self.add_reduce_scatter_full(mapping=mapping, is_first=False, total_multiplied=1,
        #                                      chunk_id=self.total_partial_trees + i, total_message=1)



        # self.add_reduce_scatter_partial(mapping=dim_x_mapping[0], is_first=True, total_multiplied=2, chunk_id=0,
        #                                 total_message=10)
        # self.add_reduce_scatter_partial(mapping=dim_x_mapping[0], is_first=False, total_multiplied=2, chunk_id=1,
        #                                 total_message=10)
        # self.add_reduce_scatter_partial(mapping=dim_x_mapping[1], is_first=True, total_multiplied=2, chunk_id=0,
        #                                 total_message=10)
        # self.add_reduce_scatter_partial(mapping=dim_x_mapping[1], is_first=False, total_multiplied=2, chunk_id=1,
        #                                 total_message=10)
        # self.add_reduce_scatter_full(mapping=dim_x_mapping[0], is_first=False, total_multiplied=1, chunk_id=2,
        #                              total_message=5)
        # self.add_reduce_scatter_full(mapping=dim_x_mapping[0], is_first=False, total_multiplied=1, chunk_id=3,
        #                              total_message=5)

        # initialize the schedules
        # reduce_scatter_schedule = {}
        # all_gather_schedule = {}
        #
        # # construct schedules for each node from trees
        # for node in range(self.number_of_nodes):
        #     reduce_scatter_schedule[node] = {}
        #     all_gather_schedule[node] = {}
        #
        # # reduce_scatter_ni = np.zeros((self.number_of_nodes, self.timesteps), dtype=int)
        # # all_gather_ni = np.zeros((self.number_of_nodes, self.timesteps), dtype=int)
        # for t in range(self.total_full_trees):
        #     for root in range(self.number_of_nodes):
        #         for edge in self.full_trees[t][root]:
        #             # reduce-scatter
        #             rs_child = edge[0]
        #             rs_parent = edge[1]
        #             rs_timestep = self.timesteps - edge[2] - 1
        #             chunk_index = self.total_full_trees + self.total_partial_trees - t
        #
        #             # send from rs_child to rs_parent for tree root at rs_timestep
        #             if rs_timestep not in reduce_scatter_schedule[rs_child].keys():
        #                 reduce_scatter_schedule[rs_child][rs_timestep] = {}
        #             flow_children = [(root, child) for child in self.trees_children[root][rs_child]]
        #             # reduce_scatter_schedule_full_tree[rs_child][rs_timestep][root] = (rs_parent, flow_children, 1, rs_timestep)
        #             reduce_scatter_schedule[rs_child][rs_timestep][root] = ((rs_parent, self.get_ni(source_node=rs_child, target_node=rs_parent), chunk_index), flow_children, 1, rs_timestep)
        #             # reduce_scatter_ni[rs_parent][rs_timestep] = (reduce_scatter_ni[rs_parent][
        #             #                                                  rs_timestep] + 1) % self.args.radix
        #
        #             # all-gather
        #             ag_child = edge[0]
        #             ag_parent = edge[1]
        #             ag_timestep = edge[2]
        #
        #             # send from ag_parent to ag_child for tree root at ag_timestep
        #             if ag_timestep not in all_gather_schedule[ag_parent].keys():
        #                 all_gather_schedule[ag_parent][ag_timestep] = {}
        #             if root not in all_gather_schedule[ag_parent][ag_timestep].keys():
        #                 if ag_parent == root:
        #                     assert self.trees_parent[root][ag_parent] == None
        #                     all_gather_schedule[ag_parent][ag_timestep][root] = (
        #                         [], None, 1, self.timesteps + ag_timestep + 1)
        #                 else:
        #                     all_gather_schedule[ag_parent][ag_timestep][root] = (
        #                         [], (root, self.trees_parent[root][ag_parent]), 1, ag_timestep + self.timesteps + 1)
        #             # all_gather_schedule_full_tree[ag_parent][ag_timestep][root][0].append(ag_child)
        #             all_gather_schedule[ag_parent][ag_timestep][root][0].append((ag_child, self.get_ni(source_node=rs_parent, target_node=rs_child), chunk_index))
        #             # all_gather_ni[ag_child][ag_timestep] = (all_gather_ni[ag_child][ag_timestep] + 1) % self.args.radix
        #
        # print(all_gather_schedule)
        # partial_tree_roots = [0, self.number_of_nodes-1]
        # for t in range(self.total_partial_trees):
        #     for root in partial_tree_roots:
        #         # ni_selector = {}
        #         for edge in self.partial_trees[t][root]:
        #             # reduce-scatter
        #             rs_child = edge[0]
        #             rs_parent = edge[1]
        #             rs_timestep = self.timesteps - edge[2] - 1
        #             chunk_index = self.total_partial_trees - t
        #
        #             # send from rs_child to rs_parent for tree root at rs_timestep
        #             if rs_timestep not in reduce_scatter_schedule[rs_child].keys():
        #                 reduce_scatter_schedule[rs_child][rs_timestep] = {}
        #             flow_children = [(root, child) for child in self.trees_children[root][rs_child]]
        #             reduce_scatter_schedule[rs_child][rs_timestep][root] = ((rs_parent, self.get_ni(source_node=rs_child, target_node=rs_parent), chunk_index), flow_children, 1, rs_timestep)
        #                 # ni_selector[(rs_child, rs_parent)] = reduce_scatter_ni[rs_parent][rs_timestep]
        #                 # reduce_scatter_ni[rs_parent][rs_timestep] = (reduce_scatter_ni[rs_parent][
        #                 #                                                  rs_timestep] + 1) % self.args.radix
        #
        #             # all-gather
        #             ag_child = edge[0]
        #             ag_parent = edge[1]
        #             ag_timestep = edge[2]
        #
        #             # send from ag_parent to ag_child for tree root at ag_timestep
        #             if ag_timestep not in all_gather_schedule[ag_parent].keys():
        #                 all_gather_schedule[ag_parent][ag_timestep] = {}
        #             if root not in all_gather_schedule[ag_parent][ag_timestep].keys():
        #                 if ag_parent == root:
        #                     assert self.trees_parent[root][ag_parent] == None
        #                     all_gather_schedule[ag_parent][ag_timestep][root] = (
        #                         [], None, 1, self.timesteps + ag_timestep + 1)
        #                 else:
        #                     all_gather_schedule[ag_parent][ag_timestep][root] = (
        #                         [], (root, self.trees_parent[root][ag_parent]), 1, ag_timestep + self.timesteps + 1)
        #             all_gather_schedule[ag_parent][ag_timestep][root][0].append(
        #                 (ag_child, self.get_ni(source_node=rs_parent, target_node=rs_child), chunk_index))
        #             # all_gather_ni[ag_child][ag_timestep] = (all_gather_ni[ag_child][ag_timestep] + 1) % self.args.radix
        # print(reduce_scatter_schedule)
        #
        # dim_x_mapping, dim_y_mapping = self.generate_mapping()
        #
        # dim_x_reduce_scatter_schedule = []
        # dim_x_all_gather_schedule = []
        # dim_x_reduce_scatter_schedule.append(reduce_scatter_schedule)
        # dim_x_all_gather_schedule.append(all_gather_schedule)
        # for mapping in dim_x_mapping:
        #     dim_x_reduce_scatter_schedule.append(self.update_rs_schedule(mapping, reduce_scatter_schedule))
        #     dim_x_all_gather_schedule.append(self.update_ag_schedule(mapping, all_gather_schedule))
        # dim_y_reduce_scatter_schedule = []
        # dim_y_all_gather_schedule = []
        # for mapping in dim_y_mapping:
        #     dim_y_reduce_scatter_schedule.append(self.update_rs_schedule(mapping, reduce_scatter_schedule))
        #     dim_y_all_gather_schedule.append(self.update_ag_schedule(mapping, all_gather_schedule))
        # # initialize the schedules
        # self.reduce_scatter_schedule = {}
        # self.all_gather_schedule = {}
        #
        # for node in range(self.network.nodes):
        #     self.reduce_scatter_schedule[node] = []
        #     self.all_gather_schedule[node] = []
        #     if verbose:
        #         print('Accelerator {}:'.format(node))
        #         print('  reduce-scatter schedule:')
        #     for timestep in range(self.timesteps):
        #         if timestep in reduce_scatter_schedule[node].keys():
        #             self.reduce_scatter_schedule[node].append(reduce_scatter_schedule[node][timestep])
        #             if verbose:
        #                 print('    timestep {}: {}'.format(timestep, reduce_scatter_schedule[node][timestep]))
        #         else:
        #             self.reduce_scatter_schedule[node].append(None)
        #             if verbose:
        #                 print('    timestep {}: no scheduled communication in this timestep'.format(timestep))
        #     flow_children = [(node, child) for child in self.trees_children[node][node]]
        #     self.reduce_scatter_schedule[node].append({node: ((None, None), flow_children, 0, self.timesteps)})
        #     if verbose:
        #         print('    root children: {}'.format(self.reduce_scatter_schedule[node][-1]))
        #
        #     if verbose:
        #         print('  all-gather schedule:')
        #     for timestep in range(self.timesteps):
        #         if timestep in all_gather_schedule[node].keys():
        #             self.all_gather_schedule[node].append(all_gather_schedule[node][timestep])
        #             if verbose:
        #                 print('    timestep {}: {}'.format(timestep, all_gather_schedule[node][timestep]))
        #         else:
        #             self.all_gather_schedule[node].append(None)
        #             if verbose:
        #                 print('    timestep {}: no scheduled communication in this timestep'.format(timestep))
        #
        # if verbose:
        #     print('\nSchedule Tables:')
        #     for node in range(self.network.nodes):
        #         print(' Accelerator {}:'.format(node))
        #         for timestep in range(self.timesteps):
        #             if self.reduce_scatter_schedule[node][timestep] == None:
        #                 print('   - NoOp')
        #             else:
        #                 for flow, schedule in self.reduce_scatter_schedule[node][timestep].items():
        #                     print('   - Reduce, FlowID {}, Parent {}, Children {}, Step {}'.format(flow, schedule[0][0],
        #                                                                                            [ele[1] for ele in
        #                                                                                             schedule[1]],
        #                                                                                            timestep))
        #
        #         for timestep in range(self.timesteps):
        #             if self.all_gather_schedule[node][timestep] == None:
        #                 print('   - NoOp')
        #             else:
        #                 for flow, schedule in self.all_gather_schedule[node][timestep].items():
        #                     if schedule[1] == None:
        #                         parent = 'nil'
        #                     else:
        #                         parent = schedule[1][1]
        #                     print('   - Gather, FlowID {}, Parent {}, Children {}, Step {}'.format(flow, parent,
        #                                                                                            [ele[0] for ele in
        #                                                                                             schedule[0]],
        #                                                                                            self.timesteps + timestep))
        #
        #     print('\nAggregation Table:')
        #     aggregation_table = {}
        #     for node in range(self.network.nodes):
        #         aggregation_table[node] = {}
        #
        #     for timestep in range(self.timesteps):
        #         for node in range(self.network.nodes):
        #             if self.reduce_scatter_schedule[node][timestep] != None:
        #                 for flow, schedule in self.reduce_scatter_schedule[node][timestep].items():
        #                     parent = schedule[0][0]
        #                     if timestep not in aggregation_table[parent].keys():
        #                         aggregation_table[parent][timestep] = {flow: [node]}
        #                     elif flow not in aggregation_table[parent][timestep]:
        #                         aggregation_table[parent][timestep][flow] = [node]
        #                     else:
        #                         aggregation_table[parent][timestep][flow].append(node)
        #
        #     for node in range(self.network.nodes):
        #         print(' Accelerator {}:'.format(node))
        #         for timestep in sorted(aggregation_table[node].keys()):
        #             for flow, children in aggregation_table[node][timestep].items():
        #                 print('   - FlowID {}, Children {}, Step {}'.format(flow, children, timestep))
        # print("Done")
    # def generate_schedule(self, verbose=False)


def main(args):
    # network = construct_network(args)
    # network.to_nodes[1].clear() # test no solution case

    allreduce = HierarchicalOverlapAllreduce(args, None)
    allreduce.compute_trees(verbose=args.verbose)
    # allreduce.generate_schedule(verbose=args.verbose)
    # allreduce.max_num_concurrent_flows()
    # if args.gendotfile:
    # allreduce.generate_ring_dotfile('ring.dot')
    #     allreduce.generate_trees_dotfile('ring_trees.dot')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--num-hmcs', default=6, type=int,
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
    parser.add_argument('--total-full-trees', default=3, type=int,
                        help='Total number of full trees in mesh')
    parser.add_argument('--total-partial-trees', default=2, type=int,
                        help='Total number of partial trees in mesh')

    args = parser.parse_args()

    main(args)
