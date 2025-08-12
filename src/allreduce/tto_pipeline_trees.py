import copy
import math
import pickle

from allreduce import Allreduce

class TTOPipelineTrees(Allreduce):
    def __init__(self, args, network):
        super().__init__(args, network)

    def form_trees(self):
        total_nodes = self.network.nodes
        per_dim_nodes = int(math.sqrt(total_nodes))
        left_nodes = {}
        right_nodes = {}
        top_nodes = {}
        bottom_nodes = {}
        max_tree_height = 0
        for node in range(total_nodes):
            left, right, top, bottom = self.get_lrtb(node, per_dim_nodes)
            left_nodes[node] = left
            right_nodes[node] = right
            top_nodes[node] = top
            bottom_nodes[node] = bottom

        tree = []
        time_tracker = {}
        node_to_consider = 0
        time_tracker[node_to_consider] = 0
        for_right = []
        for_right.append(node_to_consider)

        for i in range(per_dim_nodes - 1):
            timestep = time_tracker[node_to_consider]
            bottom_node = bottom_nodes[node_to_consider]
            tree.append((bottom_node, node_to_consider, timestep + 1, 1))
            time_tracker[bottom_node] = timestep + 1
            for_right.append(bottom_node)
            node_to_consider = bottom_node
            if timestep + 1 > max_tree_height:
                max_tree_height = timestep + 1
        for target_node in for_right:
            node_to_consider = target_node
            for i in range(per_dim_nodes - 1):
                timestep = time_tracker[node_to_consider]
                right_node = right_nodes[node_to_consider]
                tree.append((right_node, node_to_consider, timestep + 1, 1))
                time_tracker[right_node] = timestep + 1
                node_to_consider = right_node
                if timestep + 1 > max_tree_height:
                    max_tree_height = timestep + 1
        zero_tree = copy.deepcopy(tree)



        tree = []
        time_tracker = {}
        node_to_consider = self.args.num_hmcs - 1
        time_tracker[node_to_consider] = 0
        for_top = []
        for_top.append(node_to_consider)

        for i in range(per_dim_nodes - 1):
            timestep = time_tracker[node_to_consider]
            left_node = left_nodes[node_to_consider]
            tree.append((left_node, node_to_consider, timestep + 1, 1))
            time_tracker[left_node] = timestep + 1
            for_top.append(left_node)
            node_to_consider = left_node
            if timestep + 1 > max_tree_height:
                max_tree_height = timestep + 1
        for target_node in for_top:
            node_to_consider = target_node
            for i in range(per_dim_nodes - 1):
                timestep = time_tracker[node_to_consider]
                top_node = top_nodes[node_to_consider]
                tree.append((top_node, node_to_consider, timestep + 1, 1))
                time_tracker[top_node] = timestep + 1
                node_to_consider = top_node
                if timestep + 1 > max_tree_height:
                    max_tree_height = timestep + 1
        last_tree = copy.deepcopy(tree)

        tree = []
        time_tracker = {}
        node_to_consider = per_dim_nodes - 1
        time_tracker[node_to_consider] = 0
        # for_top = []
        # for_top.append(node_to_consider)

        for i in range(per_dim_nodes - 1):
            node_to_consider_left = node_to_consider
            while left_nodes[node_to_consider_left] is not None:
                timestep = time_tracker[node_to_consider_left]
                left_node = left_nodes[node_to_consider_left]
                tree.append((left_node, node_to_consider_left, timestep + 1, 1))
                time_tracker[left_node] = timestep + 1
                node_to_consider_left = left_node
                if timestep + 1 > max_tree_height:
                    max_tree_height = timestep + 1

            node_to_consider_bottom = node_to_consider
            while bottom_nodes[node_to_consider_bottom] is not None:
                timestep = time_tracker[node_to_consider_bottom]
                bottom_node = bottom_nodes[node_to_consider_bottom]
                tree.append((bottom_node, node_to_consider_bottom, timestep + 1, 1))
                time_tracker[bottom_node] = timestep + 1
                node_to_consider_bottom = bottom_node
                if timestep + 1 > max_tree_height:
                    max_tree_height = timestep + 1

            if i < per_dim_nodes - 2:
                left_node = left_nodes[node_to_consider]
                bottom_node = bottom_nodes[left_node]
                timestep = time_tracker[left_node]
                tree.append((bottom_node, left_node, timestep + 1, 1))
                time_tracker[bottom_node] = timestep + 1
                node_to_consider = bottom_node
                if timestep + 1 > max_tree_height:
                    max_tree_height = timestep + 1
        middle_tree = copy.deepcopy(tree)
        return zero_tree, middle_tree, last_tree, max_tree_height

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
            zero_tree, middle_tree, last_tree, max_tree_height = self.form_trees()
            self.max_tree_height_for_pipeline = max_tree_height
            self.timesteps_ag = max_tree_height
            self.timesteps_rs = max_tree_height
            self.trees_ag = {}
            self.trees_ag[0] = sorted(zero_tree, key=lambda x: x[2])
            self.trees_ag[self.args.per_dim_nodes - 1] = sorted(middle_tree, key=lambda x: x[2])
            self.trees_ag[self.args.num_hmcs - 1] = sorted(last_tree, key=lambda x: x[2])
            self.trees_rs = copy.deepcopy(self.trees_ag)
            self.tree_roots = self.args.corner_set

            # Check no link is used twice in the disjoint tree sets.
            switch_to_switch = copy.deepcopy(self.network.switch_to_switch_ag)
            for root in self.tree_roots:
                for edge in self.trees_ag[root]:
                    if (edge[0], edge[3]) not in switch_to_switch[edge[1]]:
                        print("Link " + str((edge[1], edge[0], edge[3])) + " is used twice.")
                        exit()
                    else:
                        switch_to_switch[edge[1]].remove((edge[0], edge[3]))
            save_object = {'max_tree_height_for_pipeline': self.max_tree_height_for_pipeline, 'trees_rs': self.trees_rs,
                           'trees_ag': self.trees_ag, 'timesteps_rs': self.timesteps_rs,
                           'timesteps_ag': self.timesteps_ag, 'tree_roots': self.tree_roots}
            pickle.dump(save_object, open(self.args.saved_tree_name, "wb"))
            print("Saved tree information")



    def generate_schedule(self, verbose=False):
        self.initiate_parent_children()
        for i in range(self.args.total_partial_trees):
            self.add_reduce_scatter_schedule(chunk_id=i, total_message=self.args.messages_per_chunk)
        for i in range(self.args.total_partial_trees):
            self.add_all_gather_schedule(chunk_id=i, total_message=self.args.messages_per_chunk)
        print("Yoo")

    def generate_trees_dotfile(self, filename, verbose=False):
        colors = ['#ffffff']

        tree = 'digraph tree {\n'
        tree += '  rankdir = BT;\n'
        tree += '  subgraph {\n'

        ranks = {}
        node_rank = {}
        for rank in range(self.timesteps_ag + 1):
            ranks[rank] = []

        for root in self.tree_roots:
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

        for root in self.tree_roots:
            tree += '    /* tree {} */\n'.format(root)
            for edge in self.trees_ag[root]:
                child = '"{}-{}"'.format(root, edge[0])
                parent = '"{}-{}"'.format(root, edge[1])
                cycle = self.timesteps_ag - edge[2]
                minlen = node_rank[child] - node_rank[parent]  # for strict separation of ranks
                if edge[3]:
                    tree += ''.join('    {} -> {} [ label="{}" minlen={} ];\n'.format(child, parent, cycle, minlen))
                else:
                    tree += ''.join(
                        '    {} -> {} [ label="{}" minlen={} color=red];\n'.format(child, parent, cycle, minlen))

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
                tree += ''.join(style.format(node, colors[0]) for node in ranks[rank])

        tree += '  } /* closing subgraph */\n'
        tree += '}\n'

        f = open(filename, 'w')
        f.write(tree)
        f.close()
