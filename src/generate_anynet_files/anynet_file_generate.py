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
        latency = int((self.args.message_size * 8 / self.args.flits_per_packet) / self.args.bandwidth)

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

            if self.args.topology == 'mesh' or self.args.topology == 'torus':
                if north is not None:
                    self.node_to_node[node].append((north, latency))
                if east is not None:
                    self.node_to_node[node].append((east, latency))
                if south is not None:
                    self.node_to_node[node].append((south, latency))
                if west is not None:
                    self.node_to_node[node].append((west, latency))
            elif self.args.topology == 'SM_Bi':
                # Default order: 0 = top, 1 = right, 2 = bottom, 3 = left, 4 = extra one
                if row == 0 and col == 0:
                    # Port 0: right, 1 = right, 2 = bottom, 3 = bottom
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((south, latency))
                elif row == 0 and col == self.nodes_in_dimension - 1:
                    # Port 0: left, 1 = bottom, 2 = bottom, 3 = left
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
                elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                    # Port 0: top, 1 = top, 2 = left, 3 = left
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((west, latency))
                elif row == self.nodes_in_dimension - 1 and col == 0:
                    # Port 0: top, 1 = right, 2 = right, 3 = top
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((north, latency))
                elif row == 0:
                    # Port 0: right, 1 = right, 2 = bottom, 3 = left, 4 = left
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((west, latency))
                elif col == self.nodes_in_dimension - 1:
                    # Port 0: top, 1 = bottom, 2 = bottom, 3 = left, 4 = top
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((north, latency))
                elif row == self.nodes_in_dimension - 1:
                    # Port 0: top, 1 = right, 2 = left, 3 = left, 4 = right
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((east, latency))
                elif col == 0:
                    # Port 0: top, 1 = right, 2 = bottom, 3 = top, 4 = bottom
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((south, latency))
                else:
                    # Port 0: top, 1 = right, 2 = bottom, 3 = left
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
            elif self.args.topology == 'SM_Uni':
                # Default order: 0 = top, 1 = right, 2 = bottom, 3 = left
                if row == 0 and col == 0:
                    # Port 0: right, 1 = right, 2 = bottom
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                elif row == 0 and col == self.nodes_in_dimension - 1:
                    # Port 0: bottom, 1 = bottom, 2 = left
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
                elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                    # Port 0: top, 1 = left, 2 = left
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((west, latency))
                elif row == self.nodes_in_dimension - 1 and col == 0:
                    # Port 0: top, 1 = right, 2 = top
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((north, latency))
                elif row == 0:
                    # Port 0: right, 1 = right, 2 = bottom, 3 = left
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
                elif col == self.nodes_in_dimension - 1:
                    # Port 0: top, 1 = bottom, 2 = bottom, 3 = left
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
                elif row == self.nodes_in_dimension - 1:
                    # Port 0: top, 1 = right, 2 = left, 3 = left, 4 = right
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((west, latency))
                    self.node_to_node[node].append((west, latency))
                elif col == 0:
                    # Port 0: top, 1 = right, 2 = bottom, 3 = top
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((north, latency))
                else:
                    # Port 0: top, 1 = right, 2 = bottom, 3 = left
                    self.node_to_node[node].append((north, latency))
                    self.node_to_node[node].append((east, latency))
                    self.node_to_node[node].append((south, latency))
                    self.node_to_node[node].append((west, latency))
            elif self.args.topology == 'SM_Alter':
                if self.nodes_in_dimension % 2 == 0:
                    # Default order: 0 = top, 1 = right, 2 = bottom, 3 = left
                    if row == 0 and col == 0:
                        # Port 0: right, 1 = right, 2 = bottom, 3 = bottom
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((south, latency))
                    elif row == 0 and col == self.nodes_in_dimension - 1:
                        # Port 0: left, 1 = bottom, 2 = bottom, 3 = left
                        self.node_to_node[node].append((west, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((west, latency))
                    elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                        # Port 0: top, 1 = top, 2 = left, 3 = left
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((west, latency))
                        self.node_to_node[node].append((west, latency))
                    elif row == self.nodes_in_dimension - 1 and col == 0:
                        # Port 0: top, 1 = right, 2 = right, 3 = top
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((north, latency))
                    elif row == 0:
                        if col % 2 == 0:
                            self.node_to_node[node].append((east, latency))
                        else:
                            self.node_to_node[node].append((west, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((west, latency))
                    elif col == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((north, latency))
                        if row % 2 == 0:
                            self.node_to_node[node].append((south, latency))
                        else:
                            self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((west, latency))
                    elif row == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((east, latency))
                        if col % 2 == 0:
                            self.node_to_node[node].append((east, latency))
                        else:
                            self.node_to_node[node].append((west, latency))
                        self.node_to_node[node].append((west, latency))
                    elif col == 0:
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((south, latency))
                        if row % 2 == 0:
                            self.node_to_node[node].append((south, latency))
                        else:
                            self.node_to_node[node].append((north, latency))
                    else:
                        # Port 0: top, 1 = right, 2 = bottom, 3 = left
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((west, latency))
                else:
                    if row == 0 and col == 0:
                        # Port 0: right, 1 = right, 2 = bottom, 3 = bottom
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((south, latency))
                    elif row == 0 and col == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((west, latency))
                    elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((west, latency))
                        self.node_to_node[node].append((west, latency))
                    elif row == self.nodes_in_dimension - 1 and col == 0:
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((north, latency))
                    elif row == 0:
                        if col % 2 == 0:
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((south, latency))
                            self.node_to_node[node].append((west, latency))
                        else:
                            self.node_to_node[node].append((west, latency))
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((south, latency))
                            self.node_to_node[node].append((west, latency))
                    elif col == self.nodes_in_dimension - 1:
                        if row % 2 == 0:
                            self.node_to_node[node].append((north, latency))
                            self.node_to_node[node].append((south, latency))
                            self.node_to_node[node].append((south, latency))
                            self.node_to_node[node].append((west, latency))
                        else:
                            self.node_to_node[node].append((north, latency))
                            self.node_to_node[node].append((north, latency))
                            self.node_to_node[node].append((south, latency))
                            self.node_to_node[node].append((west, latency))
                    elif row == self.nodes_in_dimension - 1:
                        if col % 2 == 0:
                            self.node_to_node[node].append((north, latency))
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((west, latency))
                            self.node_to_node[node].append((west, latency))
                        else:
                            self.node_to_node[node].append((north, latency))
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((west, latency))
                    elif col == 0:
                        if row % 2 == 0:
                            self.node_to_node[node].append((north, latency))
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((south, latency))
                            self.node_to_node[node].append((north, latency))
                        else:
                            self.node_to_node[node].append((north, latency))
                            self.node_to_node[node].append((east, latency))
                            self.node_to_node[node].append((south, latency))
                            self.node_to_node[node].append((south, latency))
                    else:
                        # Port 0: top, 1 = right, 2 = bottom, 3 = left
                        self.node_to_node[node].append((north, latency))
                        self.node_to_node[node].append((east, latency))
                        self.node_to_node[node].append((south, latency))
                        self.node_to_node[node].append((west, latency))


        anynet_filename = (self.args.topology + "_" + str(self.args.nodes) + "_"
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
    parser.add_argument('--topology', default='SM_Bi',
                        help='network topology (torus|mesh|SM_Bi|SM_Alter|SM_Uni), '
                             'default is torus')

    args = parser.parse_args()

    topology = Topology(args)
    topology.print_topology()


if __name__ == '__main__':
    main()
