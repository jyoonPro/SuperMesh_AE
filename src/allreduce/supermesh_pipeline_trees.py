import copy
import math
import pickle

from .allreduce import Allreduce

class SuperMeshPipelineTrees(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)
        self.args = args

    def get_row_col_nodes(self, node, direction):
        col_idx = node % self.args.per_dim_nodes
        row_idx = math.floor(node / self.args.per_dim_nodes)
        assert row_idx == 0 or row_idx == self.args.per_dim_nodes - 1 or col_idx == 0 or col_idx == self.args.per_dim_nodes - 1
        nodes = []
        for i in range(self.args.num_hmcs):
            new_col_idx = i % self.args.per_dim_nodes
            new_row_idx = math.floor(i / self.args.per_dim_nodes)
            if direction == 'row':
                if row_idx == new_row_idx:
                    nodes.append(i)
            elif direction == 'col':
                if col_idx == new_col_idx:
                    nodes.append(i)

        top_border_nodes, right_border_nodes, bottom_border_nodes, left_border_nodes = self.get_distributed_border_nodes()
        if node in bottom_border_nodes or node in left_border_nodes:
            nodes.reverse()
        popped_node_2 = nodes.pop()
        popped_node_1 = None
        if not ((row_idx == 0 and col_idx == 0) or (row_idx == 0 and col_idx == self.args.per_dim_nodes - 1) or (row_idx == self.args.per_dim_nodes - 1 and col_idx == self.args.per_dim_nodes - 1) or (row_idx == self.args.per_dim_nodes - 1 and col_idx == 0)):
            popped_node_1 = nodes.pop(0)
        if len(nodes) >= 2:
            for_one = nodes[0]
            for_two = nodes[-1]
        else:
            for_one = nodes[0]
            for_two = None
        return popped_node_1, popped_node_2, nodes, for_one, for_two

    def get_row_col_nodes_v2(self, node, direction):
        col_idx = node % self.args.per_dim_nodes
        row_idx = math.floor(node / self.args.per_dim_nodes)
        assert row_idx == 0 or row_idx == self.args.per_dim_nodes - 1 or col_idx == 0 or col_idx == self.args.per_dim_nodes - 1
        nodes = []
        for i in range(self.args.num_hmcs):
            new_col_idx = i % self.args.per_dim_nodes
            new_row_idx = math.floor(i / self.args.per_dim_nodes)
            if direction == 'row':
                if row_idx == new_row_idx:
                    nodes.append(i)
            elif direction == 'col':
                if col_idx == new_col_idx:
                    nodes.append(i)

        top_border_nodes, right_border_nodes, bottom_border_nodes, left_border_nodes = self.get_distributed_border_nodes()
        if node in bottom_border_nodes or node in left_border_nodes:
            nodes.reverse()
        return nodes

    def get_row_col_nodes_for_non_border(self, node, direction):
        col_idx = node % self.args.per_dim_nodes
        row_idx = math.floor(node / self.args.per_dim_nodes)
        assert row_idx == 0 or row_idx == self.args.per_dim_nodes - 1 or col_idx == 0 or col_idx == self.args.per_dim_nodes - 1
        nodes = []
        for i in range(self.args.num_hmcs):
            new_col_idx = i % self.args.per_dim_nodes
            new_row_idx = math.floor(i / self.args.per_dim_nodes)
            if direction == 'row':
                if row_idx == new_row_idx:
                    nodes.append(i)
            elif direction == 'col':
                if col_idx == new_col_idx:
                    nodes.append(i)

        top_border_nodes, right_border_nodes, bottom_border_nodes, left_border_nodes = self.get_distributed_border_nodes()
        if node in bottom_border_nodes or node in right_border_nodes:
            nodes.reverse()
        nodes.pop()
        nodes.pop(0)
        popped_node_1 = None
        return nodes

    def get_neighbor_in_direction(self, node_to_consider, direction):
        left, right, top, bottom = self.get_lrtb(node_to_consider, self.args.per_dim_nodes)
        if direction == 'Left':
            return left
        elif direction == 'Right':
            return right
        elif direction == 'Top':
            return top
        elif direction == 'Bottom':
            return bottom

    def go_to_border_first(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, leaves_list):
        if root_index == 0:
            toward_border = 'Top'
            toward_opposite = 'Bottom'
        elif root_index == 1:
            toward_border = 'Right'
            toward_opposite = 'Left'
        elif root_index == 2:
            toward_border = 'Bottom'
            toward_opposite = 'Top'
        elif root_index == 3:
            toward_border = 'Left'
            toward_opposite = 'Right'

        border_nodes, center_nodes = self.get_center_nodes()
        if root in border_nodes:
            border_roots = True
        else:
            border_roots = False

        if not border_roots:
            borders_reached = False
            node_to_consider = root
            # current_leaves.append(root)
            while not borders_reached:
                timestep = time_tracker[node_to_consider]
                neighbor = self.get_neighbor_in_direction(node_to_consider, toward_opposite)
                if neighbor in border_nodes:
                    borders_reached = True
                    continue
                # TODO: Changed
                assert len(link_map[(node_to_consider, neighbor)]) > 0
                second = link_map[(node_to_consider, neighbor)][0]
                link_map[(node_to_consider, neighbor)].remove(second)
                tree.append((neighbor, node_to_consider, timestep + 1, second))
                leaves_list.append(neighbor)
                time_tracker[neighbor] = timestep + 1
                if timestep + 1 > final_timestep:
                    final_timestep = timestep + 1
                switch_to_switch[node_to_consider].remove((neighbor, second))
                # current_leaves.append(neighbor)
                remaining_nodes_list.remove(neighbor)
                node_to_consider = neighbor

            borders_reached = False
            node_to_consider = root
            while not borders_reached:
                timestep = time_tracker[node_to_consider]
                neighbor = self.get_neighbor_in_direction(node_to_consider, toward_border)
                # TODO: Changed
                assert len(link_map[(node_to_consider, neighbor)]) > 0
                second = link_map[(node_to_consider, neighbor)][0]
                link_map[(node_to_consider, neighbor)].remove(second)
                tree.append((neighbor, node_to_consider, timestep + 1, second))
                leaves_list.append(neighbor)
                time_tracker[neighbor] = timestep + 1
                if timestep + 1 > final_timestep:
                    final_timestep = timestep + 1
                switch_to_switch[node_to_consider].remove((neighbor, second))
                # current_leaves.append(neighbor)
                remaining_nodes_list.remove(neighbor)
                node_to_consider = neighbor
                if neighbor in border_nodes:
                    borders_reached = True
                    root = neighbor
                    node_to_consider = root
        return final_timestep, root

    def go_to_border_first_sm_bi(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, leaves_list, center_tracker):
        if root_index == 0:
            toward_border = 'Top'
            toward_opposite = 'Bottom'
        elif root_index == 1:
            toward_border = 'Right'
            toward_opposite = 'Left'
        elif root_index == 2:
            toward_border = 'Bottom'
            toward_opposite = 'Top'
        elif root_index == 3:
            toward_border = 'Left'
            toward_opposite = 'Right'

        border_nodes, center_nodes = self.get_center_nodes()
        if root in border_nodes:
            border_roots = True
        else:
            border_roots = False

        if not border_roots:
            # borders_reached = False
            # node_to_consider = root
            # # current_leaves.append(root)
            # while not borders_reached:
            #     timestep = time_tracker[node_to_consider]
            #     neighbor = self.get_neighbor_in_direction(node_to_consider, toward_opposite)
            #     if neighbor in border_nodes:
            #         borders_reached = True
            #         continue
            #     assert len(link_map[(neighbor, node_to_consider)]) > 0
            #     second = link_map[(neighbor, node_to_consider)][0]
            #     link_map[(neighbor, node_to_consider)].remove(second)
            #     tree.append((neighbor, node_to_consider, timestep + 1, second))
            #     leaves_list.append(neighbor)
            #     time_tracker[neighbor] = timestep + 1
            #     if timestep + 1 > final_timestep:
            #         final_timestep = timestep + 1
            #     switch_to_switch[node_to_consider].remove((neighbor, second))
            #     # current_leaves.append(neighbor)
            #     remaining_nodes_list.remove(neighbor)
            #     node_to_consider = neighbor

            borders_reached = False
            node_to_consider = root
            while not borders_reached:
                timestep = time_tracker[node_to_consider]
                neighbor = self.get_neighbor_in_direction(node_to_consider, toward_border)
                # TODO: Changed
                assert len(link_map[(node_to_consider, neighbor)]) > 0
                second = link_map[(node_to_consider, neighbor)][0]
                link_map[(node_to_consider, neighbor)].remove(second)
                tree.append((neighbor, node_to_consider, timestep + 1, second))
                leaves_list.append(neighbor)
                time_tracker[neighbor] = timestep + 1
                if timestep + 1 > final_timestep:
                    final_timestep = timestep + 1
                switch_to_switch[node_to_consider].remove((neighbor, second))
                if node_to_consider in center_nodes and neighbor in center_nodes:
                    center_tracker[node_to_consider] = 1
                # current_leaves.append(neighbor)
                remaining_nodes_list.remove(neighbor)
                node_to_consider = neighbor
                if neighbor in border_nodes:
                    borders_reached = True
                    root = neighbor
                    node_to_consider = root
        return final_timestep, root

    def go_to_border_first_2(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, leaves_list, toward_border, toward_opposite):
        # if root_index == 0:
        #     toward_border = 'Top'
        #     toward_opposite = 'Bottom'
        # elif root_index == 1:
        #     toward_border = 'Right'
        #     toward_opposite = 'Left'
        # elif root_index == 2:
        #     toward_border = 'Bottom'
        #     toward_opposite = 'Top'
        # elif root_index == 3:
        #     toward_border = 'Left'
        #     toward_opposite = 'Right'

        border_nodes, center_nodes = self.get_center_nodes()
        if root in border_nodes:
            border_roots = True
        else:
            border_roots = False

        if not border_roots:
            # borders_reached = False
            # node_to_consider = root
            # # current_leaves.append(root)
            # while not borders_reached:
            #     timestep = time_tracker[node_to_consider]
            #     neighbor = self.get_neighbor_in_direction(node_to_consider, toward_opposite)
            #     if neighbor in border_nodes:
            #         borders_reached = True
            #         continue
            #     # assert len(link_map[(neighbor, node_to_consider)]) > 0
            #     if len(link_map[(neighbor, node_to_consider)]) == 0:
            #         break
            #     second = link_map[(neighbor, node_to_consider)][0]
            #     link_map[(neighbor, node_to_consider)].remove(second)
            #     tree.append((neighbor, node_to_consider, timestep + 1, second))
            #     leaves_list.append(neighbor)
            #     time_tracker[neighbor] = timestep + 1
            #     if timestep + 1 > final_timestep:
            #         final_timestep = timestep + 1
            #     switch_to_switch[node_to_consider].remove((neighbor, second))
            #     # current_leaves.append(neighbor)
            #     remaining_nodes_list.remove(neighbor)
            #     node_to_consider = neighbor

            borders_reached = False
            node_to_consider = root
            while not borders_reached:
                timestep = time_tracker[node_to_consider]
                neighbor = self.get_neighbor_in_direction(node_to_consider, toward_border)
                #TODO: Changed
                assert len(link_map[(node_to_consider, neighbor)]) > 0
                second = link_map[(node_to_consider, neighbor)][0]
                link_map[(node_to_consider, neighbor)].remove(second)
                tree.append((neighbor, node_to_consider, timestep + 1, second))
                leaves_list.append(neighbor)
                time_tracker[neighbor] = timestep + 1
                if timestep + 1 > final_timestep:
                    final_timestep = timestep + 1
                switch_to_switch[node_to_consider].remove((neighbor, second))
                # current_leaves.append(neighbor)
                remaining_nodes_list.remove(neighbor)
                node_to_consider = neighbor
                if neighbor in border_nodes:
                    borders_reached = True
                    root = neighbor
                    node_to_consider = root
        return final_timestep, root

    def get_values(self, root):
        col_idx = root % self.args.per_dim_nodes
        row_idx = math.floor(root / self.args.per_dim_nodes)
        first_dir_1 = None
        first_dir_1_count = 0
        first_dir_2 = None
        first_dir_2_count = 0
        second_dir = None
        second_dir_count = 0
        for_second_direction = []
        if row_idx == 0 and col_idx == 0:
            first_dir_1 = 'Left'
            first_dir_2 = 'Right'
            second_dir = 'Bottom'
            first_dir_1_count = col_idx
            first_dir_2_count = self.args.per_dim_nodes - col_idx - 1
            second_dir_count = self.args.per_dim_nodes - 2
            for_second_direction = self.get_row_col_nodes_v2(root, 'row')
        elif row_idx == 0 and col_idx == self.args.per_dim_nodes - 1:
            first_dir_1 = 'Top'
            first_dir_2 = 'Bottom'
            second_dir = 'Left'
            first_dir_1_count = row_idx
            first_dir_2_count = self.args.per_dim_nodes - row_idx - 1
            second_dir_count = self.args.per_dim_nodes - 2
            for_second_direction = self.get_row_col_nodes_v2(root, 'col')
        elif row_idx == self.args.per_dim_nodes - 1 and col_idx == self.args.per_dim_nodes - 1:
            first_dir_1 = 'Right'
            first_dir_2 = 'Left'
            second_dir = 'Top'
            first_dir_1_count = self.args.per_dim_nodes - col_idx - 1
            first_dir_2_count = col_idx
            second_dir_count = self.args.per_dim_nodes - 2
            for_second_direction = self.get_row_col_nodes_v2(root, 'row')
        elif row_idx == self.args.per_dim_nodes - 1 and col_idx == 0:
            first_dir_1 = 'Bottom'
            first_dir_2 = 'Top'
            second_dir = 'Right'
            first_dir_1_count = self.args.per_dim_nodes - row_idx - 1
            first_dir_2_count = row_idx
            second_dir_count = self.args.per_dim_nodes - 2
            for_second_direction = self.get_row_col_nodes_v2(root, 'col')
        else:
            if row_idx == 0:
                first_dir_1 = 'Left'
                first_dir_2 = 'Right'
                second_dir = 'Bottom'
                first_dir_1_count = col_idx
                first_dir_2_count = self.args.per_dim_nodes - col_idx - 1
                second_dir_count = self.args.per_dim_nodes - 2
                for_second_direction = self.get_row_col_nodes_v2(root, 'row')
            elif row_idx == self.args.per_dim_nodes - 1:
                first_dir_1 = 'Right'
                first_dir_2 = 'Left'
                second_dir = 'Top'
                first_dir_1_count = self.args.per_dim_nodes - col_idx - 1
                first_dir_2_count = col_idx
                second_dir_count = self.args.per_dim_nodes - 2
                for_second_direction = self.get_row_col_nodes_v2(root, 'row')
            elif col_idx == 0:
                first_dir_1 = 'Bottom'
                first_dir_2 = 'Top'
                second_dir = 'Right'
                first_dir_1_count = self.args.per_dim_nodes - row_idx - 1
                first_dir_2_count = row_idx
                second_dir_count = self.args.per_dim_nodes - 2
                for_second_direction = self.get_row_col_nodes_v2(root, 'col')
            elif col_idx == self.args.per_dim_nodes - 1:
                first_dir_1 = 'Top'
                first_dir_2 = 'Bottom'
                second_dir = 'Left'
                first_dir_1_count = row_idx
                first_dir_2_count = self.args.per_dim_nodes - row_idx - 1
                second_dir_count = self.args.per_dim_nodes - 2
                for_second_direction = self.get_row_col_nodes_v2(root, 'col')

        return first_dir_1, first_dir_2, second_dir, first_dir_1_count, first_dir_2_count, second_dir_count, for_second_direction

    def connect_first_dim_nodes(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, border_roots, leaves_list, first_dir_1, first_dir_2, first_dir_1_count, first_dir_2_count):
        if not border_roots:
            node_to_consider = root
        else:
            # current_leaves.append(root)
            node_to_consider = root


        for i in range(first_dir_1_count):
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_1)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            # current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)
            node_to_consider = neighbor

        node_to_consider = root
        for i in range(first_dir_2_count):
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_2)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            # current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)
            node_to_consider = neighbor

    def connect_first_dim_nodes_sm_bi(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, border_roots, leaves_list, first_dir_1, first_dir_2, first_dir_1_count, first_dir_2_count, center_tracker):
        border_nodes, center_nodes = self.get_center_nodes()
        if not border_roots:
            node_to_consider = root
        else:
            # current_leaves.append(root)
            node_to_consider = root


        for i in range(first_dir_1_count):
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_1)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            if node_to_consider in center_nodes and neighbor in center_nodes:
                center_tracker[node_to_consider] = 1
            # current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)
            node_to_consider = neighbor

        node_to_consider = root
        for i in range(first_dir_2_count):
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_2)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            # current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)
            node_to_consider = neighbor

    def connect_nodes_to_alternate_tree_2(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, border_roots, leaves_list, for_second_direction, second_dir_count, second_dir):
        for_one = for_second_direction[1]
        for_two = for_second_direction[-2]
        for_one_nodes = []
        for_two_nodes = []
        node_to_consider = for_one
        for i in range(second_dir_count):
            neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
            for_one_nodes.append(neighbor)
            node_to_consider =  neighbor
        node_to_consider = for_two
        for i in range(second_dir_count):
            neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
            for_two_nodes.append(neighbor)
            node_to_consider = neighbor

        for (index, target_node) in enumerate(for_second_direction):
            node_to_consider = target_node
            for i in range(second_dir_count):
                timestep = time_tracker[node_to_consider]
                neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
                # TODO: Changed
                if len(link_map[(node_to_consider, neighbor)]) == 0:
                    break
                second = link_map[(node_to_consider, neighbor)][0]
                link_map[(node_to_consider, neighbor)].remove(second)
                tree.append((neighbor, node_to_consider, timestep + 1, second))
                leaves_list.append(neighbor)
                time_tracker[neighbor] = timestep + 1
                if timestep + 1 > final_timestep:
                    final_timestep = timestep + 1
                switch_to_switch[node_to_consider].remove((neighbor, second))
                current_leaves.append(neighbor)
                if node_to_consider in current_leaves:
                    current_leaves.remove(node_to_consider)
                remaining_nodes_list.remove(neighbor)
                node_to_consider = neighbor

        return final_timestep, for_one_nodes, for_two_nodes

    def connect_nodes_to_alternate_tree_2_sm_bi(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, border_roots, leaves_list, for_second_direction, second_dir_count, second_dir, center_tracker):
        for_one = for_second_direction[1]
        for_two = for_second_direction[-2]
        for_one_nodes = []
        for_two_nodes = []
        node_to_consider = for_one
        border_nodes, center_nodes = self.get_center_nodes()
        for i in range(second_dir_count):
            neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
            for_one_nodes.append(neighbor)
            node_to_consider =  neighbor
        node_to_consider = for_two
        for i in range(second_dir_count):
            neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
            for_two_nodes.append(neighbor)
            node_to_consider = neighbor

        for (index, target_node) in enumerate(for_second_direction):
            node_to_consider = target_node
            for i in range(second_dir_count):
                timestep = time_tracker[node_to_consider]
                neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
                # TODO: Changed
                if len(link_map[(node_to_consider, neighbor)]) == 0:
                    break
                second = link_map[(node_to_consider, neighbor)][0]
                link_map[(node_to_consider, neighbor)].remove(second)
                tree.append((neighbor, node_to_consider, timestep + 1, second))
                leaves_list.append(neighbor)
                time_tracker[neighbor] = timestep + 1
                if timestep + 1 > final_timestep:
                    final_timestep = timestep + 1
                switch_to_switch[node_to_consider].remove((neighbor, second))
                current_leaves.append(neighbor)
                if node_to_consider in current_leaves:
                    current_leaves.remove(node_to_consider)
                if node_to_consider in center_nodes and neighbor in center_nodes:
                    center_tracker[node_to_consider] = 1
                remaining_nodes_list.remove(neighbor)
                node_to_consider = neighbor

        return final_timestep, for_one_nodes, for_two_nodes

    def connect_side_nodes(self, for_one_nodes, for_two_nodes, time_tracker, first_dir_1, first_dir_2, second_dir, link_map, tree, leaves_list, switch_to_switch, current_leaves, remaining_nodes_list, final_timestep):
        for node in for_one_nodes:
            neighbor1 = self.get_neighbor_in_direction(node, first_dir_1)
            neighbor2 = self.get_neighbor_in_direction(neighbor1, second_dir)
            if neighbor1 in remaining_nodes_list and neighbor2 in remaining_nodes_list:
                # TODO: Changed
                if len(link_map[(node, neighbor1)]) > 0 and len(link_map[(neighbor1, neighbor2)]) > 0:
                    timestep = time_tracker[node]
                    second = link_map[(node, neighbor1)][0]
                    link_map[(node, neighbor1)].remove(second)
                    tree.append((neighbor1, node, timestep + 1, second))
                    leaves_list.append(neighbor1)
                    time_tracker[neighbor1] = timestep + 1
                    if timestep + 1 > final_timestep:
                        final_timestep = timestep + 1
                    switch_to_switch[node].remove((neighbor1, second))
                    current_leaves.append(neighbor1)
                    remaining_nodes_list.remove(neighbor1)

                    timestep = time_tracker[neighbor1]
                    second = link_map[(neighbor1, neighbor2)][0]
                    link_map[(neighbor1, neighbor2)].remove(second)
                    tree.append((neighbor2, neighbor1, timestep + 1, second))
                    leaves_list.append(neighbor2)
                    time_tracker[neighbor2] = timestep + 1
                    if timestep + 1 > final_timestep:
                        final_timestep = timestep + 1
                    switch_to_switch[neighbor1].remove((neighbor2, second))
                    current_leaves.append(neighbor2)
                    remaining_nodes_list.remove(neighbor2)

        for node in for_two_nodes:
            neighbor1 = self.get_neighbor_in_direction(node, first_dir_2)
            neighbor2 = self.get_neighbor_in_direction(neighbor1, second_dir)
            if neighbor1 in remaining_nodes_list and neighbor2 in remaining_nodes_list:
                # TODO: Changed
                if len(link_map[(node, neighbor1)]) > 0 and len(link_map[(neighbor1, neighbor2)]) > 0:
                    timestep = time_tracker[node]
                    second = link_map[(node, neighbor1)][0]
                    link_map[(node, neighbor1)].remove(second)
                    tree.append((neighbor1, node, timestep + 1, second))
                    leaves_list.append(neighbor1)
                    time_tracker[neighbor1] = timestep + 1
                    if timestep + 1 > final_timestep:
                        final_timestep = timestep + 1
                    switch_to_switch[node].remove((neighbor1, second))
                    current_leaves.append(neighbor1)
                    remaining_nodes_list.remove(neighbor1)

                    timestep = time_tracker[neighbor1]
                    second = link_map[(neighbor1, neighbor2)][0]
                    link_map[(neighbor1, neighbor2)].remove(second)
                    tree.append((neighbor2, neighbor1, timestep + 1, second))
                    leaves_list.append(neighbor2)
                    time_tracker[neighbor2] = timestep + 1
                    if timestep + 1 > final_timestep:
                        final_timestep = timestep + 1
                    switch_to_switch[neighbor1].remove((neighbor2, second))
                    current_leaves.append(neighbor2)
                    remaining_nodes_list.remove(neighbor2)
        return final_timestep




    def connect_nodes_to_alternate_tree(self, root, link_map, switch_to_switch, current_leaves, tree, time_tracker, remaining_nodes_list, final_timestep, root_index, border_roots, leaves_list):
        # if root_index == 0:
        #     toward_border = 'Top'
        #     toward_opposite = 'Bottom'
        # elif root_index == 1:
        #     toward_border = 'Right'
        #     toward_opposite = 'Left'
        # elif root_index == 2:
        #     toward_border = 'Bottom'
        #     toward_opposite = 'Top'
        # elif root_index == 3:
        #     toward_border = 'Left'
        #     toward_opposite = 'Right'

        # border_nodes, center_nodes = self.get_center_nodes()
        # if root in border_nodes:
        #     border_roots = True
        # else:
        #     border_roots = False

        one_dir_nodes = []
        another_dir_nodes = []

        if not border_roots:
            # borders_reached = False
            # node_to_consider = root
            # current_leaves.append(root)
            # while not borders_reached:
            #     timestep = time_tracker[node_to_consider]
            #     neighbor = self.get_neighbor_in_direction(node_to_consider, toward_opposite)
            #     if neighbor in border_nodes:
            #         borders_reached = True
            #         continue
            #     assert len(link_map[(neighbor, node_to_consider)]) > 0
            #     second = link_map[(neighbor, node_to_consider)][0]
            #     link_map[(neighbor, node_to_consider)].remove(second)
            #     tree.append((neighbor, node_to_consider, timestep + 1, second))
            #     time_tracker[neighbor] = timestep + 1
            #     if timestep + 1 > final_timestep:
            #         final_timestep = timestep + 1
            #     switch_to_switch[node_to_consider].remove((neighbor, second))
            #     current_leaves.append(neighbor)
            #     remaining_nodes_list.remove(neighbor)
            #     node_to_consider = neighbor
            #
            # borders_reached = False
            # node_to_consider = root
            # while not borders_reached:
            #     timestep = time_tracker[node_to_consider]
            #     neighbor = self.get_neighbor_in_direction(node_to_consider, toward_border)
            #     assert len(link_map[(neighbor, node_to_consider)]) > 0
            #     second = link_map[(neighbor, node_to_consider)][0]
            #     link_map[(neighbor, node_to_consider)].remove(second)
            #     tree.append((neighbor, node_to_consider, timestep + 1, second))
            #     time_tracker[neighbor] = timestep + 1
            #     if timestep + 1 > final_timestep:
            #         final_timestep = timestep + 1
            #     switch_to_switch[node_to_consider].remove((neighbor, second))
            #     current_leaves.append(neighbor)
            #     remaining_nodes_list.remove(neighbor)
            #     node_to_consider = neighbor
            #     if neighbor in border_nodes:
            #         borders_reached = True
            #         root = neighbor
            #         node_to_consider = root
            node_to_consider = root
        else:
            current_leaves.append(root)
            node_to_consider = root

        col_idx = root % self.args.per_dim_nodes
        row_idx = math.floor(root / self.args.per_dim_nodes)
        first_dir_1 = None
        first_dir_1_count = 0
        first_dir_2 = None
        first_dir_2_count = 0
        second_dir = None
        second_dir_count = 0
        for_second_direction = []
        if row_idx == 0 and col_idx == 0:
            first_dir_1 = 'Left'
            first_dir_2 = 'Right'
            second_dir = 'Bottom'
            first_dir_1_count = col_idx
            first_dir_2_count = self.args.per_dim_nodes - col_idx - 1
            second_dir_count = self.args.per_dim_nodes - 2
            popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'row')
        elif row_idx == 0 and col_idx == self.args.per_dim_nodes - 1:
            first_dir_1 = 'Top'
            first_dir_2 = 'Bottom'
            second_dir = 'Left'
            first_dir_1_count = row_idx
            first_dir_2_count = self.args.per_dim_nodes - row_idx - 1
            second_dir_count = self.args.per_dim_nodes - 2
            popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'col')
        elif row_idx == self.args.per_dim_nodes - 1 and col_idx == self.args.per_dim_nodes - 1:
            first_dir_1 = 'Right'
            first_dir_2 = 'Left'
            second_dir = 'Top'
            first_dir_1_count = self.args.per_dim_nodes - col_idx - 1
            first_dir_2_count = col_idx
            second_dir_count = self.args.per_dim_nodes - 2
            popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'row')
        elif row_idx == self.args.per_dim_nodes - 1 and col_idx == 0:
            first_dir_1 = 'Bottom'
            first_dir_2 = 'Top'
            second_dir = 'Right'
            first_dir_1_count = self.args.per_dim_nodes - row_idx - 1
            first_dir_2_count = row_idx
            second_dir_count = self.args.per_dim_nodes - 2
            popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'col')
        else:
            if row_idx == 0:
                first_dir_1 = 'Left'
                first_dir_2 = 'Right'
                second_dir = 'Bottom'
                first_dir_1_count = col_idx
                first_dir_2_count = self.args.per_dim_nodes - col_idx - 1
                second_dir_count = self.args.per_dim_nodes - 2
                popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'row')
            elif row_idx == self.args.per_dim_nodes - 1:
                first_dir_1 = 'Right'
                first_dir_2 = 'Left'
                second_dir = 'Top'
                first_dir_1_count = self.args.per_dim_nodes - col_idx - 1
                first_dir_2_count = col_idx
                second_dir_count = self.args.per_dim_nodes - 2
                popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'row')
            elif col_idx == 0:
                first_dir_1 = 'Bottom'
                first_dir_2 = 'Top'
                second_dir = 'Right'
                first_dir_1_count = self.args.per_dim_nodes - row_idx - 1
                first_dir_2_count = row_idx
                second_dir_count = self.args.per_dim_nodes - 2
                popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'col')
            elif col_idx == self.args.per_dim_nodes - 1:
                first_dir_1 = 'Top'
                first_dir_2 = 'Bottom'
                second_dir = 'Left'
                first_dir_1_count = row_idx
                first_dir_2_count = self.args.per_dim_nodes - row_idx - 1
                second_dir_count = self.args.per_dim_nodes - 2
                popped_node_1, popped_node_2, for_second_direction, for_one, for_two = self.get_row_col_nodes(root, 'col')

        # first_pop = for_second_direction.pop(0)
        # second_pop = for_second_direction.pop()
        if not border_roots:
            for_second_direction.remove(root)
            if row_idx == 0:
                sorted_nodes = self.get_row_col_nodes_for_non_border(root, 'col')
            elif row_idx == self.args.per_dim_nodes - 1:
                sorted_nodes = self.get_row_col_nodes_for_non_border(root, 'col')
            elif col_idx == 0:
                sorted_nodes = self.get_row_col_nodes_for_non_border(root, 'row')
            elif col_idx == self.args.per_dim_nodes - 1:
                sorted_nodes = self.get_row_col_nodes_for_non_border(root, 'row')
            for i, node in enumerate(sorted_nodes):
                if i % 2 == 1:
                    if root == for_one:
                        one_dir_nodes.append(node)
                    elif root == for_two:
                        another_dir_nodes.append(node)
            # print("Yo")


        for i in range(first_dir_1_count):
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_1)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)
            node_to_consider = neighbor

        node_to_consider = root
        for i in range(first_dir_2_count):
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_2)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)
            node_to_consider = neighbor

        node_to_consider = popped_node_2
        timestep = time_tracker[node_to_consider]
        neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
        # TODO: Changed
        assert len(link_map[(node_to_consider, neighbor)]) > 0
        second = link_map[(node_to_consider, neighbor)][0]
        link_map[(node_to_consider, neighbor)].remove(second)
        tree.append((neighbor, node_to_consider, timestep + 1, second))
        leaves_list.append(neighbor)
        time_tracker[neighbor] = timestep + 1
        if timestep + 1 > final_timestep:
            final_timestep = timestep + 1
        switch_to_switch[node_to_consider].remove((neighbor, second))
        current_leaves.append(neighbor)
        remaining_nodes_list.remove(neighbor)

        if popped_node_1 is not None:
            node_to_consider = popped_node_1
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
            #TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)

        for (index, target_node) in enumerate(for_second_direction):
            node_to_consider = target_node
            for i in range(second_dir_count):
                timestep = time_tracker[node_to_consider]
                neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
                #TODO: Changed
                assert len(link_map[(node_to_consider, neighbor)]) > 0
                second = link_map[(node_to_consider, neighbor)][0]
                link_map[(node_to_consider, neighbor)].remove(second)
                tree.append((neighbor, node_to_consider, timestep + 1, second))
                leaves_list.append(neighbor)
                time_tracker[neighbor] = timestep + 1
                if timestep + 1 > final_timestep:
                    final_timestep = timestep + 1
                switch_to_switch[node_to_consider].remove((neighbor, second))
                current_leaves.append(neighbor)
                remaining_nodes_list.remove(neighbor)
                if i % 2 == 1:
                    if target_node == for_one:
                        if popped_node_1 is not None:
                            one_dir_nodes.append(neighbor)
                    elif target_node == for_two:
                        another_dir_nodes.append(neighbor)
                node_to_consider = neighbor

        for node in one_dir_nodes:
            node_to_consider = node
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_1)
            # TODO: Changed
            if len(link_map[(node_to_consider, neighbor)]) == 0:
                continue
            # assert len(link_map[(neighbor, node_to_consider)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)

            node_to_consider = neighbor
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)

        for node in another_dir_nodes:
            node_to_consider = node
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, first_dir_2)
            # TODO: Changed
            if len(link_map[(node_to_consider, neighbor)]) == 0:
                continue
            # assert len(link_map[(neighbor, node_to_consider)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)

            node_to_consider = neighbor
            timestep = time_tracker[node_to_consider]
            neighbor = self.get_neighbor_in_direction(node_to_consider, second_dir)
            # TODO: Changed
            assert len(link_map[(node_to_consider, neighbor)]) > 0
            second = link_map[(node_to_consider, neighbor)][0]
            link_map[(node_to_consider, neighbor)].remove(second)
            tree.append((neighbor, node_to_consider, timestep + 1, second))
            leaves_list.append(neighbor)
            time_tracker[neighbor] = timestep + 1
            if timestep + 1 > final_timestep:
                final_timestep = timestep + 1
            switch_to_switch[node_to_consider].remove((neighbor, second))
            current_leaves.append(neighbor)
            remaining_nodes_list.remove(neighbor)

        return final_timestep

    # def generate_trees(self, roots, collective):
    #     if collective == 'RS':
    #         switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
    #     else:
    #         switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)
    #
    #     link_map = {}
    #     for node in switch_to_switch.keys():
    #         for (neighbor, second) in switch_to_switch[node]:
    #             if (node, neighbor) not in link_map.keys():
    #                 link_map[(node, neighbor)] = []
    #             link_map[(node, neighbor)].append(second)
    #     print("Link map ready")
    #
    #     trees = {}
    #     time_trackers = {}
    #     remaining_nodes_list = {}
    #     current_leaves = {}
    #     final_timestep = 0
    #     leaves_list = {}
    #     first_dir_1_values = {}
    #     first_dir_2_values = {}
    #     second_dir_values = {}
    #     first_dir_1_count_values = {}
    #     first_dir_2_count_values = {}
    #     second_count_values = {}
    #     for_second_dim_values = {}
    #     for_one_nodes_values = {}
    #     for_two_nodes_values = {}
    #
    #     border_nodes, center_nodes = self.get_center_nodes()
    #
    #     if roots[0] not in border_nodes:
    #         new_roots = []
    #         for (root_idx, root) in enumerate(roots):
    #             trees[root] = []
    #             time_trackers[root] = {}
    #             time_trackers[root][root] = 0
    #             remaining_nodes_list[root] = list(range(self.args.num_hmcs))
    #             remaining_nodes_list[root].remove(root)
    #             current_leaves[root] = []
    #             leaves_list[root] = []
    #             temp_final_timestep, temp_root = self.go_to_border_first(root, link_map, switch_to_switch,
    #                                                                    current_leaves[root], trees[root],
    #                                                                    time_trackers[root], remaining_nodes_list[root],
    #                                                                    final_timestep, root_idx, leaves_list[root])
    #             new_roots.append(temp_root)
    #
    #         for (root_idx, root) in enumerate(roots):
    #             first_dir_1, first_dir_2, second_dir, first_dir_1_count, first_dir_2_count, second_dir_count, for_second_direction = self.get_values(new_roots[root_idx])
    #             first_dir_1_values[root] = first_dir_1
    #             first_dir_2_values[root] = first_dir_2
    #             second_dir_values[root] = second_dir
    #             first_dir_1_count_values[root] = first_dir_1_count
    #             first_dir_2_count_values[root] = first_dir_2_count
    #             second_count_values[root] = second_dir_count
    #             for_second_dim_values[root] = for_second_direction
    #             for_second_direction.remove(new_roots[root_idx])
    #
    #         for (root_idx, root) in enumerate(roots):
    #             self.connect_first_dim_nodes(new_roots[root_idx], link_map, switch_to_switch,
    #                                                                        current_leaves[root], trees[root],
    #                                                                        time_trackers[root],
    #                                                                        remaining_nodes_list[root], final_timestep,
    #                                                                        root_idx, False, leaves_list[root], first_dir_1_values[root], first_dir_2_values[root], first_dir_1_count_values[root], first_dir_2_count_values[root])
    #
    #         for (root_idx, root) in enumerate(roots):
    #             temp_final_timestep, for_one_nodes, for_two_nodes = self.connect_nodes_to_alternate_tree_2(new_roots[root_idx], link_map, switch_to_switch,
    #                                                                        current_leaves[root], trees[root],
    #                                                                        time_trackers[root],
    #                                                                        remaining_nodes_list[root], final_timestep,
    #                                                                        root_idx, False, leaves_list[root], for_second_dim_values[root], second_count_values[root], second_dir_values[root])
    #             for_one_nodes_values[root] = for_one_nodes
    #             for_two_nodes_values[root] = for_two_nodes
    #             if temp_final_timestep > final_timestep:
    #                 final_timestep = temp_final_timestep
    #
    #         for (root_idx, root) in enumerate(roots):
    #             temp_final_timestep = self.connect_side_nodes(for_one_nodes_values[root], for_two_nodes_values[root],
    #                                                           time_trackers[root],
    #                                                           first_dir_1_values[root], first_dir_2_values[root],
    #                                                           second_dir_values[root], link_map, trees[root],
    #                                                           leaves_list[root], switch_to_switch, current_leaves[root],
    #                                                           remaining_nodes_list[root], final_timestep)
    #             if temp_final_timestep > final_timestep:
    #                 final_timestep = temp_final_timestep
    #     else:
    #         for (root_idx, root) in enumerate(roots):
    #             trees[root] = []
    #             time_trackers[root] = {}
    #             time_trackers[root][root] = 0
    #             remaining_nodes_list[root] = list(range(self.args.num_hmcs))
    #             remaining_nodes_list[root].remove(root)
    #             current_leaves[root] = []
    #             leaves_list[root] = []
    #             temp_final_timestep = self.connect_nodes_to_alternate_tree(root, link_map, switch_to_switch, current_leaves[root], trees[root], time_trackers[root], remaining_nodes_list[root], final_timestep, root_idx, True, leaves_list[root])
    #             if temp_final_timestep > final_timestep:
    #                 final_timestep = temp_final_timestep
    #
    #     # if 8 in roots:
    #     #     print("Yoo")
    #     #     current_leaves[8].append(26)
    #     #     current_leaves[16].append(13)
    #     #     current_leaves[27].append(9)
    #     #     current_leaves[19].append(22)
    #     #
    #     # finished = False
    #     # while not finished:
    #     #     temp_current_leaves = copy.deepcopy(current_leaves)
    #     #     temp_remaining_nodes_list = copy.deepcopy(remaining_nodes_list)
    #     #     temp_switch_to_switch = copy.deepcopy(switch_to_switch)
    #     #     temp_time_trackers = copy.deepcopy(time_trackers)
    #     #     temp_trees = copy.deepcopy(trees)
    #     #     temp_leaves_list = copy.deepcopy(leaves_list)
    #     #
    #     #     all_done = False
    #     #     while not all_done:
    #     #         for root in roots:
    #     #             if len(temp_current_leaves[root]) == 0 or len(temp_remaining_nodes_list[root]) == 0:
    #     #                 continue
    #     #             to_remove = []
    #     #             leave = temp_current_leaves[root][0]
    #     #             neighbors = temp_switch_to_switch[leave]
    #     #             random.shuffle(neighbors)
    #     #             need_to_remove = True
    #     #             for neighbor, second in neighbors:
    #     #                 if neighbor in temp_remaining_nodes_list[root]:
    #     #                     timestep = temp_time_trackers[root][leave]
    #     #                     temp_trees[root].append((neighbor, leave, timestep + 1, second))
    #     #                     temp_leaves_list[root].append(neighbor)
    #     #                     temp_time_trackers[root][neighbor] = timestep + 1
    #     #                     if timestep + 1 > final_timestep:
    #     #                         final_timestep = timestep + 1
    #     #                     temp_remaining_nodes_list[root].remove(neighbor)
    #     #                     to_remove.append((neighbor, second))
    #     #                     temp_current_leaves[root].append(neighbor)
    #     #                     need_to_remove = False
    #     #                     break
    #     #             if need_to_remove:
    #     #                 temp_current_leaves[root].remove(leave)
    #     #             for node in to_remove:
    #     #                 temp_switch_to_switch[leave].remove(node)
    #     #         done = True
    #     #         for root in roots:
    #     #             if len(temp_current_leaves[root]) != 0 and len(temp_remaining_nodes_list[root]) != 0:
    #     #                 done = False
    #     #         if done:
    #     #             all_done = True
    #     #     finished = True
    #     #     for root in roots:
    #     #         if len(temp_trees[root]) != (self.args.num_hmcs - 1):
    #     #             finished = False
    #     #             break
    #     #     print("Not Finished")
    #     #
    #     # print("Yoo")
    #
    #     # all_done = False
    #     # while not all_done:
    #     #     for root in roots:
    #     #         if len(current_leaves[root]) == 0 or len(remaining_nodes_list[root]) == 0:
    #     #             continue
    #     #         to_remove = []
    #     #         leave = current_leaves[root][0]
    #     #         neighbors = switch_to_switch[leave]
    #     #         need_to_remove = True
    #     #         for neighbor, second in neighbors:
    #     #             if neighbor in remaining_nodes_list[root]:
    #     #                 timestep = time_trackers[root][leave]
    #     #                 trees[root].append((neighbor, leave, timestep + 1, second))
    #     #                 leaves_list[root].append(neighbor)
    #     #                 time_trackers[root][neighbor] = timestep + 1
    #     #                 if timestep + 1 > final_timestep:
    #     #                     final_timestep = timestep + 1
    #     #                 remaining_nodes_list[root].remove(neighbor)
    #     #                 to_remove.append((neighbor, second))
    #     #                 current_leaves[root].append(neighbor)
    #     #                 need_to_remove = False
    #     #                 break
    #     #         if need_to_remove:
    #     #             current_leaves[root].remove(leave)
    #     #         for node in to_remove:
    #     #             switch_to_switch[leave].remove(node)
    #     #     done = True
    #     #     for root in roots:
    #     #         if len(current_leaves[root]) != 0 and len(remaining_nodes_list[root]) != 0:
    #     #             done = False
    #     #     if done:
    #     #         all_done = True
    #
    #     # all_done = True
    #     # for root in roots:
    #     #     if len(trees[root]) != (self.args.num_hmcs - 1):
    #     #         all_done = False
    #     #         break
    #
    #     all_done = False
    #     if not all_done:
    #         while not all_done:
    #             all_done = True
    #             min_len = len(leaves_list[roots[0]])
    #             for i in range(len(roots)):
    #                 min_len = min(min_len, len(leaves_list[roots[i]]))
    #             for i in range(min_len):
    #                 for root in roots:
    #                     if len(remaining_nodes_list[root]) == 0:
    #                         continue
    #                     to_remove = []
    #                     leave = leaves_list[root][i]
    #                     neighbors = switch_to_switch[leave]
    #                     for neighbor, second in neighbors:
    #                         if neighbor in remaining_nodes_list[root]:
    #                             timestep = time_trackers[root][leave]
    #                             trees[root].append((neighbor, leave, timestep + 1, second))
    #                             leaves_list[root].append(neighbor)
    #                             time_trackers[root][neighbor] = timestep + 1
    #                             if timestep + 1 > final_timestep:
    #                                 final_timestep = timestep + 1
    #                             remaining_nodes_list[root].remove(neighbor)
    #                             to_remove.append((neighbor, second))
    #                             current_leaves[root].append(neighbor)
    #                             all_done = False
    #                             break
    #                     for node in to_remove:
    #                         switch_to_switch[leave].remove(node)
    #     for root in roots:
    #         assert len(trees[root]) == (self.args.num_hmcs - 1)
    #
    #     # Check no link is used twice in the disjoint tree sets.
    #     if collective == 'RS':
    #         switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
    #     else:
    #         switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)
    #
    #     for root in roots:
    #         for edge in trees[root]:
    #             if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
    #                 print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
    #                 exit()
    #             else:
    #                 switch_to_switch[edge[1]].remove((edge[0], edge[3]))
    #     return trees, final_timestep

    def generate_trees_border(self, roots, collective):
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        link_map = {}
        for node in switch_to_switch.keys():
            for (neighbor, second) in switch_to_switch[node]:
                if (node, neighbor) not in link_map.keys():
                    link_map[(node, neighbor)] = []
                link_map[(node, neighbor)].append(second)
        # print("Link map ready")

        trees = {}
        time_trackers = {}
        remaining_nodes_list = {}
        current_leaves = {}
        final_timestep = 0
        leaves_list = {}

        # border_nodes, center_nodes = self.get_center_nodes()

        for (root_idx, root) in enumerate(roots):
            trees[root] = []
            time_trackers[root] = {}
            time_trackers[root][root] = 0
            remaining_nodes_list[root] = list(range(self.args.num_hmcs))
            remaining_nodes_list[root].remove(root)
            current_leaves[root] = []
            leaves_list[root] = []
            temp_final_timestep = self.connect_nodes_to_alternate_tree(root, link_map, switch_to_switch, current_leaves[root], trees[root], time_trackers[root], remaining_nodes_list[root], final_timestep, root_idx, True, leaves_list[root])
            if temp_final_timestep > final_timestep:
                final_timestep = temp_final_timestep

        all_done = False
        if not all_done:
            while not all_done:
                all_done = True
                min_len = len(leaves_list[roots[0]])
                for i in range(len(roots)):
                    min_len = min(min_len, len(leaves_list[roots[i]]))
                for i in range(min_len):
                    for root in roots:
                        if len(remaining_nodes_list[root]) == 0:
                            continue
                        to_remove = []
                        leave = leaves_list[root][i]
                        neighbors = switch_to_switch[leave]
                        for neighbor, second in neighbors:
                            if neighbor in remaining_nodes_list[root]:
                                timestep = time_trackers[root][leave]
                                trees[root].append((neighbor, leave, timestep + 1, second))
                                leaves_list[root].append(neighbor)
                                time_trackers[root][neighbor] = timestep + 1
                                if timestep + 1 > final_timestep:
                                    final_timestep = timestep + 1
                                remaining_nodes_list[root].remove(neighbor)
                                to_remove.append((neighbor, second))
                                current_leaves[root].append(neighbor)
                                all_done = False
                                break
                        for node in to_remove:
                            switch_to_switch[leave].remove(node)
        for root in roots:
            assert len(trees[root]) == (self.args.num_hmcs - 1)

        # Check no link is used twice in the disjoint tree sets.
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        for root in roots:
            for edge in trees[root]:
                if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
                    exit()
                else:
                    switch_to_switch[edge[1]].remove((edge[0], edge[3]))
        return trees, final_timestep

    def generate_trees_center(self, roots, collective):
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        link_map = {}
        for node in switch_to_switch.keys():
            for (neighbor, second) in switch_to_switch[node]:
                if (node, neighbor) not in link_map.keys():
                    link_map[(node, neighbor)] = []
                link_map[(node, neighbor)].append(second)
        # print("Link map ready")

        trees = {}
        time_trackers = {}
        remaining_nodes_list = {}
        current_leaves = {}
        final_timestep = 0
        leaves_list = {}
        first_dir_1_values = {}
        first_dir_2_values = {}
        second_dir_values = {}
        first_dir_1_count_values = {}
        first_dir_2_count_values = {}
        second_count_values = {}
        for_second_dim_values = {}
        for_one_nodes_values = {}
        for_two_nodes_values = {}

        # border_nodes, center_nodes = self.get_center_nodes()
        new_roots = []
        for (root_idx, root) in enumerate(roots):
            trees[root] = []
            time_trackers[root] = {}
            time_trackers[root][root] = 0
            remaining_nodes_list[root] = list(range(self.args.num_hmcs))
            remaining_nodes_list[root].remove(root)
            current_leaves[root] = []
            leaves_list[root] = []
            temp_final_timestep, temp_root = self.go_to_border_first(root, link_map, switch_to_switch,
                                                                   current_leaves[root], trees[root],
                                                                   time_trackers[root], remaining_nodes_list[root],
                                                                   final_timestep, root_idx, leaves_list[root])
            new_roots.append(temp_root)

        for (root_idx, root) in enumerate(roots):
            first_dir_1, first_dir_2, second_dir, first_dir_1_count, first_dir_2_count, second_dir_count, for_second_direction = self.get_values(new_roots[root_idx])
            first_dir_1_values[root] = first_dir_1
            first_dir_2_values[root] = first_dir_2
            second_dir_values[root] = second_dir
            first_dir_1_count_values[root] = first_dir_1_count
            first_dir_2_count_values[root] = first_dir_2_count
            second_count_values[root] = second_dir_count
            for_second_dim_values[root] = for_second_direction
            for_second_direction.remove(new_roots[root_idx])

        for (root_idx, root) in enumerate(roots):
            self.connect_first_dim_nodes(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], first_dir_1_values[root], first_dir_2_values[root], first_dir_1_count_values[root], first_dir_2_count_values[root])

        for (root_idx, root) in enumerate(roots):
            temp_final_timestep, for_one_nodes, for_two_nodes = self.connect_nodes_to_alternate_tree_2(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], for_second_dim_values[root], second_count_values[root], second_dir_values[root])
            for_one_nodes_values[root] = for_one_nodes
            for_two_nodes_values[root] = for_two_nodes
            if temp_final_timestep > final_timestep:
                final_timestep = temp_final_timestep

        for (root_idx, root) in enumerate(roots):
            temp_final_timestep = self.connect_side_nodes(for_one_nodes_values[root], for_two_nodes_values[root],
                                                          time_trackers[root],
                                                          first_dir_1_values[root], first_dir_2_values[root],
                                                          second_dir_values[root], link_map, trees[root],
                                                          leaves_list[root], switch_to_switch, current_leaves[root],
                                                          remaining_nodes_list[root], final_timestep)
            if temp_final_timestep > final_timestep:
                final_timestep = temp_final_timestep

        all_done = False
        if not all_done:
            while not all_done:
                all_done = True
                min_len = len(leaves_list[roots[0]])
                for i in range(len(roots)):
                    min_len = min(min_len, len(leaves_list[roots[i]]))
                for i in range(min_len):
                    for root in roots:
                        if len(remaining_nodes_list[root]) == 0:
                            continue
                        to_remove = []
                        leave = leaves_list[root][i]
                        neighbors = switch_to_switch[leave]
                        for neighbor, second in neighbors:
                            if neighbor in remaining_nodes_list[root]:
                                timestep = time_trackers[root][leave]
                                trees[root].append((neighbor, leave, timestep + 1, second))
                                leaves_list[root].append(neighbor)
                                time_trackers[root][neighbor] = timestep + 1
                                if timestep + 1 > final_timestep:
                                    final_timestep = timestep + 1
                                remaining_nodes_list[root].remove(neighbor)
                                to_remove.append((neighbor, second))
                                current_leaves[root].append(neighbor)
                                all_done = False
                                break
                        for node in to_remove:
                            switch_to_switch[leave].remove(node)
        for root in roots:
            assert len(trees[root]) == (self.args.num_hmcs - 1)

        # Check no link is used twice in the disjoint tree sets.
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        for root in roots:
            for edge in trees[root]:
                if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
                    exit()
                else:
                    switch_to_switch[edge[1]].remove((edge[0], edge[3]))
        return trees, final_timestep

    def connect_sm_alter_special_nodes(self, leave, switch_to_switch, remaining_nodes_list, time_trackers, trees, leaves_list, current_leaves, final_timestep):
        special_nodes = {}
        special_nodes[0] = 1
        special_nodes[1] = 0
        special_nodes[self.args.per_dim_nodes-1] = self.args.per_dim_nodes - 1 + self.args.per_dim_nodes
        special_nodes[self.args.per_dim_nodes - 1 + self.args.per_dim_nodes] = self.args.per_dim_nodes - 1
        special_nodes[self.args.num_hmcs-1] = self.args.num_hmcs - 2
        special_nodes[self.args.num_hmcs-2] = self.args.num_hmcs - 1
        special_nodes[self.args.per_dim_nodes * (self.args.per_dim_nodes - 1)] = self.args.per_dim_nodes * (self.args.per_dim_nodes - 2)
        special_nodes[self.args.per_dim_nodes * (self.args.per_dim_nodes - 2)] = self.args.per_dim_nodes * (self.args.per_dim_nodes - 1)

        if leave in special_nodes.keys():
            special_neighbor = special_nodes[leave]
            neighbors = switch_to_switch[leave]
            to_remove = []
            for neighbor, second in neighbors:
                if neighbor != special_neighbor:
                    continue
                if neighbor in remaining_nodes_list:
                    timestep = time_trackers[leave]
                    trees.append((neighbor, leave, timestep + 1, second))
                    leaves_list.append(neighbor)
                    time_trackers[neighbor] = timestep + 1
                    if timestep + 1 > final_timestep:
                        final_timestep = timestep + 1
                    remaining_nodes_list.remove(neighbor)
                    to_remove.append((neighbor, second))
                    current_leaves.append(neighbor)
            for node in to_remove:
                switch_to_switch[leave].remove(node)
        return final_timestep

    def generate_partial_tree_border(self, roots, collective):
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        link_map = {}
        for node in switch_to_switch.keys():
            for (neighbor, second) in switch_to_switch[node]:
                if (node, neighbor) not in link_map.keys():
                    link_map[(node, neighbor)] = []
                link_map[(node, neighbor)].append(second)
        # print("Link map ready")

        trees = {}
        time_trackers = {}
        remaining_nodes_list = {}
        current_leaves = {}
        final_timestep = 0
        leaves_list = {}
        first_dir_1_values = {}
        first_dir_2_values = {}
        second_dir_values = {}
        first_dir_1_count_values = {}
        first_dir_2_count_values = {}
        second_count_values = {}
        for_second_dim_values = {}
        for_one_nodes_values = {}
        for_two_nodes_values = {}

        # directions = [('Top', 'Bottom'), ('Right', 'Left'), ('Bottom', 'Top'), ('Left', 'Right')]
        # for root in roots:
        #     col_idx = root % self.args.per_dim_nodes
        #     row_idx = math.floor(root / self.args.per_dim_nodes)
        #     if row_idx == 0:
        #         directions.remove(('Top', 'Bottom'))
        #     elif row_idx == self.args.per_dim_nodes - 1:
        #         directions.remove(('Bottom', 'Top'))
        #     elif col_idx == 0:
        #         directions.remove(('Left', 'Right'))
        #     elif col_idx == self.args.per_dim_nodes - 1:
        #         directions.remove(('Right', 'Left'))

        border_nodes, center_nodes = self.get_center_nodes()
        new_roots = []
        for (root_idx, root) in enumerate(roots):
            trees[root] = []
            time_trackers[root] = {}
            time_trackers[root][root] = 0
            remaining_nodes_list[root] = list(range(self.args.num_hmcs))
            remaining_nodes_list[root].remove(root)
            current_leaves[root] = []
            leaves_list[root] = [root]
            assert root in border_nodes
            current_leaves[root].append(root)
            new_roots.append(root)
            # else:
            #     towards_border, towards_opposite = directions.pop(0)
            #     temp_final_timestep, temp_root = self.go_to_border_first_2(root, link_map, switch_to_switch,
            #                                                            current_leaves[root], trees[root],
            #                                                            time_trackers[root], remaining_nodes_list[root],
            #                                                            final_timestep, root_idx, leaves_list[root], towards_border, towards_opposite)
            #     new_roots.append(temp_root)

        for (root_idx, root) in enumerate(roots):
            first_dir_1, first_dir_2, second_dir, first_dir_1_count, first_dir_2_count, second_dir_count, for_second_direction = self.get_values(new_roots[root_idx])
            first_dir_1_values[root] = first_dir_1
            first_dir_2_values[root] = first_dir_2
            second_dir_values[root] = second_dir
            first_dir_1_count_values[root] = first_dir_1_count
            first_dir_2_count_values[root] = first_dir_2_count
            second_count_values[root] = second_dir_count
            for_second_dim_values[root] = for_second_direction
            if root not in border_nodes:
                for_second_direction.remove(new_roots[root_idx])

        for (root_idx, root) in enumerate(roots):
            self.connect_first_dim_nodes(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], first_dir_1_values[root], first_dir_2_values[root], first_dir_1_count_values[root], first_dir_2_count_values[root])

        for (root_idx, root) in enumerate(roots):
            temp_final_timestep, for_one_nodes, for_two_nodes = self.connect_nodes_to_alternate_tree_2(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], for_second_dim_values[root], second_count_values[root], second_dir_values[root])
            for_one_nodes_values[root] = for_one_nodes
            for_two_nodes_values[root] = for_two_nodes
            if temp_final_timestep > final_timestep:
                final_timestep = temp_final_timestep

        # for (root_idx, root) in enumerate(roots):
        #     temp_final_timestep = self.connect_side_nodes(for_one_nodes_values[root], for_two_nodes_values[root],
        #                                                   time_trackers[root],
        #                                                   first_dir_1_values[root], first_dir_2_values[root],
        #                                                   second_dir_values[root], link_map, trees[root],
        #                                                   leaves_list[root], switch_to_switch, current_leaves[root],
        #                                                   remaining_nodes_list[root], final_timestep)
        #     if temp_final_timestep > final_timestep:
        #         final_timestep = temp_final_timestep

        # for root in roots:
        #     leaves = leaves_list[root]
        #     for leave in leaves:
        #         if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
        #             temp_final_timestep = self.connect_sm_alter_special_nodes(leave, switch_to_switch,
        #                                                                       remaining_nodes_list[root], time_trackers[root],
        #                                                                       trees[root], leaves_list[root], current_leaves[root],
        #                                                                       final_timestep)
        #             if temp_final_timestep > final_timestep:
        #                 final_timestep = temp_final_timestep

        all_done = False
        if not all_done:
            while not all_done:
                all_done = True

                bfs_leaves = {}
                for root in roots:
                    leaves = leaves_list[root]
                    priority_leaves = []
                    non_priority_leaves = []
                    for leave in leaves:
                        neighbors = switch_to_switch[leave]
                        for neighbor, second in neighbors:
                            if neighbor in remaining_nodes_list[root]:
                                if leave in border_nodes:
                                    priority_leaves.append(leave)
                                elif second:
                                    non_priority_leaves.append(leave)
                                elif not second:
                                    priority_leaves.append(leave)
                                break
                    # if root == 21:
                    #     print("Yo")
                    bfs_leaves[root] = priority_leaves
                    bfs_leaves[root].extend(non_priority_leaves)
                # min_len = len(leaves_list[roots[0]])
                # for i in range(len(roots)):
                #     min_len = min(min_len, len(leaves_list[roots[i]]))
                # for i in range(min_len):
                for root in roots:
                    if len(remaining_nodes_list[root]) == 0:
                        continue
                    to_remove = []
                    # leave = leaves_list[root][i]
                    try:
                        leave = bfs_leaves[root][0]
                    except Exception as e:
                        print("Here")
                    neighbors = switch_to_switch[leave]
                    for neighbor, second in neighbors:
                        if neighbor in remaining_nodes_list[root]:
                            timestep = time_trackers[root][leave]
                            trees[root].append((neighbor, leave, timestep + 1, second))
                            leaves_list[root].append(neighbor)
                            time_trackers[root][neighbor] = timestep + 1
                            if timestep + 1 > final_timestep:
                                final_timestep = timestep + 1
                            remaining_nodes_list[root].remove(neighbor)
                            to_remove.append((neighbor, second))
                            current_leaves[root].append(neighbor)
                            # if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
                            #     temp_final_timestep = self.connect_sm_alter_special_nodes(leave, switch_to_switch,
                            #                                                               remaining_nodes_list[root],
                            #                                                               time_trackers[root],
                            #                                                               trees[root],
                            #                                                               leaves_list[root],
                            #                                                               current_leaves[root],
                            #                                                               final_timestep)
                            #     if temp_final_timestep > final_timestep:
                            #         final_timestep = temp_final_timestep
                            all_done = False
                            break
                    for node in to_remove:
                        switch_to_switch[leave].remove(node)
        for root in roots:
            assert len(trees[root]) == (self.args.num_hmcs - 1)

        # Check no link is used twice in the disjoint tree sets.
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        for root in roots:
            for edge in trees[root]:
                if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
                    exit()
                else:
                    switch_to_switch[edge[1]].remove((edge[0], edge[3]))
        return trees, final_timestep

    def generate_other_trees_three(self, roots, collective):
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        link_map = {}
        for node in switch_to_switch.keys():
            for (neighbor, second) in switch_to_switch[node]:
                if (node, neighbor) not in link_map.keys():
                    link_map[(node, neighbor)] = []
                link_map[(node, neighbor)].append(second)
        # print("Link map ready")

        trees = {}
        time_trackers = {}
        remaining_nodes_list = {}
        current_leaves = {}
        final_timestep = 0
        leaves_list = {}
        first_dir_1_values = {}
        first_dir_2_values = {}
        second_dir_values = {}
        first_dir_1_count_values = {}
        first_dir_2_count_values = {}
        second_count_values = {}
        for_second_dim_values = {}
        for_one_nodes_values = {}
        for_two_nodes_values = {}

        directions = [('Top', 'Bottom'), ('Right', 'Left'), ('Bottom', 'Top'), ('Left', 'Right')]
        for root in roots:
            col_idx = root % self.args.per_dim_nodes
            row_idx = math.floor(root / self.args.per_dim_nodes)
            if row_idx == 0:
                directions.remove(('Top', 'Bottom'))
            elif row_idx == self.args.per_dim_nodes - 1:
                directions.remove(('Bottom', 'Top'))
            elif col_idx == 0:
                directions.remove(('Left', 'Right'))
            elif col_idx == self.args.per_dim_nodes - 1:
                directions.remove(('Right', 'Left'))

        border_nodes, center_nodes = self.get_center_nodes()
        new_roots = []
        for (root_idx, root) in enumerate(roots):
            trees[root] = []
            time_trackers[root] = {}
            time_trackers[root][root] = 0
            remaining_nodes_list[root] = list(range(self.args.num_hmcs))
            remaining_nodes_list[root].remove(root)
            current_leaves[root] = []
            leaves_list[root] = [root]
            if root in border_nodes:
                current_leaves[root].append(root)
                new_roots.append(root)
            else:
                towards_border, towards_opposite = directions.pop(0)
                temp_final_timestep, temp_root = self.go_to_border_first_2(root, link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root], remaining_nodes_list[root],
                                                                       final_timestep, root_idx, leaves_list[root], towards_border, towards_opposite)
                new_roots.append(temp_root)

        for (root_idx, root) in enumerate(roots):
            first_dir_1, first_dir_2, second_dir, first_dir_1_count, first_dir_2_count, second_dir_count, for_second_direction = self.get_values(new_roots[root_idx])
            first_dir_1_values[root] = first_dir_1
            first_dir_2_values[root] = first_dir_2
            second_dir_values[root] = second_dir
            first_dir_1_count_values[root] = first_dir_1_count
            first_dir_2_count_values[root] = first_dir_2_count
            second_count_values[root] = second_dir_count
            for_second_dim_values[root] = for_second_direction
            if root not in border_nodes:
                for_second_direction.remove(new_roots[root_idx])

        for (root_idx, root) in enumerate(roots):
            self.connect_first_dim_nodes(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], first_dir_1_values[root], first_dir_2_values[root], first_dir_1_count_values[root], first_dir_2_count_values[root])

        for (root_idx, root) in enumerate(roots):
            temp_final_timestep, for_one_nodes, for_two_nodes = self.connect_nodes_to_alternate_tree_2(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], for_second_dim_values[root], second_count_values[root], second_dir_values[root])
            for_one_nodes_values[root] = for_one_nodes
            for_two_nodes_values[root] = for_two_nodes
            if temp_final_timestep > final_timestep:
                final_timestep = temp_final_timestep

        # for (root_idx, root) in enumerate(roots):
        #     temp_final_timestep = self.connect_side_nodes(for_one_nodes_values[root], for_two_nodes_values[root],
        #                                                   time_trackers[root],
        #                                                   first_dir_1_values[root], first_dir_2_values[root],
        #                                                   second_dir_values[root], link_map, trees[root],
        #                                                   leaves_list[root], switch_to_switch, current_leaves[root],
        #                                                   remaining_nodes_list[root], final_timestep)
        #     if temp_final_timestep > final_timestep:
        #         final_timestep = temp_final_timestep

        # for root in roots:
        #     leaves = leaves_list[root]
        #     for leave in leaves:
        #         if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
        #             temp_final_timestep = self.connect_sm_alter_special_nodes(leave, switch_to_switch,
        #                                                                       remaining_nodes_list[root], time_trackers[root],
        #                                                                       trees[root], leaves_list[root], current_leaves[root],
        #                                                                       final_timestep)
        #             if temp_final_timestep > final_timestep:
        #                 final_timestep = temp_final_timestep

        all_done = False
        if not all_done:
            while not all_done:
                all_done = True

                bfs_leaves = {}
                for root in roots:
                    leaves = leaves_list[root]
                    priority_leaves = []
                    non_priority_leaves = []
                    for leave in leaves:
                        neighbors = switch_to_switch[leave]
                        for neighbor, second in neighbors:
                            if neighbor in remaining_nodes_list[root]:
                                if leave in border_nodes:
                                    priority_leaves.append(leave)
                                elif second:
                                    non_priority_leaves.append(leave)
                                elif not second:
                                    priority_leaves.append(leave)
                                break
                    # if root == 21:
                    #     print("Yo")
                    bfs_leaves[root] = priority_leaves
                    bfs_leaves[root].extend(non_priority_leaves)
                # min_len = len(leaves_list[roots[0]])
                # for i in range(len(roots)):
                #     min_len = min(min_len, len(leaves_list[roots[i]]))
                # for i in range(min_len):
                for root in roots:
                    if len(remaining_nodes_list[root]) == 0:
                        continue
                    to_remove = []
                    # leave = leaves_list[root][i]
                    leave = bfs_leaves[root][0]
                    neighbors = switch_to_switch[leave]
                    for neighbor, second in neighbors:
                        if neighbor in remaining_nodes_list[root]:
                            timestep = time_trackers[root][leave]
                            trees[root].append((neighbor, leave, timestep + 1, second))
                            leaves_list[root].append(neighbor)
                            time_trackers[root][neighbor] = timestep + 1
                            if timestep + 1 > final_timestep:
                                final_timestep = timestep + 1
                            remaining_nodes_list[root].remove(neighbor)
                            to_remove.append((neighbor, second))
                            current_leaves[root].append(neighbor)
                            # if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
                            #     temp_final_timestep = self.connect_sm_alter_special_nodes(leave, switch_to_switch,
                            #                                                               remaining_nodes_list[root],
                            #                                                               time_trackers[root],
                            #                                                               trees[root],
                            #                                                               leaves_list[root],
                            #                                                               current_leaves[root],
                            #                                                               final_timestep)
                            #     if temp_final_timestep > final_timestep:
                            #         final_timestep = temp_final_timestep
                            all_done = False
                            break
                    for node in to_remove:
                        switch_to_switch[leave].remove(node)
        for root in roots:
            assert len(trees[root]) == (self.args.num_hmcs - 1)

        # Check no link is used twice in the disjoint tree sets.
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        for root in roots:
            for edge in trees[root]:
                if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
                    exit()
                else:
                    switch_to_switch[edge[1]].remove((edge[0], edge[3]))
        return trees, final_timestep

    def generate_other_trees_sm_bi_odd(self, roots, collective):
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        link_map = {}
        for node in switch_to_switch.keys():
            for (neighbor, second) in switch_to_switch[node]:
                if (node, neighbor) not in link_map.keys():
                    link_map[(node, neighbor)] = []
                link_map[(node, neighbor)].append(second)
        # print("Link map ready")

        trees = {}
        time_trackers = {}
        remaining_nodes_list = {}
        current_leaves = {}
        final_timestep = 0
        leaves_list = {}
        first_dir_1_values = {}
        first_dir_2_values = {}
        second_dir_values = {}
        first_dir_1_count_values = {}
        first_dir_2_count_values = {}
        second_count_values = {}
        for_second_dim_values = {}
        for_one_nodes_values = {}
        for_two_nodes_values = {}
        center_tracker = {}

        directions = [('Top', 'Bottom'), ('Right', 'Left'), ('Bottom', 'Top'), ('Left', 'Right')]
        for root in roots:
            col_idx = root % self.args.per_dim_nodes
            row_idx = math.floor(root / self.args.per_dim_nodes)
            if row_idx == 0:
                directions.remove(('Top', 'Bottom'))
            elif row_idx == self.args.per_dim_nodes - 1:
                directions.remove(('Bottom', 'Top'))
            elif col_idx == 0:
                directions.remove(('Left', 'Right'))
            elif col_idx == self.args.per_dim_nodes - 1:
                directions.remove(('Right', 'Left'))

        border_nodes, center_nodes = self.get_center_nodes()
        new_roots = []
        for (root_idx, root) in enumerate(roots):
            trees[root] = []
            time_trackers[root] = {}
            time_trackers[root][root] = 0
            remaining_nodes_list[root] = list(range(self.args.num_hmcs))
            remaining_nodes_list[root].remove(root)
            current_leaves[root] = []
            leaves_list[root] = [root]
            center_tracker[root] = {}
            for i in range(self.args.num_hmcs):
                center_tracker[root][i] = 0
            if root in border_nodes:
                current_leaves[root].append(root)
                new_roots.append(root)
            else:
                towards_border, towards_opposite = directions.pop(0)
                temp_final_timestep, temp_root = self.go_to_border_first_sm_bi(root, link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root], remaining_nodes_list[root],
                                                                       final_timestep, root_idx, leaves_list[root], center_tracker[root])
                new_roots.append(temp_root)

        for (root_idx, root) in enumerate(roots):
            first_dir_1, first_dir_2, second_dir, first_dir_1_count, first_dir_2_count, second_dir_count, for_second_direction = self.get_values(new_roots[root_idx])
            first_dir_1_values[root] = first_dir_1
            first_dir_2_values[root] = first_dir_2
            second_dir_values[root] = second_dir
            first_dir_1_count_values[root] = first_dir_1_count
            first_dir_2_count_values[root] = first_dir_2_count
            second_count_values[root] = second_dir_count
            for_second_dim_values[root] = for_second_direction
            if root not in border_nodes:
                for_second_direction.remove(new_roots[root_idx])

        for (root_idx, root) in enumerate(roots):
            self.connect_first_dim_nodes_sm_bi(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], first_dir_1_values[root], first_dir_2_values[root], first_dir_1_count_values[root], first_dir_2_count_values[root], center_tracker[root])

        for (root_idx, root) in enumerate(roots):
            temp_final_timestep, for_one_nodes, for_two_nodes = self.connect_nodes_to_alternate_tree_2_sm_bi(new_roots[root_idx], link_map, switch_to_switch,
                                                                       current_leaves[root], trees[root],
                                                                       time_trackers[root],
                                                                       remaining_nodes_list[root], final_timestep,
                                                                       root_idx, False, leaves_list[root], for_second_dim_values[root], second_count_values[root], second_dir_values[root], center_tracker[root])
            for_one_nodes_values[root] = for_one_nodes
            for_two_nodes_values[root] = for_two_nodes
            if temp_final_timestep > final_timestep:
                final_timestep = temp_final_timestep

        # for (root_idx, root) in enumerate(roots):
        #     temp_final_timestep = self.connect_side_nodes(for_one_nodes_values[root], for_two_nodes_values[root],
        #                                                   time_trackers[root],
        #                                                   first_dir_1_values[root], first_dir_2_values[root],
        #                                                   second_dir_values[root], link_map, trees[root],
        #                                                   leaves_list[root], switch_to_switch, current_leaves[root],
        #                                                   remaining_nodes_list[root], final_timestep)
        #     if temp_final_timestep > final_timestep:
        #         final_timestep = temp_final_timestep

        # for root in roots:
        #     leaves = leaves_list[root]
        #     for leave in leaves:
        #         if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
        #             temp_final_timestep = self.connect_sm_alter_special_nodes(leave, switch_to_switch,
        #                                                                       remaining_nodes_list[root], time_trackers[root],
        #                                                                       trees[root], leaves_list[root], current_leaves[root],
        #                                                                       final_timestep)
        #             if temp_final_timestep > final_timestep:
        #                 final_timestep = temp_final_timestep

        all_done = False
        if not all_done:
            while not all_done:
                all_done = True

                bfs_leaves = {}
                for root in roots:
                    leaves = leaves_list[root]
                    priority_leaves = []
                    non_priority_leaves = []
                    for leave in leaves:
                        neighbors = switch_to_switch[leave]
                        for neighbor, second in neighbors:
                            if neighbor in remaining_nodes_list[root]:
                                if leave in center_nodes and neighbor in center_nodes and center_tracker[root][leave] == 1:
                                    continue
                                if leave in border_nodes:
                                    priority_leaves.append(leave)
                                elif second:
                                    non_priority_leaves.append(leave)
                                elif not second:
                                    priority_leaves.append(leave)
                                break
                    # if root == 21:
                    #     print("Yo")
                    bfs_leaves[root] = priority_leaves
                    bfs_leaves[root].extend(non_priority_leaves)
                # min_len = len(leaves_list[roots[0]])
                # for i in range(len(roots)):
                #     min_len = min(min_len, len(leaves_list[roots[i]]))
                # for i in range(min_len):
                for root in roots:
                    if len(remaining_nodes_list[root]) == 0 or len(bfs_leaves[root]) == 0:
                        continue
                    to_remove = []
                    # leave = leaves_list[root][i]
                    leave = bfs_leaves[root][0]
                    neighbors = switch_to_switch[leave]

                    for neighbor, second in neighbors:
                        if neighbor in remaining_nodes_list[root]:
                            if leave in center_nodes and neighbor in center_nodes and center_tracker[root][leave] == 1:
                                continue
                            if root == 14 and neighbor == 25:
                                print("Yo")
                            timestep = time_trackers[root][leave]
                            trees[root].append((neighbor, leave, timestep + 1, second))
                            leaves_list[root].append(neighbor)
                            time_trackers[root][neighbor] = timestep + 1
                            if timestep + 1 > final_timestep:
                                final_timestep = timestep + 1
                            remaining_nodes_list[root].remove(neighbor)
                            to_remove.append((neighbor, second))
                            current_leaves[root].append(neighbor)
                            if leave in center_nodes and neighbor in center_nodes:
                                center_tracker[root][leave] = 1
                            # if self.args.booksim_network == 'SM_Alter' and self.args.per_dim_nodes % 2 != 0:
                            #     temp_final_timestep = self.connect_sm_alter_special_nodes(leave, switch_to_switch,
                            #                                                               remaining_nodes_list[root],
                            #                                                               time_trackers[root],
                            #                                                               trees[root],
                            #                                                               leaves_list[root],
                            #                                                               current_leaves[root],
                            #                                                               final_timestep)
                            #     if temp_final_timestep > final_timestep:
                            #         final_timestep = temp_final_timestep
                            all_done = False
                            break
                    for node in to_remove:
                        switch_to_switch[leave].remove(node)

        all_done = True
        for root in roots:
            if len(trees[root]) != (self.args.num_hmcs - 1):
                all_done = False

        if not all_done:
            final_leaves = {}
            for root in roots:
                leaves = leaves_list[root]
                priority_leaves = []
                non_priority_leaves = []
                for leave in leaves:
                    neighbors = switch_to_switch[leave]
                    for neighbor, second in neighbors:
                        if neighbor in remaining_nodes_list[root]:
                            if leave in border_nodes:
                                priority_leaves.append(leave)
                            elif second:
                                non_priority_leaves.append(leave)
                            elif not second:
                                priority_leaves.append(leave)
                            break
                final_leaves[root] = priority_leaves
                final_leaves[root].extend(non_priority_leaves)
            while not all_done:
                # all_done = True
                for root in roots:
                    if len(remaining_nodes_list[root]) == 0:
                        continue
                    to_remove = []
                    # leave = leaves_list[root][i]
                    leave = final_leaves[root][0]
                    neighbors = switch_to_switch[leave]
                    remove_leave = True
                    for neighbor, second in neighbors:
                        if neighbor in remaining_nodes_list[root]:
                            # if leave in center_nodes and neighbor in center_nodes and center_tracker[root][leave] == 1:
                            #     continue
                            # if root == 14 and neighbor == 25:
                            #     print("Yo")
                            timestep = time_trackers[root][leave]
                            trees[root].append((neighbor, leave, timestep + 1, second))
                            leaves_list[root].append(neighbor)
                            time_trackers[root][neighbor] = timestep + 1
                            if timestep + 1 > final_timestep:
                                final_timestep = timestep + 1
                            remaining_nodes_list[root].remove(neighbor)
                            to_remove.append((neighbor, second))
                            current_leaves[root].append(neighbor)
                            final_leaves[root].append(neighbor)
                            if leave in center_nodes and neighbor in center_nodes:
                                center_tracker[root][leave] = 1
                            remove_leave = False
                            # all_done = False
                            break
                    for node in to_remove:
                        switch_to_switch[leave].remove(node)
                    if remove_leave:
                        final_leaves[root].pop(0)
                all_done = True
                for root in roots:
                    if len(trees[root]) != (self.args.num_hmcs - 1):
                        all_done = False
                # print("Inside Loop")


        for root in roots:
            assert len(trees[root]) == (self.args.num_hmcs - 1)

        # Check no link is used twice in the disjoint tree sets.
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        for root in roots:
            for edge in trees[root]:
                if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
                    exit()
                else:
                    switch_to_switch[edge[1]].remove((edge[0], edge[3]))
        return trees, final_timestep

    def compute_multitree_trees(self, roots, collective, sort=True):
        trees = {}
        tree_nodes = {}
        # for node in range(self.network.nodes):
        for node in roots:
            trees[node] = []
            tree_nodes[node] = [node]

        timesteps = 0
        # sorted_roots = list(range(self.network.nodes))
        sorted_roots = roots

        changed_tracker = []
        for i in range(self.network.nodes):
            changed_tracker.append(False)
        finished = False
        while not finished:
            if collective == 'RS':
                switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
            else:
                switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)
            last_tree_nodes = copy.deepcopy(tree_nodes)

            changed = True
            turns = 0
            while changed:
                changed = False
                root = sorted_roots[turns % len(roots)]
                if len(tree_nodes[root]) < self.network.nodes:
                    for parent in last_tree_nodes[root]:
                        if not changed:
                            neighbor_switches = copy.deepcopy(switch_to_switch[parent])
                            for (child, second) in neighbor_switches:
                                if child not in tree_nodes[root]:
                                    switch_to_switch[parent].remove((child, second))
                                    tree_nodes[root].append(child)
                                    trees[root].append((child, parent, timesteps, second))
                                    changed = True
                                    break
                                if changed:
                                    break
                        if changed:
                            break

                turns += 1
                changed_tracker[root] = changed

                if turns % len(roots) != 0:
                    changed = True
                else:
                    if sort:
                        # sorted_roots = list(range(self.network.nodes))
                        sorted_roots = roots
                        sorted_roots = [root for _, root in sorted(zip(self.network.priority, sorted_roots), reverse=True)]
                    if any(changed_tracker):
                        changed = True
                    num_trees = 0
                    # for i in range(self.network.nodes):
                    for i in roots:
                        changed_tracker[i] = False
                        if len(tree_nodes[i]) == self.network.nodes:
                            num_trees += 1
                    if num_trees == len(roots):
                        finished = True
                        break
            timesteps += 1

        # Check no link is used twice in same timestpe.
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)
        final_link_checker = {}
        for i in range(timesteps):
            final_link_checker[i] = copy.deepcopy(switch_to_switch)

        # for i in range(self.network.nodes):
        for i in roots:
            for edge in trees[i]:
                if (edge[0], edge[3]) not in final_link_checker[edge[2]][edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used more than availability in timestep " + str(edge[2]))
                    exit()
                else:
                    final_link_checker[edge[2]][edge[1]].remove((edge[0], edge[3]))

        return trees, timesteps


    def get_neighboring_border_nodes(self, leave, remaining_nodes, border_nodes, switch_to_switch):
        current_neighbors = switch_to_switch[leave]
        border_leaves = []
        border_leaves_node = []
        for (neighbor, second) in current_neighbors:
            if neighbor in border_nodes and neighbor in remaining_nodes and neighbor not in border_leaves_node:
                border_leaves.append((neighbor, second))
                border_leaves_node.append(neighbor)
        return border_leaves

    def generate_tree_three(self, roots, collective):
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        total_nodes = self.args.num_hmcs
        border_nodes, center_nodes = self.get_center_nodes()

        trees = {}
        time_trackers = {}
        remaining_nodes_list = {}
        current_leaves = {}
        backup_leaves = {}
        current_leaves_toward_one_dim = {}
        current_leaves_toward_border = {}
        current_leaves_for_all_border = {}
        final_timestep = 0
        leaves_order = {}
        center_tracker = {}
        for root in roots:
            trees[root] = []
            time_trackers[root] = {}
            time_trackers[root][root] = 0
            remaining_nodes_list[root] = list(range(total_nodes))
            remaining_nodes_list[root].remove(root)
            current_leaves[root] = []
            backup_leaves[root] = [root]
            current_leaves_toward_one_dim[root] = []
            current_leaves_for_all_border[root] = []
            current_leaves_toward_border[root] = [root]
            leaves_order[root] = [root]
            center_tracker[root] = {}
            for i in range(total_nodes):
                center_tracker[root][i] = 0

        # Go To Border Nodes First
        # if roots[0] not in border_nodes:
        #     borders_reached = False
        #     while not borders_reached:
        #         borders_reached = True
        #         for root_index, root in enumerate(roots):
        #             leave = current_leaves_toward_border[root][0]
        #             link_to_remove = []
        #
        #             left, right, top, bottom = self.get_lrtb(leave, self.args.per_dim_nodes)
        #             if root_index == 0:
        #                 selected_leave = top
        #             elif root_index == 1:
        #                 selected_leave = right
        #             elif root_index == 2:
        #                 selected_leave = bottom
        #             elif root_index == 3:
        #                 selected_leave = left
        #             else:
        #                 raise RuntimeError("Wrong root index")
        #             col_idx = selected_leave % self.args.per_dim_nodes
        #             row_idx = math.floor(selected_leave / self.args.per_dim_nodes)
        #             timestep = time_trackers[root][leave]
        #             trees[root].append((selected_leave, leave, timestep + 1, 1))
        #             leaves_order[root].append(selected_leave)
        #             if leave in center_nodes and selected_leave in center_nodes:
        #                 leaves_order[root].remove(leave)
        #                 center_tracker[root][leave] = 1
        #             time_trackers[root][selected_leave] = timestep + 1
        #             if timestep + 1 > final_timestep:
        #                 final_timestep = timestep + 1
        #             remaining_nodes_list[root].remove(selected_leave)
        #             if col_idx == 0 or row_idx == 0 or col_idx == self.args.per_dim_nodes - 1 or row_idx == self.args.per_dim_nodes - 1:
        #                 current_leaves_toward_one_dim[root].append(selected_leave)
        #                 current_leaves[root].append(selected_leave)
        #             else:
        #                 current_leaves_toward_border[root].append(selected_leave)
        #                 backup_leaves[root].append(selected_leave)
        #                 borders_reached = False
        #             link_to_remove.append((selected_leave, 1))
        #             current_leaves_toward_border[root].remove(leave)
        #             for link in link_to_remove:
        #                 switch_to_switch[leave].remove(link)
        #         for root in roots:
        #             if len(current_leaves_toward_border[root]) > 0:
        #                 borders_reached = False
        #                 break

        # if len(current_leaves_toward_one_dim[roots[0]]) == 0:
        #     for root in roots:
        #         current_leaves_toward_one_dim[root].append(root)

        if len(current_leaves[roots[0]]) == 0:
            for root in roots:
                current_leaves[root].append(root)

        # # Connect all the outer nodes in a single dimension first
        # all_borders_of_roots_handled = False
        # while not all_borders_of_roots_handled:
        #     all_borders_of_roots_handled = True
        #     for root_index, root in enumerate(roots):
        #         leave = current_leaves_toward_one_dim[root][0]
        #         link_to_remove = []
        #         # Figure out neighboring nodes of border nodes
        #         neighboring_leaves = self.get_neighboring_border_nodes(leave, remaining_nodes_list[root],
        #                                                                border_nodes, switch_to_switch)
        #         for (neighbor, second) in neighboring_leaves:
        #             col_idx = neighbor % self.args.per_dim_nodes
        #             row_idx = math.floor(neighbor / self.args.per_dim_nodes)
        #             if root_index == 0:
        #                 if row_idx != 0:
        #                     continue
        #             elif root_index == 1:
        #                 if col_idx != self.args.per_dim_nodes - 1:
        #                     continue
        #             elif root_index == 2:
        #                 if row_idx != self.args.per_dim_nodes - 1:
        #                     continue
        #             elif root_index == 3:
        #                 if col_idx != 0:
        #                     continue
        #             timestep = time_trackers[root][leave]
        #             trees[root].append((neighbor, leave, timestep + 1, second))
        #             time_trackers[root][neighbor] = timestep + 1
        #             leaves_order[root].append(neighbor)
        #             if timestep + 1 > final_timestep:
        #                 final_timestep = timestep + 1
        #             remaining_nodes_list[root].remove(neighbor)
        #             current_leaves[root].append(neighbor)
        #             current_leaves_toward_one_dim[root].append(neighbor)
        #             link_to_remove.append((neighbor, second))
        #             all_borders_of_roots_handled = False
        #         current_leaves_toward_one_dim[root].remove(leave)
        #         current_leaves_for_all_border[root].append(leave)
        #         for link in link_to_remove:
        #             switch_to_switch[leave].remove(link)
        #     for root in roots:
        #         if len(current_leaves_toward_one_dim[root]) > 0:
        #             all_borders_of_roots_handled = False
        #             break
        #
        # # Connect all the outer nodes first
        # all_borders_of_roots_handled = False
        # while not all_borders_of_roots_handled:
        #     all_borders_of_roots_handled = True
        #     for root_index, root in enumerate(roots):
        #         leave = current_leaves_for_all_border[root][0]
        #         link_to_remove = []
        #         # Figure out neighboring nodes of border nodes
        #         neighboring_leaves = self.get_neighboring_border_nodes(leave, remaining_nodes_list[root], border_nodes, switch_to_switch)
        #         for (neighbor, second) in neighboring_leaves:
        #             timestep = time_trackers[root][leave]
        #             trees[root].append((neighbor, leave, timestep + 1, second))
        #             time_trackers[root][neighbor] = timestep + 1
        #             leaves_order[root].append(neighbor)
        #             if timestep + 1 > final_timestep:
        #                 final_timestep = timestep + 1
        #             remaining_nodes_list[root].remove(neighbor)
        #             current_leaves[root].append(neighbor)
        #             current_leaves_for_all_border[root].append(neighbor)
        #             link_to_remove.append((neighbor, second))
        #             all_borders_of_roots_handled = False
        #         current_leaves_for_all_border[root].remove(leave)
        #         for link in link_to_remove:
        #             switch_to_switch[leave].remove(link)
        #     for root in roots:
        #         if len(current_leaves_for_all_border[root]) > 0:
        #             all_borders_of_roots_handled = False
        #             break

        all_done = False
        while not all_done:
            # if len(trees[0]) == 41:
            #     print("Yo")
            for root in roots:
                if len(current_leaves[root]) == 0 or len(remaining_nodes_list[root]) == 0:
                    continue
                to_remove = []
                leave = current_leaves[root][0]
                neighbors = switch_to_switch[leave]
                need_to_remove = True
                for neighbor, second in neighbors:
                    # if neighbor in backup_leaves[root]:
                    #     current_leaves[root].append(neighbor)
                    #     backup_leaves[root].remove(neighbor)
                    if leave in center_nodes and neighbor in center_nodes and center_tracker[root][leave] == 1:
                        continue
                    if neighbor in remaining_nodes_list[root]:
                        timestep = time_trackers[root][leave]
                        trees[root].append((neighbor, leave, timestep + 1, second))
                        time_trackers[root][neighbor] = timestep + 1
                        leaves_order[root].append(neighbor)
                        if leave in center_nodes and neighbor in center_nodes:
                            leaves_order[root].remove(leave)
                            center_tracker[root][leave] = 1
                        if timestep + 1 > final_timestep:
                            final_timestep = timestep + 1
                        remaining_nodes_list[root].remove(neighbor)
                        to_remove.append((neighbor, second))
                        current_leaves[root].append(neighbor)
                        # if leave not in center_nodes or neighbor not in center_nodes:
                        need_to_remove = False
                        break
                if need_to_remove:
                    current_leaves[root].remove(leave)
                for node in to_remove:
                    switch_to_switch[leave].remove(node)
            done = True
            for root in roots:
                if len(current_leaves[root]) != 0 and len(remaining_nodes_list[root]) != 0:
                    done = False
            if done:
                all_done = True

        all_done = True
        for root in roots:
            if len(trees[root]) != (total_nodes - 1):
                all_done = False
                break

        if not all_done:
            while not all_done:
                all_done = True
                min_len = len(leaves_order[roots[0]])
                for i in range(len(roots)):
                    min_len = min(min_len, len(leaves_order[roots[i]]))
                for i in range(min_len):
                    for root in roots:
                        if len(remaining_nodes_list[root]) == 0:
                            continue
                        to_remove = []
                        leave = leaves_order[root][i]
                        neighbors = switch_to_switch[leave]
                        for neighbor, second in neighbors:
                            if leave in center_nodes and neighbor in center_nodes and center_tracker[root][leave] == 1:
                                continue
                            if neighbor in remaining_nodes_list[root]:
                                timestep = time_trackers[root][leave]
                                trees[root].append((neighbor, leave, timestep + 1, second))
                                time_trackers[root][neighbor] = timestep + 1
                                leaves_order[root].append(neighbor)
                                if leave in center_nodes and neighbor in center_nodes:
                                    leaves_order[root].remove(leave)
                                    center_tracker[root][leave] = 1
                                if timestep + 1 > final_timestep:
                                    final_timestep = timestep + 1
                                remaining_nodes_list[root].remove(neighbor)
                                to_remove.append((neighbor, second))
                                current_leaves[root].append(neighbor)
                                all_done = False
                                break
                        for node in to_remove:
                            switch_to_switch[leave].remove(node)




        for root in roots:
            assert len(trees[root]) == (total_nodes - 1)

        # Check no link is used twice in the disjoint tree sets.
        if collective == 'RS':
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)

        for root in roots:
            for edge in trees[root]:
                if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
                    exit()
                else:
                    switch_to_switch[edge[1]].remove((edge[0], edge[3]))
        return trees, final_timestep

    def connect_nodes_to_uni_tree(self, first_direction, second_direction, root):
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

    def build_trees_unidirectional_ag(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        top_left_tree = self.connect_nodes_to_uni_tree('right', 'bottom', 0)
        top_right_tree = self.connect_nodes_to_uni_tree('bottom', 'left', per_dim_nodes - 1)
        bottom_right_tree = self.connect_nodes_to_uni_tree('left', 'top', total_nodes - 1)
        bottom_left_tree = self.connect_nodes_to_uni_tree('top', 'right', per_dim_nodes * (per_dim_nodes - 1))
        self.timesteps = 2 * per_dim_nodes - 2
        return top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree

    def build_trees_unidirectional_rs(self):
        total_nodes = self.args.num_hmcs
        per_dim_nodes = int(math.sqrt(total_nodes))
        top_left_tree = self.connect_nodes_to_uni_tree('bottom', 'right', 0)
        top_right_tree = self.connect_nodes_to_uni_tree('left', 'bottom', per_dim_nodes - 1)
        bottom_right_tree = self.connect_nodes_to_uni_tree('top', 'left', total_nodes - 1)
        bottom_left_tree = self.connect_nodes_to_uni_tree('right', 'top', per_dim_nodes * (per_dim_nodes - 1))
        return top_left_tree, top_right_tree, bottom_left_tree, bottom_right_tree

    def compute_trees(self, sort=False, verbose=False):
        if self.args.load_tree:
            save_object = pickle.load(open(self.args.saved_tree_name, 'rb'))
            self.max_tree_height_for_pipeline = save_object['max_tree_height_for_pipeline']
            self.trees_rs = save_object['trees_rs']
            self.trees_ag = save_object['trees_ag']
            self.timesteps_rs = save_object['timesteps_rs']
            self.timesteps_ag = save_object['timesteps_ag']
            self.tree_roots = save_object['tree_roots']
            print("Loaded tree information")
        else:
            self.trees_rs = {}
            self.trees_ag = {}
            self.timesteps_rs = {}
            self.timesteps_ag = {}
            self.tree_roots = {}
            border_nodes, center_nodes = self.get_center_nodes()

            if self.args.booksim_network == 'SM_Alter':
                if self.args.per_dim_nodes % 2 == 0:
                    trees_rs, corner_timestep_rs = self.generate_trees_border(self.args.corner_set, 'RS')
                    trees_ag, corner_timestep_ag = self.generate_trees_border(self.args.corner_set, 'AG')
                    str_key = '_'.join(map(str, self.args.corner_set))
                    self.trees_rs[str_key] = trees_rs
                    self.trees_ag[str_key] = trees_ag
                    self.timesteps_rs[str_key] = corner_timestep_rs
                    self.timesteps_ag[str_key] = corner_timestep_ag
                    self.max_tree_height_for_pipeline = max(corner_timestep_rs, corner_timestep_ag)
                    self.tree_roots[str_key] = self.args.corner_set

                    for tree_roots in self.args.other_pipeline_sets:
                        is_center = False
                        for root in tree_roots:
                            if root in center_nodes:
                                is_center = True
                                break
                        if is_center:
                            trees_rs, timestep_rs = self.generate_trees_center(tree_roots, 'RS')
                            trees_ag, timestep_ag = self.generate_trees_center(tree_roots, 'AG')
                        else:
                            trees_rs, timestep_rs = self.generate_trees_border(tree_roots, 'RS')
                            trees_ag, timestep_ag = self.generate_trees_border(tree_roots, 'AG')
                        str_key = '_'.join(map(str, tree_roots))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs, timestep_ag)
                        self.tree_roots[str_key] = tree_roots
                else:
                    trees_rs, corner_timestep_rs = self.generate_trees_border(self.args.corner_set, 'RS')
                    trees_ag, corner_timestep_ag = self.generate_trees_border(self.args.corner_set, 'AG')
                    str_key = '_'.join(map(str, self.args.corner_set))
                    self.trees_rs[str_key] = trees_rs
                    self.trees_ag[str_key] = trees_ag
                    self.timesteps_rs[str_key] = corner_timestep_rs
                    self.timesteps_ag[str_key] = corner_timestep_ag
                    self.max_tree_height_for_pipeline = max(corner_timestep_rs, corner_timestep_ag)
                    self.tree_roots[str_key] = self.args.corner_set

                    for tree_roots in self.args.other_pipeline_sets:
                        print(tree_roots)

                        # assert len(tree_roots) == 3
                        # is_center = False
                        # for root in tree_roots:
                        #     if root in center_nodes:
                        #         is_center = True
                        #         break
                        # if is_center:
                        #     trees_rs, timestep_rs = self.generate_trees_center(tree_roots, 'RS')
                        #     trees_ag, timestep_ag = self.generate_trees_center(tree_roots, 'AG')
                        # else:
                        #     trees_rs, timestep_rs = self.generate_trees_border(tree_roots, 'RS')
                        #     trees_ag, timestep_ag = self.generate_trees_border(tree_roots, 'AG')

                        trees_rs, timestep_rs = self.generate_other_trees_three(tree_roots, 'RS')
                        trees_ag, timestep_ag = self.generate_other_trees_three(tree_roots, 'AG')
                        str_key = '_'.join(map(str, tree_roots))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs,
                                                                timestep_ag)
                        self.tree_roots[str_key] = tree_roots

                    if self.args.remaining_multitree_set is not None:
                        assert len(self.args.remaining_multitree_set) > 0
                        trees_rs, timestep_rs = self.compute_multitree_trees(self.args.remaining_multitree_set, 'RS', True)
                        trees_ag, timestep_ag = self.compute_multitree_trees(self.args.remaining_multitree_set, 'AG', True)
                        str_key = '_'.join(map(str, self.args.remaining_multitree_set))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        # self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs,
                        #                                         timestep_ag)
                        self.tree_roots[str_key] = self.args.remaining_multitree_set
            elif self.args.booksim_network == 'SM_Bi':
                if self.args.per_dim_nodes % 2 == 0:
                    trees_rs, corner_timestep_rs = self.generate_trees_border(self.args.corner_set, 'RS')
                    trees_ag, corner_timestep_ag = self.generate_trees_border(self.args.corner_set, 'AG')
                    str_key = '_'.join(map(str, self.args.corner_set))
                    self.trees_rs[str_key] = trees_rs
                    self.trees_ag[str_key] = trees_ag
                    self.timesteps_rs[str_key] = corner_timestep_rs
                    self.timesteps_ag[str_key] = corner_timestep_ag
                    self.max_tree_height_for_pipeline = max(corner_timestep_rs, corner_timestep_ag)
                    self.tree_roots[str_key] = self.args.corner_set

                    for tree_roots in self.args.other_pipeline_sets:
                        print(tree_roots)
                        is_center = False
                        for root in tree_roots:
                            if root in center_nodes:
                                is_center = True
                                break
                        if is_center:
                            trees_rs, timestep_rs = self.generate_trees_center(tree_roots, 'RS')
                            trees_ag, timestep_ag = self.generate_trees_center(tree_roots, 'AG')
                        else:
                            trees_rs, timestep_rs = self.generate_trees_border(tree_roots, 'RS')
                            trees_ag, timestep_ag = self.generate_trees_border(tree_roots, 'AG')
                        str_key = '_'.join(map(str, tree_roots))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs, timestep_ag)
                        self.tree_roots[str_key] = tree_roots
                    if self.args.remaining_multitree_set is not None:
                        assert len(self.args.remaining_multitree_set) > 0
                        trees_rs, timestep_rs = self.compute_multitree_trees(self.args.remaining_multitree_set, 'RS', True)
                        trees_ag, timestep_ag = self.compute_multitree_trees(self.args.remaining_multitree_set, 'AG', True)
                        str_key = '_'.join(map(str, self.args.remaining_multitree_set))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        # self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs,
                        #                                         timestep_ag)
                        self.tree_roots[str_key] = self.args.remaining_multitree_set
                else:
                    trees_rs, corner_timestep_rs = self.generate_trees_border(self.args.corner_set, 'RS')
                    trees_ag, corner_timestep_ag = self.generate_trees_border(self.args.corner_set, 'AG')
                    str_key = '_'.join(map(str, self.args.corner_set))
                    self.trees_rs[str_key] = trees_rs
                    self.trees_ag[str_key] = trees_ag
                    self.timesteps_rs[str_key] = corner_timestep_rs
                    self.timesteps_ag[str_key] = corner_timestep_ag
                    self.max_tree_height_for_pipeline = max(corner_timestep_rs, corner_timestep_ag)
                    self.tree_roots[str_key] = self.args.corner_set

                    for tree_roots in self.args.other_pipeline_sets:
                        print(tree_roots)

                        # assert len(tree_roots) == 3
                        # is_center = False
                        # for root in tree_roots:
                        #     if root in center_nodes:
                        #         is_center = True
                        #         break
                        # if is_center:
                        #     trees_rs, timestep_rs = self.generate_trees_center(tree_roots, 'RS')
                        #     trees_ag, timestep_ag = self.generate_trees_center(tree_roots, 'AG')
                        # else:
                        #     trees_rs, timestep_rs = self.generate_trees_border(tree_roots, 'RS')
                        #     trees_ag, timestep_ag = self.generate_trees_border(tree_roots, 'AG')

                        trees_rs, timestep_rs = self.generate_other_trees_sm_bi_odd(tree_roots, 'RS')
                        trees_ag, timestep_ag = self.generate_other_trees_sm_bi_odd(tree_roots, 'AG')
                        str_key = '_'.join(map(str, tree_roots))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs,
                                                                timestep_ag)
                        self.tree_roots[str_key] = tree_roots

                    if self.args.remaining_multitree_set is not None:
                        assert len(self.args.remaining_multitree_set) > 0
                        trees_rs, timestep_rs = self.compute_multitree_trees(self.args.remaining_multitree_set, 'RS',
                                                                             True)
                        trees_ag, timestep_ag = self.compute_multitree_trees(self.args.remaining_multitree_set, 'AG',
                                                                             True)
                        str_key = '_'.join(map(str, self.args.remaining_multitree_set))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        # self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs,
                        #                                         timestep_ag)
                        self.tree_roots[str_key] = self.args.remaining_multitree_set
            elif self.args.booksim_network == 'Partial_SM_Bi' or self.args.booksim_network == 'Partial_SM_Alter':
                if self.args.per_dim_nodes % 2 == 0:
                    trees_rs, corner_timestep_rs = self.generate_partial_tree_border(self.args.corner_set, 'RS')
                    trees_ag, corner_timestep_ag = self.generate_partial_tree_border(self.args.corner_set, 'AG')
                    str_key = '_'.join(map(str, self.args.corner_set))
                    self.trees_rs[str_key] = trees_rs
                    self.trees_ag[str_key] = trees_ag
                    self.timesteps_rs[str_key] = corner_timestep_rs
                    self.timesteps_ag[str_key] = corner_timestep_ag
                    self.max_tree_height_for_pipeline = max(corner_timestep_rs, corner_timestep_ag)
                    self.tree_roots[str_key] = self.args.corner_set

                    for tree_roots in self.args.other_pipeline_sets:
                        print(tree_roots)
                        trees_rs, timestep_rs = self.generate_other_trees_three(tree_roots, 'RS')
                        trees_ag, timestep_ag = self.generate_other_trees_three(tree_roots, 'AG')
                        str_key = '_'.join(map(str, tree_roots))
                        self.trees_rs[str_key] = trees_rs
                        self.trees_ag[str_key] = trees_ag
                        self.timesteps_rs[str_key] = timestep_rs
                        self.timesteps_ag[str_key] = timestep_ag
                        self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs, timestep_ag)
                        self.tree_roots[str_key] = tree_roots
                else:
                    raise RuntimeError("Partial SM_Bi for odd dimension has not been implemented yet.")
            elif self.args.booksim_network == 'SM_Uni':
                ag_top_left_tree, ag_top_right_tree, ag_bottom_left_tree, ag_bottom_right_tree = self.build_trees_unidirectional_ag()
                rs_top_left_tree, rs_top_right_tree, rs_bottom_left_tree, rs_bottom_right_tree = self.build_trees_unidirectional_rs()
                trees_rs = {0: sorted(rs_top_left_tree, key=lambda x: x[2]),
                            self.args.per_dim_nodes - 1: sorted(rs_top_right_tree, key=lambda x: x[2]),
                            self.args.per_dim_nodes * (self.args.per_dim_nodes - 1): sorted(rs_bottom_left_tree,
                                                                                            key=lambda x: x[2]),
                            self.args.num_hmcs - 1: sorted(rs_bottom_right_tree, key=lambda x: x[2])}
                trees_ag = {0: sorted(ag_top_left_tree, key=lambda x: x[2]),
                            self.args.per_dim_nodes - 1: sorted(ag_top_right_tree, key=lambda x: x[2]),
                            self.args.per_dim_nodes * (self.args.per_dim_nodes - 1): sorted(ag_bottom_left_tree,
                                                                                            key=lambda x: x[2]),
                            self.args.num_hmcs - 1: sorted(ag_bottom_right_tree, key=lambda x: x[2])}
                str_key = '_'.join(map(str, self.args.corner_set))
                self.trees_rs[str_key] = trees_rs
                self.trees_ag[str_key] = trees_ag
                self.timesteps_rs[str_key] = 2 * (self.args.per_dim_nodes - 1)
                self.timesteps_ag[str_key] = 2 * (self.args.per_dim_nodes - 1)
                self.max_tree_height_for_pipeline = 2 * (self.args.per_dim_nodes - 1)
                self.tree_roots[str_key] = self.args.corner_set
                print("Corner done")

                for tree_roots in self.args.other_pipeline_sets:
                    print(tree_roots)

                    # assert len(tree_roots) == 3
                    # is_center = False
                    # for root in tree_roots:
                    #     if root in center_nodes:
                    #         is_center = True
                    #         break
                    # if is_center:
                    #     trees_rs, timestep_rs = self.generate_trees_center(tree_roots, 'RS')
                    #     trees_ag, timestep_ag = self.generate_trees_center(tree_roots, 'AG')
                    # else:
                    #     trees_rs, timestep_rs = self.generate_trees_border(tree_roots, 'RS')
                    #     trees_ag, timestep_ag = self.generate_trees_border(tree_roots, 'AG')

                    trees_rs, timestep_rs = self.generate_other_trees_three(tree_roots, 'RS')
                    trees_ag, timestep_ag = self.generate_other_trees_three(tree_roots, 'AG')
                    str_key = '_'.join(map(str, tree_roots))
                    self.trees_rs[str_key] = trees_rs
                    self.trees_ag[str_key] = trees_ag
                    self.timesteps_rs[str_key] = timestep_rs
                    self.timesteps_ag[str_key] = timestep_ag
                    self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs, timestep_ag)
                    self.tree_roots[str_key] = tree_roots

                if self.args.remaining_multitree_set is not None:
                    assert len(self.args.remaining_multitree_set) > 0
                    trees_rs, timestep_rs = self.compute_multitree_trees(self.args.remaining_multitree_set, 'RS', True)
                    trees_ag, timestep_ag = self.compute_multitree_trees(self.args.remaining_multitree_set, 'AG', True)
                    str_key = '_'.join(map(str, self.args.remaining_multitree_set))
                    self.trees_rs[str_key] = trees_rs
                    self.trees_ag[str_key] = trees_ag
                    self.timesteps_rs[str_key] = timestep_rs
                    self.timesteps_ag[str_key] = timestep_ag
                    # self.max_tree_height_for_pipeline = max(self.max_tree_height_for_pipeline, timestep_rs,
                    #                                         timestep_ag)
                    self.tree_roots[str_key] = self.args.remaining_multitree_set

            save_object = {'max_tree_height_for_pipeline': self.max_tree_height_for_pipeline,
                           'trees_rs': self.trees_rs,
                           'trees_ag': self.trees_ag, 'timesteps_rs': self.timesteps_rs,
                           'timesteps_ag': self.timesteps_ag, 'tree_roots': self.tree_roots}
            pickle.dump(save_object, open(self.args.saved_tree_name, "wb"))
            print("Saved tree information")

        # top_left = self.generate_tree(1)
        # top_right = self.generate_tree(7)
        # bottom_left = self.generate_tree(8)
        # bottom_right = self.generate_tree(14)
        # trees, final_timestep = self.generate_tree([0, 3, 12, 15])
        # trees, final_timestep = self.generate_tree([4, 8, 7, 11])
        # trees, final_timestep = self.generate_tree([1, 2, 13, 14])
        # trees, final_timestep = self.generate_tree([5, 6, 9, 10])
        # self.tree_roots = [5, 6, 9, 10]

        # self.tree_roots = [0, 5, 30, 35]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [2, 3, 32, 33]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [6, 24, 11, 29]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [12, 18, 17, 23]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [8, 9, 26, 27]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [14, 15, 20, 21]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [0, 2, 6, 8]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [0, 4, 20, 24]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [1, 3, 21, 23]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [2, 10, 14, 22]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # self.tree_roots = [6, 8, 16, 18]
        # trees, final_timestep = self.generate_tree(self.tree_roots)
        # trees, final_timestep = self.generate_tree(self.args.corner_roots)
        # self.max_tree_height_for_pipeline = final_timestep
        # self.trees = trees
        # self.timesteps = final_timestep
        # tree_dot_file_path = '{}/src/dotFiles/'.format(os.environ['SIMHOME'])
        # dot_fle_name = tree_dot_file_path + str(self.args.booksim_network) + "_" + str(self.args.allreduce) + "_" + str(self.args.num_hmcs) + "_" + str(self.args.extension) + "_" + '_'.join(str(i) for i in self.tree_roots) + ".dot"
        # self.generate_trees_dotfile(dot_fle_name)
        # if self.args.allreduce == 'SM_Uni':
        #     self.rs_template_trees = self.trees
        #     self.ag_template_trees = self.trees
        # else:
        #     self.template_trees = self.trees
        # if self.args.allreduce == 'SM_Uni':
        #     self.rs_time_relative_links_last = {}
        #     for key in self.rs_template_trees.keys():
        #         tree = self.rs_template_trees[key]
        #         for edge in tree:
        #             time = edge[2] - 1
        #             if time not in self.rs_time_relative_links_last.keys():
        #                 self.rs_time_relative_links_last[time] = []
        #             self.rs_time_relative_links_last[time].append((edge[0], edge[1], key, edge[3]))
        #     self.ag_time_relative_links_last = {}
        #     for key in self.ag_template_trees.keys():
        #         tree = self.ag_template_trees[key]
        #         for edge in tree:
        #             time = edge[2] - 1
        #             if time not in self.ag_time_relative_links_last.keys():
        #                 self.ag_time_relative_links_last[time] = []
        #             self.ag_time_relative_links_last[time].append((edge[0], edge[1], key, edge[3]))
        # else:
        #     self.time_relative_links_last = {}
        #     for key in self.template_trees.keys():
        #         tree = self.template_trees[key]
        #         for edge in tree:
        #             time = edge[2] - 1
        #             if time not in self.time_relative_links_last.keys():
        #                 self.time_relative_links_last[time] = []
        #             self.time_relative_links_last[time].append((edge[0], edge[1], key, edge[3]))
        # self.total_partial_trees = self.args.total_partial_trees

        # self.tree_roots = []
        # self.tree_roots.append(0)
        # self.tree_roots.append(self.number_of_nodes - 1)
        # self.tree_roots.append(self.number_of_nodes * (self.number_of_nodes - 1))
        # self.tree_roots.append(self.args.num_hmcs - 1)
        # if self.args.allreduce != 'fatmesh_unidirectional':
            # self.trees = {}
            # self.trees[0] = top_left_tree
            # self.trees[self.number_of_nodes - 1] = top_right_tree
            # self.trees[self.number_of_nodes * (self.number_of_nodes - 1)] = bottom_left_tree
            # self.trees[self.args.num_hmcs - 1] = bottom_right_tree

    # def add_reduce_scatter_schedule(self, chunk_id, total_message):
    #     for key in sorted(self.time_relative_links_rs.keys(), reverse=True):
    #         for edge in self.time_relative_links_rs[key]:
    #             source = edge[0]
    #             target = edge[1]
    #             tree = edge[2]
    #             second = edge[3]
    #             dependencies = self.get_rs_dependency(tree=tree, source=source)
    #             source_ni, target_ni = self.get_source_dest_NI(source, target, self.args.booksim_network, second)
    #             if (target, second) not in self.reduce_scatter_schedule[source]:
    #                     self.reduce_scatter_schedule[source][(target, second)] = []
    #             self.reduce_scatter_schedule[source][(target, second)].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))
    #     for root in self.tree_roots:
    #         self.update_rs_final_dep(root, chunk_id)
    #
    # def add_all_gather_schedule(self, chunk_id, total_message):
    #     for key in sorted(self.time_relative_links_ag.keys()):
    #         for edge in self.time_relative_links_ag[key]:
    #             source = edge[1]
    #             target = edge[0]
    #             tree = edge[2]
    #             second = edge[3]
    #             dependencies = self.get_ag_dependency(tree=tree, source=source)
    #             source_ni, target_ni = self.get_source_dest_NI(source, target, self.args.booksim_network, second)
    #             if (target, second) not in self.all_gather_schedule[source]:
    #                     self.all_gather_schedule[source][(target, second)] = []
    #             self.all_gather_schedule[source][(target, second)].append((tree, chunk_id, dependencies, total_message, 0, source_ni, target_ni))

    def generate_schedule(self, verbose=False):
        trees_rs = copy.deepcopy(self.trees_rs)
        trees_ag = copy.deepcopy(self.trees_ag)
        tree_roots = copy.deepcopy(self.tree_roots)
        current_max_chunk = 0

        if self.args.collective == 'AR':
            key = '_'.join(map(str, self.args.corner_set))
            self.trees_rs = trees_rs[key]
            self.trees_ag = trees_ag[key]
            self.tree_roots = tree_roots[key]
            self.initiate_parent_children()
            for i in range(self.args.total_partial_trees):
                self.add_reduce_scatter_schedule(chunk_id=i, total_message=self.args.messages_per_chunk)
            for i in range(self.args.total_partial_trees):
                self.add_all_gather_schedule(chunk_id=i, total_message=self.args.messages_per_chunk)
        elif self.args.collective == 'RS' or self.args.collective == 'AG':
            key = '_'.join(map(str, self.args.corner_set))
            self.trees_rs = trees_rs[key]
            self.trees_ag = trees_ag[key]
            self.tree_roots = tree_roots[key]
            self.initiate_parent_children()
            for i in range(self.args.corner_partial_trees):
                self.add_reduce_scatter_schedule(chunk_id=current_max_chunk+i, total_message=self.args.messages_per_chunk)
            for i in range(self.args.corner_partial_trees):
                self.add_all_gather_schedule(chunk_id=current_max_chunk+i, total_message=self.args.messages_per_chunk)
            current_max_chunk += self.args.corner_partial_trees

            for temp_tree_roots in self.args.other_pipeline_sets:
                key = '_'.join(map(str, temp_tree_roots))
                self.trees_rs = trees_rs[key]
                self.trees_ag = trees_ag[key]
                self.tree_roots = tree_roots[key]
                self.initiate_parent_children()
                for i in range(self.args.other_partial_trees):
                    self.add_reduce_scatter_schedule(chunk_id=current_max_chunk+i, total_message=self.args.messages_per_chunk)
                for i in range(self.args.other_partial_trees):
                    self.add_all_gather_schedule(chunk_id=current_max_chunk+i, total_message=self.args.messages_per_chunk)
                current_max_chunk += self.args.other_partial_trees

            # if (self.args.booksim_network == 'SM_Alter' or self.args.booksim_network == 'SM_Bi') and self.args.per_dim_nodes % 2 == 0:
            #     assert self.args.remaining_multitree_set is None
            if self.args.remaining_multitree_set is not None:
                key = '_'.join(map(str, self.args.remaining_multitree_set))
                self.trees_rs = trees_rs[key]
                self.trees_ag = trees_ag[key]
                self.tree_roots = tree_roots[key]
                self.initiate_parent_children()
                self.add_reduce_scatter_schedule(chunk_id=current_max_chunk, total_message=self.args.multitree_message_for_pipeline)
                self.add_all_gather_schedule(chunk_id=current_max_chunk, total_message=self.args.multitree_message_for_pipeline)

    def generate_trees_dotfile(self, filename, verbose = False):
        # file_path = '/home/sabuj/Sabuj/Research/FatMesh_DoubleLink/results/mesh_logs/outputs/bb/bb_fatmesh_alternate_16_fatmesh_alternate_AlphaGoZero_google.log'
        # reduce_re = re.compile(r"(\d+) \| HMC-(\d+) \| start reducing for flow (\d+) \(from NI (\d+)\) to parent HMC-\((\d+), (\d+)\) \(to NI (\d+)\) for chunk (\d+)")
        # receive_re = re.compile(r"(\d+) \| HMC-(\d+) \| receives full reduce for flow (\d+) from child HMC-(\d+)-(\d+) for chunk (\d+)")
        # color palette for ploting nodes of different tree levels
        colors = ['#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff',
                  '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff']

        tree = 'digraph tree {\n'
        tree += '  rankdir = BT;\n'
        tree += '  subgraph {\n'

        # group nodes with same rank (same tree level/iteration)
        # and set up the map for node name and its rank in node_rank
        ranks = {}
        node_rank = {}
        for rank in range(self.timesteps_ag + 1):
            ranks[rank] = []
        tree_roots = self.args.corner_set

        for root in tree_roots:
            minrank = self.timesteps_ag
            for edge in self.trees_ag[root]:
                child = '"{}-{}"'.format(root, edge[0])
                rank = edge[2]
                ranks[rank].append(child)
                node_rank[child] = rank
                if edge[1] == root and rank - 1 < minrank:
                    minrank = rank - 1
            ranks[minrank].append('"{}-{}"'.format(root, root))
            node_rank['"{}-{}"'.format(root, root)] = minrank

        for root in tree_roots:
            tree += '    /* tree {} */\n'.format(root)
            for edge in self.trees_ag[root]:
                child = '"{}-{}"'.format(root, edge[0])
                parent = '"{}-{}"'.format(root, edge[1])
                cycle = self.timesteps_ag - edge[2]
                minlen = node_rank[child] - node_rank[parent]  # for strict separation of ranks
                if edge[3]:
                    tree += ''.join('    {} -> {} [ label="{}" minlen={} ];\n'.format(child, parent, cycle, minlen))
                else:
                    tree += ''.join('    {} -> {} [ label="{}" minlen={} color=red];\n'.format(child, parent, cycle, minlen))

        tree += '    // note that rank is used in the subgraph\n'
        for rank in range(self.timesteps_ag + 1):
            if ranks[rank]:
                level = '    {rank = same;'
                for node in ranks[rank]:
                    level += ' {};'.format(node)
                level += '}\n'
                tree += level

        tree += '    // node colors\n'
        style = '    {} [style="filled", fillcolor="{}"];\n'
        for rank in range(self.timesteps_ag + 1):
            if ranks[rank]:
                tree += ''.join(style.format(node, colors[rank % len(colors)]) for node in ranks[rank])

        tree += '  } /* closing subgraph */\n'
        tree += '}\n'

        f = open(filename, 'w')
        f.write(tree)
        f.close()
