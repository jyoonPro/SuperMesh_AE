import json
import os

from allreduce import Allreduce


class TecclAllreduce(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)

    def extract_flows(self, json_file_path):
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        return data['7-Flows']

    def get_tree(self, filepath):
        data_flows = self.extract_flows(filepath)

        final_timestep = 0
        time_trackers = {}
        trees = {}
        leaves_list = {}
        for root in range(self.network.nodes):
            time_trackers[root] = {}
            time_trackers[root][root] = 0
            trees[root] = []
            leaves_list[root] = [root]
        occupied_link = {}
        for line in data_flows:
            parts = line.split(' ')
            chunk_id = int(parts[3])
            src_dest = parts[6]
            src_dest_split = src_dest.split('->')
            src_id = int(src_dest_split[0])
            dest_id = int(src_dest_split[1])

            assert dest_id not in leaves_list[chunk_id]
            timestep = time_trackers[chunk_id][src_id]
            new_timestep = timestep + 1
            if (src_id, dest_id) not in occupied_link.keys():
                occupied_link[(src_id, dest_id)] = []
            while new_timestep in occupied_link[(src_id, dest_id)]:
                new_timestep += 1
            trees[chunk_id].append((dest_id, src_id, new_timestep, 1))
            if new_timestep > final_timestep:
                final_timestep = new_timestep
            time_trackers[chunk_id][dest_id] = new_timestep
            leaves_list[chunk_id].append(dest_id)
            occupied_link[(src_id, dest_id)].append(new_timestep)

        for node in range(self.network.nodes):
            assert len(trees[node]) == self.args.num_hmcs - 1

        return trees, final_timestep


    def compute_trees(self, sort=False, verbose=False):
        if self.args.booksim_network == 'mesh':
            rs_file_path = '{}/src/teccl/Mesh_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)
            ag_file_path = '{}/src/teccl/Mesh_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)
        elif self.args.booksim_network == 'SM_Bi':
            rs_file_path = '{}/src/teccl/SM_Bi_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)
            ag_file_path = '{}/src/teccl/SM_Bi_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)
        elif self.args.booksim_network == 'SM_Alter':
            if self.args.per_dim_nodes % 2 == 0:
                rs_file_path = '{}/src/teccl/SM_Alter_Even_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)
                ag_file_path = '{}/src/teccl/SM_Alter_Even_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)
        elif self.args.booksim_network == 'SM_Uni':
            rs_file_path = '{}/src/teccl/SM_Uni_RS_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)
            ag_file_path = '{}/src/teccl/SM_Uni_{}-nodes_1-chunks_1.0-chunksize_AllGather_MILP.json'.format(os.environ['SIMHOME'], self.args.num_hmcs)

        # trees_rs, final_timestep_rs = self.get_tree(rs_file_path)
        trees_ag, final_timestep_ag = self.get_tree(ag_file_path)
        self.trees_rs = None
        # self.trees_rs = trees_rs
        self.trees_ag = trees_ag
        # self.timesteps_rs = final_timestep_rs
        self.timesteps_ag = final_timestep_ag
        self.tree_roots = [i for i in range(self.args.num_hmcs)]
        # self.max_tree_height_for_pipeline = max(final_timestep_rs, final_timestep_ag)


    def generate_schedule(self, verbose=False):
        self.initiate_parent_children()
        # self.add_reduce_scatter_schedule(chunk_id=0, total_message=self.args.teccl_total_message)
        self.add_all_gather_schedule(chunk_id=0, total_message=self.args.teccl_total_message)

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
