import copy
import json
import math
import os

from allreduce import Allreduce


class Alternative2dRingAllreduce(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)

    def get_tree(self, node):
        tree = []
        # final_timestep = 0

        # Add Horizontal Node First
        node_to_consider = node
        for i in range(2 * self.args.per_dim_nodes - 1):
            col_idx = node_to_consider % self.args.per_dim_nodes
            row_idx = math.floor(node_to_consider / self.args.per_dim_nodes)
            left, right, top, bottom = self.get_lrtb(node_to_consider, self.args.per_dim_nodes)
            if col_idx == self.args.per_dim_nodes - 1:
                if row_idx % 2 == 0:
                    neighbor = bottom
                else:
                    neighbor = left
            elif col_idx == 0:
                if row_idx % 2 == 0:
                    neighbor = right
                else:
                    neighbor = top
            elif row_idx % 2 == 0:
                neighbor = right
            elif row_idx % 2 == 1:
                neighbor = left
            else:
                raise RuntimeError("Wrong row and col index")
            tree.append((neighbor, node_to_consider, i + 1, 1, self.args.alternate_2d_first_dim_messages))
            node_to_consider = neighbor

        # Form rings in column
        vertical_ring = []
        vertical_ring_path = {}
        node_to_consider = node
        col_idx = node_to_consider % self.args.per_dim_nodes
        vertical_ring.append(col_idx)
        temp_path = []
        for i in range(self.args.per_dim_nodes - 1):
            src = (self.args.per_dim_nodes - 1 - i) * self.args.per_dim_nodes + col_idx
            neighbor = (self.args.per_dim_nodes - 1 - i - 1) * self.args.per_dim_nodes + col_idx
            temp_path.append((src, neighbor))
        vertical_ring_path[col_idx] = temp_path
        for i in range(self.args.per_dim_nodes - 1):
            src = i * self.args.per_dim_nodes + col_idx
            neighbor = (i+1) * self.args.per_dim_nodes + col_idx
            vertical_ring.append(neighbor)
            vertical_ring_path[neighbor] = [(src, neighbor)]

        final_timestep = 2 * self.args.per_dim_nodes - 1
        node_to_consider = node
        for i in range(self.args.per_dim_nodes // 2 - 1):
            index = vertical_ring.index(node_to_consider)
            first_neighbor_index = (index + 1) % self.args.per_dim_nodes
            second_neighbor_index = (first_neighbor_index + 1) % self.args.per_dim_nodes
            for path in vertical_ring_path[vertical_ring[first_neighbor_index]]:
                tree.append((path[1], path[0], final_timestep + 1, 1, self.args.alternate_2d_second_dim_messages))
                final_timestep += 1
            for path in vertical_ring_path[vertical_ring[second_neighbor_index]]:
                tree.append((path[1], path[0], final_timestep + 1, 1, self.args.alternate_2d_second_dim_messages))
                final_timestep += 1
            node_to_consider = vertical_ring[second_neighbor_index]

        return tree, final_timestep


    def compute_trees(self, sort=False, verbose=False):
        trees_ag = {}
        final_timestep_ag = 0
        for i in range(self.network.nodes):
            temp_tree, temp_timestep = self.get_tree(i)
            trees_ag[i] = temp_tree
            if temp_timestep > final_timestep_ag:
                final_timestep_ag = temp_timestep

        self.trees_rs = copy.deepcopy(trees_ag)
        self.trees_ag = trees_ag
        self.timesteps_rs = final_timestep_ag
        self.timesteps_ag = final_timestep_ag
        self.tree_roots = [i for i in range(self.args.num_hmcs)]
        self.max_tree_height_for_pipeline = final_timestep_ag


    def generate_schedule(self, verbose=False):
        self.initiate_parent_children()
        self.add_reduce_scatter_schedule(chunk_id=0, total_message=None)
        self.add_all_gather_schedule(chunk_id=0, total_message=None)

    def generate_trees_dotfile(self, filename, verbose = False):
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
        for rank in range(self.timesteps_ag + 1):
            ranks[rank] = []

        for root in range(self.network.nodes):
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

        for root in range(self.network.nodes):
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
