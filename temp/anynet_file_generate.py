import argparse
import math


class Topology:
    def __init__(self, args):
        self.args = args
        self.nodes = args.nodes
        self.nodes_in_dimension = int(math.sqrt(args.nodes))
        self.node_to_node = {}
        if self.args.topology == 'torus':
            self.mesh = False
        else:
            self.mesh = True

    def print_topology(self):
        if self.args.flits_per_packet != 16:
            raise RuntimeError('Warnings: Flits per packet is not 16, be cautious with floating point calculation')
        latency = int((self.args.message_size * 8 / self.args.flits_per_packet) / self.args.bandwidth)
        half_latency = math.ceil(latency / 2)

        for node in range(self.nodes):
            self.node_to_node[node] = []
            row = node // self.nodes_in_dimension
            col = node % self.nodes_in_dimension

            north = None
            south = None
            east = None
            west = None
            # TODO: Add comments
            if row == 0 and not self.mesh:
                if self.nodes_in_dimension > 2:
                    north = node + self.nodes_in_dimension * (self.nodes_in_dimension - 1)
            elif row != 0:
                north = node - self.nodes_in_dimension

            if row == self.nodes_in_dimension - 1 and not self.mesh:
                if self.nodes_in_dimension > 2:
                    south = node - self.nodes_in_dimension * (self.nodes_in_dimension - 1)
            elif row != self.nodes_in_dimension - 1:
                south = node + self.nodes_in_dimension

            if col == 0 and not self.mesh:
                if self.nodes_in_dimension > 2:
                    west = node + self.nodes_in_dimension - 1
            elif col != 0:
                west = node - 1

            if col == self.nodes_in_dimension - 1 and not self.mesh:
                if self.nodes_in_dimension > 2:
                    east = node - self.nodes_in_dimension + 1
            elif col != self.nodes_in_dimension - 1:
                east = node + 1

            if north is not None:
                if self.args.topology == 'fatmesh_all':
                    if col == 0 or col == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((north, half_latency))
                    else:
                        self.node_to_node[node].append((north, latency))
                elif self.args.topology == 'mesh' or self.args.topology == 'torus':
                    self.node_to_node[node].append((north, latency))
                elif self.args.topology == 'fatmesh_alternate':
                    if self.nodes_in_dimension % 2 == 0:
                        if (col == 0 or col == self.nodes_in_dimension - 1) and row % 2 == 1:
                            self.node_to_node[node].append((north, half_latency))
                        else:
                            self.node_to_node[node].append((north, latency))
                    else:
                        if (col == 0 and row % 2 == 0) or (col == self.nodes_in_dimension - 1 and row % 2 == 1):
                            self.node_to_node[node].append((north, half_latency))
                        else:
                            self.node_to_node[node].append((north, latency))
            if south is not None:
                if self.args.topology == 'fatmesh_all':
                    if col == 0 or col == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((south, half_latency))
                    else:
                        self.node_to_node[node].append((south, latency))
                elif self.args.topology == 'mesh' or self.args.topology == 'torus':
                    self.node_to_node[node].append((south, latency))
                elif self.args.topology == 'fatmesh_alternate':
                    if self.nodes_in_dimension % 2 == 0:
                        if (col == 0 or col == self.nodes_in_dimension - 1) and row % 2 == 0:
                            self.node_to_node[node].append((south, half_latency))
                        else:
                            self.node_to_node[node].append((south, latency))
                    else:
                        if (col == 0 and row % 2 == 1) or (col == self.nodes_in_dimension - 1 and row % 2 == 0):
                            self.node_to_node[node].append((south, half_latency))
                        else:
                            self.node_to_node[node].append((south, latency))
            if west is not None:
                if self.args.topology == 'fatmesh_all':
                    if row == 0 or row == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((west, half_latency))
                    else:
                        self.node_to_node[node].append((west, latency))
                elif self.args.topology == 'mesh' or self.args.topology == 'torus':
                    self.node_to_node[node].append((west, latency))
                elif self.args.topology == 'fatmesh_alternate':
                    if self.nodes_in_dimension % 2 == 0:
                        if (row == 0 or row == self.nodes_in_dimension - 1) and col % 2 == 1:
                            self.node_to_node[node].append((west, half_latency))
                        else:
                            self.node_to_node[node].append((west, latency))
                    else:
                        if (row == 0 and col % 2 == 1) or (row == self.nodes_in_dimension - 1 and col % 2 == 0):
                            self.node_to_node[node].append((west, half_latency))
                        else:
                            self.node_to_node[node].append((west, latency))
            if east is not None:
                if self.args.topology == 'fatmesh_all':
                    if row == 0 or row == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((east, half_latency))
                    else:
                        self.node_to_node[node].append((east, latency))
                elif self.args.topology == 'mesh' or self.args.topology == 'torus':
                    self.node_to_node[node].append((east, latency))
                elif self.args.topology == 'fatmesh_alternate':
                    if self.nodes_in_dimension % 2 == 0:
                        if (row == 0 or row == self.nodes_in_dimension - 1) and col % 2 == 0:
                            self.node_to_node[node].append((east, half_latency))
                        else:
                            self.node_to_node[node].append((east, latency))
                    else:
                        if (row == 0 and col % 2 == 0) or (row == self.nodes_in_dimension - 1 and col % 2 == 1):
                            self.node_to_node[node].append((east, half_latency))
                        else:
                            self.node_to_node[node].append((east, latency))

        anynet_filename = ("generate_anynet_files/" + self.args.topology + "_" + str(self.args.nodes) + "_"
                           + str(self.args.bandwidth) + ".txt")

        with open(anynet_filename, 'w') as f:
            for node in range(self.nodes):
                line = "router " + str(node)
                for i in range(self.args.radix):
                    line += " node " + str(node * self.args.radix + i)
                for neighbor_node in self.node_to_node[node]:
                    line += " router " + str(neighbor_node[0]) + " " + str(neighbor_node[1])
                line += "\n"
                f.write(line)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--nodes', default=25, type=int,
                        help='network nodes, default is 16')
    parser.add_argument('--radix', default=4, type=int,
                        help='node radix connected to router (end node NIs), default is 4')
    parser.add_argument('--flits-per-packet', default=16, type=int,
                        help='Number of payload flits per packet, packet header is not considered here, that will be '
                             'added in booksim')
    parser.add_argument('--bandwidth', default=200, type=int,
                        help='On chip latency')
    parser.add_argument('--message-size', default=8192, type=int,
                        help='size of a message, default is 256 bytes, 0 means treat the whole chunk of gradients as '
                             'a message')
    parser.add_argument('--topology', default='fatmesh_all',
                        help='network topology (torus|mesh|fatmesh_all|fatmesh_alternate|fatmesh_unidirectional), '
                             'default is torus')

    args = parser.parse_args()

    topology = Topology(args)
    topology.print_topology()


if __name__ == '__main__':
    main()
