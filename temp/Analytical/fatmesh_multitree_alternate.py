import numpy
import copy

# Multitree for n1 x n2 mesh that returns timesteps in the graph

def compute_trees(n1, n2, kary, alternate=True, sort=False, verbose=False):
        assert kary > 1

        nodes = n1*n2
        node_to_switch_mesh = {}
        switch_to_node_mesh = {}
        switch_to_switch_mesh = {}
        for node in range(nodes):
            node_to_switch_mesh[node] = (node, 4)
            switch_to_node_mesh[node] = []
            for i in range(4):
                switch_to_node_mesh[node].append(node)
            switch_to_switch_mesh[node] = []

            row = node // n2
            col = node % n2
            #print('node {}: row {} col {}'.format(node, row, col))

            north = None
            south = None
            east = None
            west = None
            if row != 0:
                north = node - n2

            if row != n1 - 1:
                south = node + n2

            if col != 0:
                west = node - 1

            if col != n2 - 1:
                east = node + 1

            if north != None:
                switch_to_switch_mesh[node].append(north)
            if south != None:
                switch_to_switch_mesh[node].append(south)
            if west != None:
                switch_to_switch_mesh[node].append(west)
            if east != None:
                switch_to_switch_mesh[node].append(east)

            if row == 0 or row == n1-1:
                if col % 2 == 0:
                    if east is not None:
                        switch_to_switch_mesh[node].append(east)
                else:
                    if west is not None:
                        switch_to_switch_mesh[node].append(west)
            if col == 0 or col == n2-1:
                if row % 2 == 0:
                    if south is not None:
                        switch_to_switch_mesh[node].append(south)
                else:
                    if north is not None:
                        switch_to_switch_mesh[node].append(north)


        # print(switch_to_switch_mesh)

        # initialize empty trees
        trees = {}
        tree_nodes = {}
        for node in range(nodes):
            trees[node] = []
            tree_nodes[node] = [node]
            if verbose:
                print('initialized tree {}: {}'.format(node, tree_nodes[node]))

        # tree construction
        num_trees = 0
        timesteps = 0

        # sort the roots based on link conflicts during allocation
        sorted_roots = list(range(nodes))
        conflicts = [0] * nodes

        constructed_trees = []

        while num_trees < nodes:
            if verbose:
                print('timestep {}'.format(timesteps))

            node_to_switch = copy.deepcopy(node_to_switch_mesh)
            switch_to_switch = copy.deepcopy(switch_to_switch_mesh)
            switch_to_node = copy.deepcopy(switch_to_node_mesh)
            last_tree_nodes = copy.deepcopy(tree_nodes)

            # alternating the link allocation every time for each tree
            if alternate:

                changed = True

                turns = 0
                while changed:
                    changed = False

                    root = sorted_roots[turns % nodes]

                    if len(tree_nodes[root]) < nodes and verbose:
                        p = (turns // nodes) % len(tree_nodes[root])
                        parent = tree_nodes[root][p]
                        print('turns: {}, root: {}, p: {}, parent: {}'.format(turns, root, p, parent))

                    # meaning nodes still left to add in tree[root]
                    if len(tree_nodes[root]) < nodes:
                        # check leaves?
                        for parent in last_tree_nodes[root]:
                            # no links starting from parent are available
                            if parent not in node_to_switch.keys():
                                continue
                            # some links strating from parent are available
                            switch = node_to_switch[parent][0]
                            # first check nodes on same switch
                            if switch in switch_to_node.keys():
                                children = copy.deepcopy(switch_to_node[switch])
                                for child in children:
                                    if child not in tree_nodes[root]:
                                        if verbose:
                                            print(' -- add node {} to tree {} (connected to parent {} on same switch {})'.format(child, root, parent, switch))
                                            print('    before: {}'.format(trees[root]))
                                        node_to_switch[parent] = (switch, node_to_switch[parent][1] - 1)
                                        if node_to_switch[parent][1] == 0:
                                            node_to_switch.pop(parent, None)
                                        switch_to_node[switch].remove(child)
                                        #if not switch_to_node[switch]:
                                        #    switch_to_node.pop(switch, None)
                                        tree_nodes[root].append(child)
                                        trees[root].append((child, parent, timesteps))
                                        if verbose:
                                            print('    after : {}'.format(trees[root]))
                                            print('    tree nodes: {}'.format(tree_nodes[root]))
                                        changed = True
                                        break
                                    else:
                                        conflicts[root] += 1

                            # check remote switchs' nodes
                            if changed == False:
                                dfs_switch_to_switch = copy.deepcopy(switch_to_switch)
                                visited = [switch]

                                # perform depth-first search to find a node
                                while visited and not changed:
                                    switch = visited[-1]
                                    neighbor_switches = copy.deepcopy(dfs_switch_to_switch[switch])
                                    for neighbor_sw in neighbor_switches:
                                        if neighbor_sw in visited:
                                            dfs_switch_to_switch[switch].remove(neighbor_sw)
                                            continue
                                        if neighbor_sw not in switch_to_node.keys(): # spine switch, not leaf
                                            visited.append(neighbor_sw)
                                            break
                                        else:
                                            children = copy.deepcopy(switch_to_node[neighbor_sw])
                                            for child in children:
                                                if child not in tree_nodes[root]:
                                                    if verbose:
                                                        print(' -- add node {} ( with switch {}) to tree {} (connected to parent {} on neighbor switch {})'.format(child, neighbor_sw, root, parent, switch))
                                                        print('    before: {}'.format(trees[root]))
                                                    node_to_switch[parent] = (switch, node_to_switch[parent][1] - 1)
                                                    if node_to_switch[parent][1] == 0:
                                                        node_to_switch.pop(parent, None)
                                                    switch_to_node[neighbor_sw].remove(child)
                                                    #if not switch_to_node[neighbor_sw]:
                                                    #    switch_to_node.pop(neighbor_sw, None)
                                                    # remove connections between switches
                                                    for i in range(len(visited) - 1):
                                                        switch_to_switch[visited[i]].remove(visited[i+1])
                                                    switch_to_switch[visited[-1]].remove(neighbor_sw)
                                                    tree_nodes[root].append(child)
                                                    trees[root].append((child, parent, timesteps))
                                                    if verbose:
                                                        print('    after : {}'.format(trees[root]))
                                                        print('    tree nodes: {}'.format(tree_nodes[root]))
                                                    changed = True
                                                    break
                                                else:
                                                    conflicts[root] += 1
                                            if changed:
                                                break

                                        # a node has been found and added
                                        if changed:
                                            break
                                        elif switch == visited[-1]:
                                            # no nodes associated with this leaf switch can be connected
                                            dfs_switch_to_switch[switch].remove(neighbor_sw)

                                    if not changed and switch == visited[-1]:
                                        visited.pop()

                            if changed:
                                break

                    turns += 1

                    if len(tree_nodes[root]) == nodes and root not in constructed_trees:
                        constructed_trees.append(root)
                        num_trees += 1
                        if verbose:
                            print('timestep {} - tree {} constructed: {}'.format(timesteps, root, trees[root]))
                        if num_trees == nodes:
                            break

                    if turns % nodes != 0:
                        changed = True

            timesteps += 1

        # verify that there is no link conflicts
        # for root in range(nodes):
        #     for i in range(root + 1, nodes):
        #         intersection = set(trees[root]) & set(trees[i])
        #         if len(intersection) != 0:
        #             print('tree {} and tree {} have link conflicts {}'.format(root, i, intersection))
        #             print('tree {}: {}'.format(root, trees[root]))
        #             print('tree {}: {}'.format(i, trees[i]))
        #             exit()

        if verbose:
            print('Total timesteps for network size of {}: {}'.format(nodes, timesteps))

        return timesteps, trees
    # def compute_trees(self, kary, alternate=False, sort=True, verbose=False)

def generate_trees_dotfile(filename, timesteps, nodes, trees):
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
    for rank in range(timesteps + 1):
        ranks[rank] = []

    for root in range(nodes):
        minrank = timesteps
        for edge in trees[root]:
            child = '"{}-{}"'.format(root, edge[0])
            rank = edge[2]+1
            ranks[rank].append(child)
            node_rank[child] = rank
            if edge[1] == root and rank - 1 < minrank:
                minrank = rank - 1
        ranks[minrank].append('"{}-{}"'.format(root, root))
        node_rank['"{}-{}"'.format(root, root)] = minrank

    for root in range(nodes):
        tree += '    /* tree {} */\n'.format(root)
        for edge in trees[root]:
            child = '"{}-{}"'.format(root, edge[0])
            parent = '"{}-{}"'.format(root, edge[1])
            cycle = timesteps - edge[2]
            minlen = node_rank[child] - node_rank[parent]  # for strict separation of ranks
            tree += ''.join('    {} -> {} [ label="{}" minlen={} ];\n'.format(child, parent, cycle, minlen))

    tree += '    // note that rank is used in the subgraph\n'
    for rank in range(timesteps + 1):
        if ranks[rank]:
            level = '    {rank = same;'
            for node in ranks[rank]:
                level += ' {};'.format(node)
            level += '}\n'
            tree += level

    tree += '    // node colors\n'
    style = '    {} [style="filled", fillcolor="{}"];\n'
    for rank in range(timesteps + 1):
        if ranks[rank]:
            tree += ''.join(style.format(node, colors[rank % len(colors)]) for node in ranks[rank])

    tree += '  } /* closing subgraph */\n'
    tree += '}\n'

    f = open(filename, 'w')
    f.write(tree)
    f.close()

# n1, n2, latencies, num_messages, flits_per_packet
def fatmesh_multitree_alternate(n1, n2, latency, num_messages, flits_per_packet, timesteps):
    if timesteps is None:
        timesteps, trees = compute_trees(n1, n2, 5)
    print(timesteps)

    total_nodes = n1*n2
    # generate_trees_dotfile('selective_' + str(total_nodes) + '.dot', timesteps, total_nodes, trees)

    # Time = number of messages/(n1*n2) x flits per packet x latency x timesteps x 2
    return (num_messages*flits_per_packet*latency*timesteps*2)/(n1*n2), timesteps

# print(multitree(4, 4, 10, 100, 25))