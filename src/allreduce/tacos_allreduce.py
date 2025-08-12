import math
import os

from allreduce import Allreduce
import matplotlib.colors as mcolors

class TacosAllreduce(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)

    def get_color(self, r, g, b):
        # Normalize the RGB values to 0-1 range, as matplotlib expects this format
        return mcolors.to_hex([r / 255.0, g / 255.0, b / 255.0])

    def get_tree(self, filepath):
        divider = 2441406
        trees = {}
        current_time = None
        current_timestep = None
        chunk_tracker = {}
        total_nodes = self.args.num_hmcs
        with open(filepath, 'r') as file:
            for line in file:
                parts = line.split()
                event_time = int(parts[1])
                chunk_id = int(parts[4].strip(':'))
                src = int(parts[5])
                dest = int(parts[7])
                if dest == (chunk_id % total_nodes):
                    continue
                if src == (chunk_id % total_nodes):
                    if src not in chunk_tracker.keys():
                        chunk_tracker[src] = {}
                    if chunk_id not in chunk_tracker[src].keys():
                        chunk_tracker[src][chunk_id] = 0
                assert chunk_id in chunk_tracker[src].keys()
                if current_time is None:
                    current_time = event_time
                    current_timestep = 1
                elif event_time > current_time:
                    current_time = event_time
                    current_timestep += 1
                assert current_timestep > chunk_tracker[src][chunk_id]
                if chunk_id not in trees.keys():
                    trees[chunk_id] = []
                trees[chunk_id].append((dest, src, current_timestep, 1))
                if dest not in chunk_tracker.keys():
                    chunk_tracker[dest] = {}
                chunk_tracker[dest][chunk_id] = current_timestep
                # computed_timestep = int(event_time / divider)
                # if self.args.booksim_network == 'mesh':
                #     if (src, dest) in self.network.corner_links.keys():
                #         self.network.corner_links[(src,dest)].add(current_timestep)
                #     elif (src, dest) in self.network.border_links.keys():
                #         self.network.border_links[(src,dest)].add(current_timestep)
                #     else:
                #         self.network.internal_links[(src, dest)].add(current_timestep)
                # else:
                #     if (src, dest) in self.network.corner_links.keys():
                #         if (src, dest) not in self.network.added_links:
                #             self.network.corner_links[(src, dest)].add(current_timestep)
                #             self.network.corner_links[(src, dest)].add(current_timestep - 1)
                #         else:
                #             self.network.corner_links[(src, dest)].add(current_timestep)
                #     elif (src, dest) in self.network.border_links.keys():
                #         if (src, dest) not in self.network.added_links:
                #             self.network.border_links[(src, dest)].add(current_timestep)
                #             self.network.border_links[(src, dest)].add(current_timestep - 1)
                #         else:
                #             self.network.border_links[(src, dest)].add(current_timestep)
                #     else:
                #         if (src, dest) not in self.network.added_links:
                #             self.network.internal_links[(src, dest)].add(current_timestep)
                #             self.network.internal_links[(src, dest)].add(current_timestep - 1)
                #         else:
                #             self.network.internal_links[(src, dest)].add(current_timestep)

        # for i in range(self.args.num_hmcs * 4): # Each node sends 4 chunks, so total number of trees = 4 * nodes
        for i in range(self.args.num_hmcs): # Each node sends 4 chunks, so total number of trees = 4 * nodes
            assert len(trees[i]) == self.args.num_hmcs - 1
        # total_timesteps = current_timestep
        # utilization_dict = {}
        # unique_utilizations = set()
        # for link in self.network.border_links.keys():
        #     perc = int((len(self.network.border_links[link]) * 100) / total_timesteps)
        #     if perc <= 25:
        #         perc = 25
        #     elif perc <= 50:
        #         perc = 50
        #     elif perc <= 75:
        #         perc = 75
        #     else:
        #         perc = 100
        #     if perc not in utilization_dict.keys():
        #         utilization_dict[perc] = []
        #     utilization_dict[perc].append(link)
        #     unique_utilizations.add(perc)
        #
        # for link in self.network.corner_links.keys():
        #     perc = int((len(self.network.corner_links[link]) * 100) / total_timesteps)
        #     if perc <= 25:
        #         perc = 25
        #     elif perc <= 50:
        #         perc = 50
        #     elif perc <= 75:
        #         perc = 75
        #     else:
        #         perc = 100
        #     if perc not in utilization_dict.keys():
        #         utilization_dict[perc] = []
        #     utilization_dict[perc].append(link)
        #     unique_utilizations.add(perc)
        #
        # for link in self.network.internal_links.keys():
        #     perc = int((len(self.network.internal_links[link]) * 100) / total_timesteps)
        #     if perc <= 25:
        #         perc = 25
        #     elif perc <= 50:
        #         perc = 50
        #     elif perc <= 75:
        #         perc = 75
        #     else:
        #         perc = 100
        #     if perc not in utilization_dict.keys():
        #         utilization_dict[perc] = []
        #     utilization_dict[perc].append(link)
        #     unique_utilizations.add(perc)
        #
        # print(unique_utilizations)
        # low_rgb = (69, 117, 180)  # Blue
        # blue_color = self.get_color(69, 117, 180)
        # print("Blue color code:" + str(blue_color))
        # high_rgb = (244, 109, 67)  # Orange
        # orange_color = self.get_color(244, 109, 67)
        # print("Orange color code:" + str(orange_color))
        # for percentage in sorted(unique_utilizations):
        #     # r = int(percentage * 255 / 100)
        #     # g = int((100 - percentage) * 255 / 100)
        #     # print(str(percentage) + " - R:" + str(r) + ", G:" + str(g))
        #     # color_code = self.get_color(r, g, 0)
        #     # print("color code:" + str(color_code))
        #     # Linear interpolation for each color channel
        #     r = int(low_rgb[0] + (high_rgb[0] - low_rgb[0]) * (percentage / 100))
        #     g = int(low_rgb[1] + (high_rgb[1] - low_rgb[1]) * (percentage / 100))
        #     b = int(low_rgb[2] + (high_rgb[2] - low_rgb[2]) * (percentage / 100))
        #
        #     print(f"{percentage:.1f}% - R:{r}, G:{g}, B:{b}")
        #     color_code = self.get_color(r, g, b)
        #     print("color code:" + str(color_code))
        #     for (src, dest) in utilization_dict[percentage]:
        #         print(str(src) + " -> " + str(dest))
        #     print()
        # percentage = 25
        # r = int(low_rgb[0] + (high_rgb[0] - low_rgb[0]) * (percentage / 100))
        # g = int(low_rgb[1] + (high_rgb[1] - low_rgb[1]) * (percentage / 100))
        # b = int(low_rgb[2] + (high_rgb[2] - low_rgb[2]) * (percentage / 100))
        #
        # print(f"{percentage:.1f}% - R:{r}, G:{g}, B:{b}")
        # color_code = self.get_color(r, g, b)
        # print("color code:" + str(color_code))
        #
        # header = 'digraph tree {\n'
        # header += '  rankdir = BT;\n'
        # header += '  color = black;\n'
        # per_dim_nodes = int(math.sqrt(total_nodes))
        #
        # header += '\n'
        # for node in range(per_dim_nodes):
        #     header += '  {rank = same;'
        #     for target_node in range(per_dim_nodes - 1, -1, -1):
        #         header += ' "{}";'.format(node * per_dim_nodes + target_node)
        #     header += '}\n'
        # for percentage in sorted(unique_utilizations):
        #     # r = int(percentage * 255 / 100)
        #     # g = int((100 - percentage) * 255 / 100)
        #     # color_code = self.get_color(r, g, 0)
        #     # Linear interpolation for each color channel
        #     r = int(low_rgb[0] + (high_rgb[0] - low_rgb[0]) * (percentage / 100))
        #     g = int(low_rgb[1] + (high_rgb[1] - low_rgb[1]) * (percentage / 100))
        #     b = int(low_rgb[2] + (high_rgb[2] - low_rgb[2]) * (percentage / 100))
        #     color_code = self.get_color(r, g, b)
        #     for (src, dest) in utilization_dict[percentage]:
        #         header += '  "{}" -> "{}" [ minlen=1, color="{}", penwidth=2];\n'.format(src, dest, str(color_code))
        # # for node in range(total_nodes):
        # #     for key, value in temp_node_to_node_tracker[node].items():
        # #         header += '  "{}" -> "{}" [ minlen=1, color="{}", penwidth=2];\n'.format(node, key, color_dict[
        # #             node_to_node_tracker[node][key]])
        # header += '}\n'
        # output_path = '/home/sabuj/Sabuj/Research/SuperMesh/src/6x6_sm_bi_tacos_new.dot'
        # f = open(output_path, 'w')
        # f.write(header)
        # f.close()
        return trees, current_timestep


    def compute_trees(self, sort=False, verbose=False):
        if self.args.booksim_network == 'mesh':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_mesh.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_mesh.txt'
        elif self.args.booksim_network == 'SM_Bi':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_sm_bi.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_sm_bi.txt'
        elif self.args.booksim_network == 'SM_Alter':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_sm_alter.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_sm_alter.txt'
        elif self.args.booksim_network == 'SM_Uni':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_sm_uni_rs.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_sm_uni_ag.txt'
        elif self.args.booksim_network == 'folded_torus':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_folded_torus.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_folded_torus.txt'
        elif self.args.booksim_network == 'cmesh':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_cmesh.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_cmesh.txt'
        elif self.args.booksim_network == 'dbutterfly':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_butterfly.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_butterfly.txt'
        elif self.args.booksim_network == 'kite':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_kite.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_kite.txt'
        elif self.args.booksim_network == 'kite_medium':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_kite_medium.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_kite_medium.txt'
        elif self.args.booksim_network == 'Partial_SM_Bi':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_partial_sm_bi.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_partial_sm_bi.txt'
        elif self.args.booksim_network == 'Partial_SM_Alter':
            rs_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_partial_sm_alter.txt'
            ag_file_path = '{}/src/tacos/results/tacos_'.format(os.environ['SIMHOME']) + str(self.args.num_hmcs) + '_partial_sm_alter.txt'

        trees_rs, final_timestep_rs = self.get_tree(rs_file_path)
        trees_ag, final_timestep_ag = self.get_tree(ag_file_path)
        self.trees_rs = trees_rs
        self.trees_ag = trees_ag
        self.timesteps_rs = final_timestep_rs
        self.timesteps_ag = final_timestep_ag
        # self.chunk_roots = [i for i in range(self.args.num_hmcs) for _ in range(4)]
        self.tree_roots = [i for i in range(self.args.num_hmcs * 4)]
        self.max_tree_height_for_pipeline = max(final_timestep_rs, final_timestep_ag)


    def generate_schedule(self, verbose=False):
        self.initiate_parent_children()
        self.add_reduce_scatter_schedule(chunk_id=0, total_message=self.args.tacos_total_message)
        self.add_all_gather_schedule(chunk_id=0, total_message=self.args.tacos_total_message)
        print("Yo")

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
