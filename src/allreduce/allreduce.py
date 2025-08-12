import math
import os
from abc import ABC, abstractmethod


class Allreduce(ABC):
    def __init__(self, args, network):
        self.args = args
        self.network = network
        self.trees_rs = None
        self.trees_ag = None
        self.trees_parent_ag = None
        self.trees_children_rs = None
        self.timesteps_rs = None
        self.timesteps_ag = None
        self.reduce_scatter_schedule = {}
        self.all_gather_schedule = {}
        for source in range(self.args.num_hmcs):
            self.reduce_scatter_schedule[source] = {}
            self.all_gather_schedule[source] = {}
        self.max_tree_height_for_pipeline = None
        self.rs2_final_dep = {}
        self.tree_roots = None
        # self.chunk_roots = None
        self.time_relative_links_rs = None
        self.time_relative_links_ag = None

        # TODO: reduce-scatter and all-gather schedulues are merged into a unified
        # schedule, opcodes: {'Reduce', 'Gather', 'NOP'}
        self.collective_schedule = None
        self.current_trees = None

    '''
    compute_schedule() - computes spanning trees and schedule for the given network
    '''

    def build_trees(self, sort=True, verbose=False):
        self.args.saved_tree_name = '{}/src/SavedTrees/'.format(os.environ['SIMHOME']) + self.args.booksim_network + '/' + str(self.args.booksim_network) + "_" + str(self.args.allreduce) + "_" + str(self.args.num_hmcs)
        self.compute_trees(sort, verbose)
        # dot_file_name = '{}/src/dotFiles/'.format(os.environ['SIMHOME']) + self.args.booksim_network + '/' + self.args.booksim_network + '_' + self.args.allreduce + '_' + str(
        #     self.args.num_hmcs) + '_' + self.args.collective + '.dot'
        # self.generate_trees_dotfile(dot_file_name)

    def compute_schedule(self, sort=True, verbose=False):
        self.generate_schedule(verbose)

    '''
    compute_trees() - computes allreduce spanning trees for the given network
    '''

    @abstractmethod
    def compute_trees(self, sort=True, verbose=False):
        pass

    '''
    generate_schedule()
    @verbose: print the generated schedules

    desc - generate reduce_scatter_schedule and all_gather_schedule from trees
    '''

    @abstractmethod
    def generate_schedule(self, verbose=False):
        pass

    '''
    generate_trees_dotfile() - generate dotfile for computed trees
    @filename: name of dotfile
    '''

    @abstractmethod
    def generate_trees_dotfile(self, filename, verbose=False):
        pass

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

    def get_rs_dependency(self, tree, source):
        dependencies = []
        for dep in self.trees_children_rs[tree][source]:
            dependencies.append(dep)
        return dependencies

    def get_ag_dependency(self, tree, source):
        dependencies = []
        if self.trees_parent_ag[tree][source] is not None:
            dependencies.append(self.trees_parent_ag[tree][source])
        return dependencies

    def update_rs_final_dep(self, root, chunk_id):
        dependencies = self.get_rs_dependency(root, root)
        if root not in self.rs2_final_dep.keys():
            self.rs2_final_dep[root] = []
        self.rs2_final_dep[root].append((chunk_id, dependencies))

    def update_rs_final_dep_tacos(self, root, chunk_id):
        dependencies = self.get_rs_dependency(chunk_id, root)
        if root not in self.rs2_final_dep.keys():
            self.rs2_final_dep[root] = []
        self.rs2_final_dep[root].append((chunk_id, dependencies))

    def initiate_parent_children(self):
        self.trees_children_rs = {}
        self.trees_parent_ag = {}
        for root in self.tree_roots:
            self.trees_children_rs[root] = {}
            self.trees_parent_ag[root] = {}
            if self.args.allreduce == 'tacos':
                self.trees_parent_ag[root][root % self.args.num_hmcs] = None
            else:
                self.trees_parent_ag[root][root] = None
            if self.trees_rs is not None:
                for node in range(self.args.num_hmcs):
                    self.trees_children_rs[root][node] = []
                for edge in self.trees_rs[root]:
                    child = edge[0]
                    parent = edge[1]
                    self.trees_children_rs[root][parent].append(child)
            for edge in self.trees_ag[root]:
                child = edge[0]
                parent = edge[1]
                self.trees_parent_ag[root][child] = parent
        if self.trees_rs is not None:
            self.time_relative_links_rs = {}
            for key in self.trees_rs.keys():
                tree = self.trees_rs[key]
                for edge in tree:
                    time = edge[2] - 1
                    if time not in self.time_relative_links_rs.keys():
                        self.time_relative_links_rs[time] = []
                    if self.args.allreduce == 'alternate_2d_ring':
                        self.time_relative_links_rs[time].append((edge[0], edge[1], key, edge[3], edge[4]))
                    else:
                        self.time_relative_links_rs[time].append((edge[0], edge[1], key, edge[3]))
        self.time_relative_links_ag = {}
        for key in self.trees_ag.keys():
            tree = self.trees_ag[key]
            for edge in tree:
                time = edge[2] - 1
                if time not in self.time_relative_links_ag.keys():
                    self.time_relative_links_ag[time] = []
                if self.args.allreduce == 'alternate_2d_ring':
                    self.time_relative_links_ag[time].append((edge[0], edge[1], key, edge[3], edge[4]))
                else:
                    self.time_relative_links_ag[time].append((edge[0], edge[1], key, edge[3]))

    def add_reduce_scatter_schedule(self, chunk_id, total_message):
        for key in sorted(self.time_relative_links_rs.keys(), reverse=True):
            for edge in self.time_relative_links_rs[key]:
                source = edge[0]
                target = edge[1]
                tree = edge[2]
                second = edge[3]
                dependencies = self.get_rs_dependency(tree=tree, source=source)
                if self.args.booksim_network == 'mesh':
                    source_ni = self.get_ni(source, target)
                    target_ni = self.get_ni(target, source)
                else:
                    if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
                        topology = 'SM_Bi'
                    else:
                        topology = self.args.booksim_network
                    # source_ni, target_ni = self.get_source_dest_NI(source, target, self.args.booksim_network, second)
                    if self.args.booksim_network == 'kite' or self.args.booksim_network == 'dbutterfly' or self.args.booksim_network == 'kite_medium' or self.args.booksim_network == 'cmesh' or self.args.booksim_network == 'folded_torus':
                        source_ni = -1
                        target_ni = -1
                    else:
                        source_ni, target_ni = self.get_source_dest_NI(source, target, topology, second)
                if (target, second) not in self.reduce_scatter_schedule[source]:
                        self.reduce_scatter_schedule[source][(target, second)] = []
                if self.args.allreduce == 'alternate_2d_ring':
                    total_message = edge[4]
                if self.args.allreduce == 'tacos':
                    self.reduce_scatter_schedule[source][(target, second)].append((tree, tree, dependencies, total_message, 0, source_ni, target_ni))
                else:
                    self.reduce_scatter_schedule[source][(target, second)].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))
        if self.args.allreduce == 'tacos':
            for i, root in enumerate(self.tree_roots):
                self.update_rs_final_dep_tacos(root % self.args.num_hmcs, root)
        else:
            for root in self.tree_roots:
                self.update_rs_final_dep(root, chunk_id)

    def add_reduce_scatter_schedule_2d_ring(self, chunk_id, total_message):
        for key in sorted(self.time_relative_links_rs.keys()):
            for edge in self.time_relative_links_rs[key]:
                source = edge[1]
                target = edge[0]
                tree = edge[2]
                second = edge[3]
                dependencies = self.get_ag_dependency(tree=tree, source=source)
                if self.args.booksim_network == 'mesh':
                    source_ni = self.get_ni(source, target)
                    target_ni = self.get_ni(target, source)
                else:
                    source_ni, target_ni = self.get_source_dest_NI(source, target, self.args.booksim_network, second)
                if (target, second) not in self.reduce_scatter_schedule[source]:
                        self.reduce_scatter_schedule[source][(target, second)] = []
                if self.args.allreduce == 'alternate_2d_ring':
                    total_message = edge[4]
                self.reduce_scatter_schedule[source][(target, second)].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))
        for root in self.tree_roots:
            self.update_rs_final_dep(root, chunk_id)

    def add_all_gather_schedule(self, chunk_id, total_message):
        for key in sorted(self.time_relative_links_ag.keys()):
            for edge in self.time_relative_links_ag[key]:
                source = edge[1]
                target = edge[0]
                tree = edge[2]
                second = edge[3]
                dependencies = self.get_ag_dependency(tree=tree, source=source)
                if self.args.booksim_network == 'mesh':
                    source_ni = self.get_ni(source, target)
                    target_ni = self.get_ni(target, source)
                else:
                    if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
                        topology = 'SM_Bi'
                    else:
                        topology = self.args.booksim_network
                    # source_ni, target_ni = self.get_source_dest_NI(source, target, self.args.booksim_network, second)
                    if self.args.booksim_network == 'kite' or self.args.booksim_network == 'dbutterfly' or self.args.booksim_network == 'kite_medium' or self.args.booksim_network == 'cmesh' or self.args.booksim_network == 'folded_torus':
                        source_ni = -1
                        target_ni = -1
                    else:
                        source_ni, target_ni = self.get_source_dest_NI(source, target, topology, second)
                if (target, second) not in self.all_gather_schedule[source]:
                        self.all_gather_schedule[source][(target, second)] = []
                if self.args.allreduce == 'alternate_2d_ring':
                    total_message = edge[4]
                self.all_gather_schedule[source][(target, second)].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni, [0]))

    def get_ni(self, source_node, target_node):
        if target_node == source_node - 1:
            return 0
        elif target_node == source_node + 1:
            return 1
        elif target_node == source_node - self.args.per_dim_nodes:
            return 2
        elif target_node == source_node + self.args.per_dim_nodes:
            return 3
        else:
            raise RuntimeError('Error: NI info is wrong')

    def get_center_nodes(self):
        nodes_in_dimension = int(math.sqrt(self.args.num_hmcs))
        center_nodes = []
        border_nodes = []
        for node in range(self.args.num_hmcs):
            row = node // nodes_in_dimension
            col = node % nodes_in_dimension
            if (row == 0) or (col == 0) or (row == nodes_in_dimension - 1) or (col == nodes_in_dimension - 1):
                border_nodes.append(node)
            else:
                center_nodes.append(node)
        return border_nodes, center_nodes

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

    def get_distributed_border_nodes(self):
        nodes_in_dimension = int(math.sqrt(self.args.num_hmcs))

        top_border_nodes = []
        right_border_nodes = []
        bottom_border_nodes = []
        left_border_nodes = []
        for node in range(self.args.num_hmcs):
            row = node // nodes_in_dimension
            col = node % nodes_in_dimension
            if row == 0 and col == 0:
                top_border_nodes.append(node)
            elif row == 0 and col == nodes_in_dimension - 1:
                right_border_nodes.append(node)
            elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                bottom_border_nodes.append(node)
            elif row == nodes_in_dimension - 1 and col == 0:
                left_border_nodes.append(node)
            elif row == 0:
                top_border_nodes.append(node)
            elif col == nodes_in_dimension - 1:
                right_border_nodes.append(node)
            elif row == nodes_in_dimension - 1:
                bottom_border_nodes.append(node)
            elif col == 0:
                left_border_nodes.append(node)
        return top_border_nodes, right_border_nodes, bottom_border_nodes, left_border_nodes

    # TODO: Refactor this code and mmmerge with get_ni()
    def get_source_dest_NI(self, source_node, dest_node, topology, second=False):
        nodes_in_dimension = int(math.sqrt(self.args.num_hmcs))
        row = source_node // nodes_in_dimension
        col = source_node % nodes_in_dimension
        if topology == 'torus':
            mesh = False
        else:
            mesh = True

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
                dest_ni = 2
                src_ni = 0
            elif dest_node == east:
                dest_ni = 3
                src_ni = 1
            elif dest_node == south:
                dest_ni = 0
                src_ni = 2
            elif dest_node == west:
                dest_ni = 1
                src_ni = 3
        elif topology == 'SM_Uni':
            if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension - 1:
                if row == 0 and col == 0:
                    if dest_node == east and second:
                        dest_ni = 3
                        src_ni = 1
                    elif dest_node == east and not second:
                        dest_ni = 0
                        src_ni = 0
                    elif dest_node == south:
                        dest_ni = 0
                        src_ni = 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == 0 and col == nodes_in_dimension - 1:
                    if dest_node == south and second:
                        dest_ni = 0
                        src_ni = 2
                    elif dest_node == south and not second:
                        dest_ni = 1
                        src_ni = 1
                    elif dest_node == west:
                        dest_ni = 1
                        src_ni = 3
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                    if dest_node == west and second:
                        dest_ni = 1
                        src_ni = 3
                    elif dest_node == west and not second:
                        dest_ni = 2
                        src_ni = 2
                    elif dest_node == north:
                        dest_ni = 2
                        src_ni = 0
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == 0:
                    if dest_node == north and second:
                        dest_ni = 2
                        src_ni = 0
                    elif dest_node == north and not second:
                        dest_ni = 3
                        src_ni = 3
                    elif dest_node == east:
                        dest_ni = 3
                        src_ni = 1
                    else:
                        raise RuntimeError("Wrong dest node")
                else:
                    if row == 0:
                        if dest_node == east and second:
                            dest_ni = 3
                            src_ni = 1
                        elif dest_node == east and not second:
                            dest_ni = 0
                            src_ni = 0
                        elif dest_node == south:
                            dest_ni = 0
                            src_ni = 2
                        elif dest_node == west:
                            dest_ni = 1
                            src_ni = 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == nodes_in_dimension - 1:
                        if dest_node == south and second:
                            dest_ni = 0
                            src_ni = 2
                        elif dest_node == south and not second:
                            dest_ni = 1
                            src_ni = 1
                        elif dest_node == west:
                            dest_ni = 1
                            src_ni = 3
                        elif dest_node == north:
                            dest_ni = 2
                            src_ni = 0
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1:
                        if dest_node == west and second:
                            dest_ni = 1
                            src_ni = 3
                        elif dest_node == west and not second:
                            dest_ni = 2
                            src_ni = 2
                        elif dest_node == north:
                            dest_ni = 2
                            src_ni = 0
                        elif dest_node == east:
                            dest_ni = 3
                            src_ni = 1
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == 0:
                        if dest_node == north and second:
                            dest_ni = 2
                            src_ni = 0
                        elif dest_node == north and not second:
                            dest_ni = 3
                            src_ni = 3
                        elif dest_node == east:
                            dest_ni = 3
                            src_ni = 1
                        elif dest_node == south:
                            dest_ni = 0
                            src_ni = 2
                        else:
                            raise RuntimeError("Wrong dest node")
            else:
                if dest_node == north:
                    dest_ni = 2
                    src_ni = 0
                elif dest_node == east:
                    dest_ni = 3
                    src_ni = 1
                elif dest_node == south:
                    dest_ni = 0
                    src_ni = 2
                elif dest_node == west:
                    dest_ni = 1
                    src_ni = 3
        elif topology == 'SM_Bi' or topology == 'Partial_SM_Bi':
            if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension - 1:
                if row == 0 and col == 0:
                    if dest_node == east and second:
                        dest_ni = 3
                        src_ni = 1
                    elif dest_node == east and not second:
                        dest_ni = 4
                        src_ni = 0
                    elif dest_node == south and second:
                        dest_ni = 0
                        src_ni = 2
                    elif dest_node == south and not second:
                        dest_ni = 3
                        src_ni = 3
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == 0 and col == nodes_in_dimension - 1:
                    if dest_node == west and second:
                        dest_ni = 1
                        src_ni = 3
                    elif dest_node == west and not second:
                        dest_ni = 0
                        src_ni = 4
                    elif dest_node == south and second:
                        dest_ni = 0
                        src_ni = 2
                    elif dest_node == south and not second:
                        dest_ni = 4
                        src_ni = 1
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                    if dest_node == north and second:
                        dest_ni = 2
                        src_ni = 0
                    elif dest_node == north and not second:
                        dest_ni = 1
                        src_ni = 4
                    elif dest_node == west and second:
                        dest_ni = 1
                        src_ni = 3
                    elif dest_node == west and not second:
                        dest_ni = 4
                        src_ni = 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == 0:
                    if dest_node == north and second:
                        dest_ni = 2
                        src_ni = 0
                    elif dest_node == north and not second:
                        dest_ni = 4
                        src_ni = 3
                    elif dest_node == east and second:
                        dest_ni = 3
                        src_ni = 1
                    elif dest_node == east and not second:
                        dest_ni = 2
                        src_ni = 2
                    else:
                        raise RuntimeError("Wrong dest node")
                else:
                    if row == 0:
                        if dest_node == east and second:
                            dest_ni = 3
                            src_ni = 1
                        elif dest_node == east and not second:
                            dest_ni = 4
                            src_ni = 0
                        elif dest_node == west and second:
                            dest_ni = 1
                            src_ni = 3
                        elif dest_node == west and not second:
                            dest_ni = 0
                            src_ni = 4
                        elif dest_node == south:
                            dest_ni = 0
                            src_ni = 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == nodes_in_dimension - 1:
                        if dest_node == north and second:
                            dest_ni = 2
                            src_ni = 0
                        elif dest_node == north and not second:
                            dest_ni = 1
                            src_ni = 4
                        elif dest_node == south and second:
                            dest_ni = 0
                            src_ni = 2
                        elif dest_node == south and not second:
                            dest_ni = 4
                            src_ni = 1
                        elif dest_node == west:
                            dest_ni = 1
                            src_ni = 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1:
                        if dest_node == east and second:
                            dest_ni = 3
                            src_ni = 1
                        elif dest_node == east and not second:
                            dest_ni = 2
                            src_ni = 4
                        elif dest_node == west and second:
                            dest_ni = 1
                            src_ni = 3
                        elif dest_node == west and not second:
                            dest_ni = 4
                            src_ni = 2
                        elif dest_node == north:
                            dest_ni = 2
                            src_ni = 0
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif col == 0:
                        if dest_node == south and second:
                            dest_ni = 0
                            src_ni = 2
                        elif dest_node == south and not second:
                            dest_ni = 3
                            src_ni = 4
                        elif dest_node == north and second:
                            dest_ni = 2
                            src_ni = 0
                        elif dest_node == north and not second:
                            dest_ni = 4
                            src_ni = 3
                        elif dest_node == east:
                            dest_ni = 3
                            src_ni = 1
                        else:
                            raise RuntimeError("Wrong dest node")
            else:
                if dest_node == north:
                    dest_ni = 2
                    src_ni = 0
                elif dest_node == east:
                    dest_ni = 3
                    src_ni = 1
                elif dest_node == south:
                    dest_ni = 0
                    src_ni = 2
                elif dest_node == west:
                    dest_ni = 1
                    src_ni = 3
        elif topology == 'SM_Alter' or topology == 'Partial_SM_Alter':
            if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension - 1:
                if nodes_in_dimension % 2 == 0:
                    if row == 0 and col == 0:
                        if dest_node == east and second:
                            dest_ni = 3
                            src_ni = 1
                        elif dest_node == east and not second:
                            dest_ni = 0
                            src_ni = 0
                        elif dest_node == south and second:
                            dest_ni = 0
                            src_ni = 2
                        elif dest_node == south and not second:
                            dest_ni = 3
                            src_ni = 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == 0 and col == nodes_in_dimension - 1:
                        if dest_node == west and second:
                            dest_ni = 1
                            src_ni = 3
                        elif dest_node == west and not second:
                            dest_ni = 0
                            src_ni = 0
                        elif dest_node == south and second:
                            dest_ni = 0
                            src_ni = 2
                        elif dest_node == south and not second:
                            dest_ni = 1
                            src_ni = 1
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                        if dest_node == north and second:
                            dest_ni = 2
                            src_ni = 0
                        elif dest_node == north and not second:
                            dest_ni = 1
                            src_ni = 1
                        elif dest_node == west and second:
                            dest_ni = 1
                            src_ni = 3
                        elif dest_node == west and not second:
                            dest_ni = 2
                            src_ni = 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == 0:
                        if dest_node == north and second:
                            dest_ni = 2
                            src_ni = 0
                        elif dest_node == north and not second:
                            dest_ni = 3
                            src_ni = 3
                        elif dest_node == east and second:
                            dest_ni = 3
                            src_ni = 1
                        elif dest_node == east and not second:
                            dest_ni = 2
                            src_ni = 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    else:
                        if row == 0:
                            if col % 2 == 0:
                                if dest_node == east and second:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == east and not second:
                                    dest_ni = 0
                                    src_ni = 0
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == west and second:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == west and not second:
                                    dest_ni = 0
                                    src_ni = 0
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == nodes_in_dimension - 1:
                            if row % 2 == 0:
                                if dest_node == south and second:
                                    dest_ni = 0
                                    src_ni = 2
                                elif dest_node == south and not second:
                                    dest_ni = 1
                                    src_ni = 1
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == north and second:
                                    dest_ni = 2
                                    src_ni = 0
                                elif dest_node == north and not second:
                                    dest_ni = 1
                                    src_ni = 1
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif row == nodes_in_dimension - 1:
                            if col % 2 == 0:
                                if dest_node == east and second:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == east and not second:
                                    dest_ni = 2
                                    src_ni = 2
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == west and second:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == west and not second:
                                    dest_ni = 2
                                    src_ni = 2
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == 0:
                            if row % 2 == 0:
                                if dest_node == south and second:
                                    dest_ni = 0
                                    src_ni = 2
                                elif dest_node == south and not second:
                                    dest_ni = 3
                                    src_ni = 3
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == north and second:
                                    dest_ni = 2
                                    src_ni = 0
                                elif dest_node == north and not second:
                                    dest_ni = 3
                                    src_ni = 3
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                else:
                    if row == 0 and col == 0:
                        if dest_node == east and second:
                            dest_ni = 3
                            src_ni = 1
                        elif dest_node == east and not second:
                            dest_ni = 0
                            src_ni = 0
                        elif dest_node == south:
                            dest_ni = 0
                            src_ni = 2
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == 0 and col == nodes_in_dimension - 1:
                        if dest_node == south and second:
                            dest_ni = 0
                            src_ni = 2
                        elif dest_node == south and not second:
                            dest_ni = 1
                            src_ni = 1
                        elif dest_node == west:
                            dest_ni = 1
                            src_ni = 3
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                        if dest_node == west and second:
                            dest_ni = 1
                            src_ni = 3
                        elif dest_node == west and not second:
                            dest_ni = 2
                            src_ni = 2
                        elif dest_node == north:
                            dest_ni = 2
                            src_ni = 0
                        else:
                            raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1 and col == 0:
                        if dest_node == north and second:
                            dest_ni = 2
                            src_ni = 0
                        elif dest_node == north and not second:
                            dest_ni = 3
                            src_ni = 3
                        elif dest_node == east:
                            dest_ni = 3
                            src_ni = 1
                        else:
                            raise RuntimeError("Wrong dest node")
                    else:
                        if row == 0:
                            if col % 2 == 0:
                                if dest_node == east and second:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == east and not second:
                                    dest_ni = 0
                                    src_ni = 0
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == west and second:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == west and not second:
                                    dest_ni = 0
                                    src_ni = 0
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == nodes_in_dimension - 1:
                            if row % 2 == 0:
                                if dest_node == south and second:
                                    dest_ni = 0
                                    src_ni = 2
                                elif dest_node == south and not second:
                                    dest_ni = 1
                                    src_ni = 1
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == north and second:
                                    dest_ni = 2
                                    src_ni = 0
                                elif dest_node == north and not second:
                                    dest_ni = 1
                                    src_ni = 1
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif row == nodes_in_dimension - 1:
                            if col % 2 == 0:
                                if dest_node == west and second:
                                    dest_ni = 1
                                    src_ni = 3
                                elif dest_node == west and not second:
                                    dest_ni = 2
                                    src_ni = 2
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == east and second:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == east and not second:
                                    dest_ni = 2
                                    src_ni = 2
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                elif dest_node == west:
                                    dest_ni = 1
                                    src_ni = 3
                                else:
                                    raise RuntimeError("Wrong dest node")
                        elif col == 0:
                            if row % 2 == 0:
                                if dest_node == north and second:
                                    dest_ni = 2
                                    src_ni = 0
                                elif dest_node == north and not second:
                                    dest_ni = 3
                                    src_ni = 3
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                elif dest_node == south:
                                    dest_ni = 0
                                    src_ni = 2
                                else:
                                    raise RuntimeError("Wrong dest node")
                            else:
                                if dest_node == south and second:
                                    dest_ni = 0
                                    src_ni = 2
                                elif dest_node == south and not second:
                                    dest_ni = 3
                                    src_ni = 3
                                elif dest_node == north:
                                    dest_ni = 2
                                    src_ni = 0
                                elif dest_node == east:
                                    dest_ni = 3
                                    src_ni = 1
                                else:
                                    raise RuntimeError("Wrong dest node")
            else:
                if dest_node == north:
                    dest_ni = 2
                    src_ni = 0
                elif dest_node == east:
                    dest_ni = 3
                    src_ni = 1
                elif dest_node == south:
                    dest_ni = 0
                    src_ni = 2
                elif dest_node == west:
                    dest_ni = 1
                    src_ni = 3
        # source_ni = src_ni - radix * source_node
        # dst_ni = dest_ni - radix * dest_node
        return src_ni, dest_ni