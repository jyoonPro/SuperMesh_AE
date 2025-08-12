import numpy

def compute_trees(n1, n2, kary=None, alternate=True, sort=False, verbose=False):

    # initialize empty a ring
    ring = []
    ring.append(0)

    nodes = n1*n2

    to_nodes = {}
    for node in range(n1*n2):
        to_nodes[node] = []
        row = node // n2
        col = node % n2

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
            to_nodes[node].append(north)
        if south != None:
            to_nodes[node].append(south)
        if west != None:
            to_nodes[node].append(west)
        if east != None:
            to_nodes[node].append(east)

    # construct a ring
    explored = {}
    while True:
        # current node
        current = ring[-1]

        if current not in explored.keys():
            explored[current] = []

        next_node = None
        for neightbor in to_nodes[current]:
            if neightbor not in ring and neightbor not in explored[current]:
                next_node = neightbor
                break

        found = True
        if next_node:
            ring.append(next_node)
            explored[current].append(next_node)
            if len(ring) == nodes:
                if ring[0] in to_nodes[next_node]:
                    break
                else:
                    # doesn't lead to a valid solution, not circle
                    ring.pop()
        else:
            if verbose:
                print('Cannot reach a solution from current state: {}, backtrack'.format(ring))
            # remove the current node since it cannot reach to a solution
            ring.pop()
            explored.pop(current)
            if not explored:
                break

    if len(ring) == nodes:
        timesteps = nodes - 1
        if verbose:
            print('Ring found: {}'.format(ring))
        # form the 'trees'
        trees = {}
        for root in range(nodes):
            trees[root] = []
            root_idx = ring.index(root)
            for timestep in range(nodes - 1):
                parent_idx = (timestep + root_idx) % nodes
                child_idx = (timestep + root_idx + 1) % nodes

                parent = ring[parent_idx]
                child = ring[child_idx]

                trees[root].append((child, parent, timestep))
            if verbose:
                print('ring {}: {}'.format(root, trees[root]))
        return timesteps
    else:
        # print('No solution found! Check the topology graph')
        return -1

# n1, n2, latencies, num_messages, flits_per_packet
def one_dim(n1, n2, latency, num_messages, flits_per_packet):
    if n1 % 2 == 0:
        timesteps = compute_trees(n1, n2)
        if timesteps < 0:
            # meaning ring was not found.
            return -1
        else:
            # Time = number of messages/(n1*n2) x flits per packet x latency x timesteps x 2
            return (num_messages * flits_per_packet * latency * timesteps * 2) / (n1 * n2), (num_messages * flits_per_packet * latency * timesteps * 2) / (2 * n1 * n2)
    else:
        uni_timesteps = n1 * n2
        bi_timesteps = 2 * n1 * n2 - 3
        # Time = number of messages/(n1*n2) x flits per packet x latency x timesteps x 2
        return (num_messages*flits_per_packet*latency*uni_timesteps*2)/(n1*n2), (num_messages*flits_per_packet*latency*bi_timesteps)/(2 * (n1*n2-1))

# print(one_dim(4, 4, 10, 100, 25))