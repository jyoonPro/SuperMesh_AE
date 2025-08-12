import copy
import pickle
from copy import deepcopy

from allreduce import Allreduce

class MultiTreeAllreduce(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)

    def compute_trees_from_timestep(self, collective, sort=True):
        trees = {}
        tree_nodes = {}
        for node in range(self.network.nodes):
            trees[node] = []
            tree_nodes[node] = [node]

        timesteps = 0
        sorted_roots = list(range(self.network.nodes))

        changed_tracker = []
        for i in range(self.network.nodes):
            changed_tracker.append(False)
        finished = False
        while not finished:
            if collective == 'RS':
                switch_to_switch = deepcopy(self.network.switch_to_switch_rs)
            else:
                switch_to_switch = deepcopy(self.network.switch_to_switch_ag)
            last_tree_nodes = deepcopy(tree_nodes)

            changed = True
            turns = 0
            while changed:
                changed = False
                root = sorted_roots[turns % self.network.nodes]
                if len(tree_nodes[root]) < self.network.nodes:
                    for parent in last_tree_nodes[root]:
                        if not changed:
                            neighbor_switches = deepcopy(switch_to_switch[parent])
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

                if turns % self.network.nodes != 0:
                    changed = True
                else:
                    if sort:
                        sorted_roots = list(range(self.network.nodes))
                        sorted_roots = [root for _, root in sorted(zip(self.network.priority, sorted_roots), reverse=True)]
                    if any(changed_tracker):
                        changed = True
                    num_trees = 0
                    for i in range(self.network.nodes):
                        changed_tracker[i] = False
                        if len(tree_nodes[i]) == self.network.nodes:
                            num_trees += 1
                    if num_trees == self.network.nodes:
                        finished = True
                        break
            timesteps += 1

        # Check no link is used twice in same timestpe.
        if collective == 'RS':
            switch_to_switch = deepcopy(self.network.switch_to_switch_rs)
        else:
            switch_to_switch = deepcopy(self.network.switch_to_switch_ag)
        final_link_checker = {}
        for i in range(timesteps):
            final_link_checker[i] = copy.deepcopy(switch_to_switch)

        for i in range(self.network.nodes):
            for edge in trees[i]:
                if (edge[0], edge[3]) not in final_link_checker[edge[2]][edge[1]]:
                    print("Link " + str((edge[1], edge[0], edge[3])) + " is used more than availability in timestep " + str(edge[2]))
                    exit()
                else:
                    final_link_checker[edge[2]][edge[1]].remove((edge[0], edge[3]))

        return trees, timesteps

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
            trees_ag, final_timestep_ag = self.compute_trees_from_timestep('AG', True)
            trees_rs, final_timestep_rs = self.compute_trees_from_timestep('RS', True)
            self.max_tree_height_for_pipeline = max(final_timestep_rs, final_timestep_ag)
            self.trees_rs = trees_rs
            self.trees_ag = trees_ag
            self.timesteps_rs = final_timestep_rs
            self.timesteps_ag = final_timestep_ag
            self.tree_roots = [i for i in range(self.args.num_hmcs)]

            save_object = {'max_tree_height_for_pipeline': self.max_tree_height_for_pipeline, 'trees_rs': self.trees_rs,
                           'trees_ag': self.trees_ag, 'timesteps_rs': self.timesteps_rs,
                           'timesteps_ag': self.timesteps_ag, 'tree_roots': self.tree_roots}
            pickle.dump(save_object, open(self.args.saved_tree_name, "wb"))
            print("Saved tree information")

    def generate_schedule(self, verbose=False):
        self.initiate_parent_children()
        self.add_reduce_scatter_schedule(chunk_id=0, total_message=self.args.multitree_total_message)
        self.add_all_gather_schedule(chunk_id=0, total_message=self.args.multitree_total_message)
        print("Yoo")

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
                rank = edge[2] + 1
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
