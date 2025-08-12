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
        global_routing_table = {}

        for node in range(self.nodes):
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

            global_routing_table[node] = [0] * self.nodes * self.args.radix
            for i in range(self.args.radix):
                global_routing_table[node][node * self.args.radix + i] = i
            if self.args.topology == 'SM_Alter':
                if self.nodes_in_dimension % 2 == 0:
                    if row == 0 and col == 0:
                        global_routing_table[node][east * self.args.radix + 0] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][south * self.args.radix + 3] = self.args.radix + 3
                    elif row == 0 and col == self.nodes_in_dimension - 1:
                        global_routing_table[node][west * self.args.radix + 0] = self.args.radix + 0
                        global_routing_table[node][south * self.args.radix + 1] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                    elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][north * self.args.radix + 1] = self.args.radix + 1
                        global_routing_table[node][west * self.args.radix + 2] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                    elif row == self.nodes_in_dimension - 1 and col == 0:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][east * self.args.radix + 2] = self.args.radix + 2
                        global_routing_table[node][north * self.args.radix + 3] = self.args.radix + 3
                    else:
                        if row == 0:
                            if col % 2 == 0:
                                global_routing_table[node][east * self.args.radix + 0] = self.args.radix + 0
                            else:
                                global_routing_table[node][west * self.args.radix + 0] = self.args.radix + 0
                            global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                            global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                            global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        elif col == self.nodes_in_dimension - 1:
                            global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                            if row % 2 == 0:
                                global_routing_table[node][south * self.args.radix + 1] = self.args.radix + 1
                            else:
                                global_routing_table[node][north * self.args.radix + 1] = self.args.radix + 1
                            global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                            global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        elif row == self.nodes_in_dimension - 1:
                            global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                            global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                            if col % 2 == 0:
                                global_routing_table[node][east * self.args.radix + 2] = self.args.radix + 2
                            else:
                                global_routing_table[node][west * self.args.radix + 2] = self.args.radix + 2
                            global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        elif col == 0:
                            global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                            global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                            global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                            if row % 2 == 0:
                                global_routing_table[node][south * self.args.radix + 3] = self.args.radix + 3
                            else:
                                global_routing_table[node][north * self.args.radix + 3] = self.args.radix + 3
                else:
                    if row == 0 and col == 0:
                        global_routing_table[node][east * self.args.radix + 0] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                    elif row == 0 and col == self.nodes_in_dimension - 1:
                        global_routing_table[node][south * self.args.radix + 1] = self.args.radix + 0
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 1
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 2
                    elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][west * self.args.radix + 2] = self.args.radix + 1
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 2
                    elif row == self.nodes_in_dimension - 1 and col == 0:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][north * self.args.radix + 3] = self.args.radix + 2
                    else:
                        if row == 0:
                            if col % 2 == 0:
                                global_routing_table[node][east * self.args.radix + 0] = self.args.radix + 0
                                global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                                global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                                global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                            else:
                                global_routing_table[node][west * self.args.radix + 0] = self.args.radix + 0
                                global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                                global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                                global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        elif col == self.nodes_in_dimension - 1:
                            if row % 2 == 0:
                                global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                                global_routing_table[node][south * self.args.radix + 1] = self.args.radix + 1
                                global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                                global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                            else:
                                global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                                global_routing_table[node][north * self.args.radix + 1] = self.args.radix + 1
                                global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                                global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        elif row == self.nodes_in_dimension - 1:
                            if col % 2 == 0:
                                global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                                global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                                global_routing_table[node][west * self.args.radix + 2] = self.args.radix + 2
                                global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                            else:
                                global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                                global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                                global_routing_table[node][east * self.args.radix + 2] = self.args.radix + 2
                                global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        elif col == 0:
                            if row % 2 == 0:
                                global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                                global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                                global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                                global_routing_table[node][north * self.args.radix + 3] = self.args.radix + 3
                            else:
                                global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                                global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                                global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                                global_routing_table[node][south * self.args.radix + 3] = self.args.radix + 3
            elif self.args.topology == 'SM_Bi':
                assert self.args.radix == 5
                if row == 0 and col == 0:
                    global_routing_table[node][east * self.args.radix + 4] = self.args.radix + 0
                    global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                    global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                    global_routing_table[node][south * self.args.radix + 3] = self.args.radix + 3
                elif row == 0 and col == self.nodes_in_dimension - 1:
                    global_routing_table[node][west * self.args.radix + 0] = self.args.radix + 0
                    global_routing_table[node][south * self.args.radix + 4] = self.args.radix + 1
                    global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                    global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                    global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                    global_routing_table[node][north * self.args.radix + 1] = self.args.radix + 1
                    global_routing_table[node][west * self.args.radix + 4] = self.args.radix + 2
                    global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                elif row == self.nodes_in_dimension - 1 and col == 0:
                    global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                    global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                    global_routing_table[node][east * self.args.radix + 2] = self.args.radix + 2
                    global_routing_table[node][north * self.args.radix + 4] = self.args.radix + 3
                else:
                    if row == 0:
                        global_routing_table[node][east * self.args.radix + 4] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        global_routing_table[node][west * self.args.radix + 0] = self.args.radix + 4
                    elif col == self.nodes_in_dimension - 1:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][south * self.args.radix + 4] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        global_routing_table[node][north * self.args.radix + 1] = self.args.radix + 4
                    elif row == self.nodes_in_dimension - 1:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][west * self.args.radix + 4] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                        global_routing_table[node][east * self.args.radix + 2] = self.args.radix + 4
                    elif col == 0:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][north * self.args.radix + 4] = self.args.radix + 3
                        global_routing_table[node][south * self.args.radix + 3] = self.args.radix + 4
            elif self.args.topology == 'SM_Uni':
                if row == 0 and col == 0:
                    global_routing_table[node][east * self.args.radix + 0] = self.args.radix + 0
                    global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                    global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                elif row == 0 and col == self.nodes_in_dimension - 1:
                    global_routing_table[node][south * self.args.radix + 1] = self.args.radix + 0
                    global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 1
                    global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 2
                elif row == self.nodes_in_dimension - 1 and col == self.nodes_in_dimension - 1:
                    global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                    global_routing_table[node][west * self.args.radix + 2] = self.args.radix + 1
                    global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 2
                elif row == self.nodes_in_dimension - 1 and col == 0:
                    global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                    global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                    global_routing_table[node][north * self.args.radix + 3] = self.args.radix + 2
                else:
                    if row == 0:
                        global_routing_table[node][east * self.args.radix + 0] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                    elif col == self.nodes_in_dimension - 1:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][south * self.args.radix + 1] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                    elif row == self.nodes_in_dimension - 1:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][west * self.args.radix + 2] = self.args.radix + 2
                        global_routing_table[node][west * self.args.radix + 1] = self.args.radix + 3
                    elif col == 0:
                        global_routing_table[node][north * self.args.radix + 2] = self.args.radix + 0
                        global_routing_table[node][east * self.args.radix + 3] = self.args.radix + 1
                        global_routing_table[node][south * self.args.radix + 0] = self.args.radix + 2
                        global_routing_table[node][north * self.args.radix + 3] = self.args.radix + 3

        for key in global_routing_table:
            print("Router " + str(key) + ": " + str(global_routing_table[key]))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--nodes', default=9, type=int,
                        help='network nodes, default is 16')
    parser.add_argument('--radix', default=5, type=int,
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


def get_NI(source_node, dest_node, nodes_in_dimension, topology, radix, second=False):
    row = source_node // nodes_in_dimension
    col = source_node % nodes_in_dimension
    if topology == 'torus':
        mesh = False
    else:
        mesh = True

    north = None
    south = None
    east = None
    west = None
    # TODO: Add comments
    if row == 0 and not mesh:
        if nodes_in_dimension > 2:
            north = source_node + nodes_in_dimension * (nodes_in_dimension - 1)
    elif row != 0:
        north = source_node - nodes_in_dimension

    if row == nodes_in_dimension - 1 and not mesh:
        if nodes_in_dimension > 2:
            south = source_node - nodes_in_dimension * (nodes_in_dimension - 1)
    elif row != nodes_in_dimension - 1:
        south = source_node + nodes_in_dimension

    if col == 0 and not mesh:
        if nodes_in_dimension > 2:
            west = source_node + nodes_in_dimension - 1
    elif col != 0:
        west = source_node - 1

    if col == nodes_in_dimension - 1 and not mesh:
        if nodes_in_dimension > 2:
            east = source_node - nodes_in_dimension + 1
    elif col != nodes_in_dimension - 1:
        east = source_node + 1

    assert (dest_node == north) or (dest_node == east) or (dest_node == south) or (dest_node == west)

    dest_ni = None
    if topology == 'torus' or topology == 'mesh':
        if dest_node == north:
            dest_ni = radix * dest_node + 2
        elif dest_node == east:
            dest_ni = radix * dest_node + 3
        elif dest_node == south:
            dest_ni = radix * dest_node + 0
        elif dest_node == west:
            dest_ni = radix * dest_node + 1
    elif topology == 'SM_Uni':
        if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension:
            if row == 0 and col == 0:
                if dest_node == east and not second:
                    dest_ni = radix * dest_node + 3
                elif dest_node == east and second:
                    dest_ni = radix * dest_node + 0
                elif dest_node == south:
                    dest_ni = radix * dest_node + 0
                else:
                    raise RuntimeError("Wrong dest node")
            elif row == 0 and col == nodes_in_dimension - 1:
                if dest_node == south and not second:
                    dest_ni = radix * dest_node + 0
                elif dest_node == south and second:
                    dest_ni = radix * dest_node + 1
                elif dest_node == west:
                    dest_ni = radix * dest_node + 1
                else:
                    raise RuntimeError("Wrong dest node")
            elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                if dest_node == west and not second:
                    dest_ni = radix * dest_node + 1
                elif dest_node == west and second:
                    dest_ni = radix * dest_node + 2
                elif dest_node == north:
                    dest_ni = radix * dest_node + 2
                else:
                    raise RuntimeError("Wrong dest node")
            elif row == nodes_in_dimension - 1 and col == 0:
                if dest_node == north and not second:
                    dest_ni = radix * dest_node + 2
                elif dest_node == north and second:
                    dest_ni = radix * dest_node + 3
                elif dest_node == east:
                    dest_ni = radix * dest_node + 3
                else:
                    raise RuntimeError("Wrong dest node")
            else:
                if row == 0:
                    if dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == west:
                        dest_ni = radix * dest_node + 1
                    else:
                        raise RuntimeError("Wrong dest node")
                elif col == nodes_in_dimension - 1:
                    if dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == north:
                        dest_ni = radix * dest_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1:
                    if dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == east:
                        dest_ni = radix * dest_node + 3
                    else:
                        raise RuntimeError("Wrong dest node")
                elif col == 0:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == south:
                        dest_ni = radix * dest_node + 0
                    else:
                        raise RuntimeError("Wrong dest node")
        else:
            if dest_node == north:
                dest_ni = radix * dest_node + 2
            elif dest_node == east:
                dest_ni = radix * dest_node + 3
            elif dest_node == south:
                dest_ni = radix * dest_node + 0
            elif dest_node == west:
                dest_ni = radix * dest_node + 1
    elif topology == 'SM_Bi':
        if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension:
            if row == 0 and col == 0:
                if dest_node == east and not second:
                    dest_ni = radix * dest_node + 3
                elif dest_node == east and second:
                    dest_ni = radix * dest_node + 4
                elif dest_node == south and not second:
                    dest_ni = radix * dest_node + 0
                elif dest_node == south and second:
                    dest_ni = radix * dest_node + 3
                else:
                    raise RuntimeError("Wrong dest node")
            elif row == 0 and col == nodes_in_dimension - 1:
                if dest_node == west and not second:
                    dest_ni = radix * dest_node + 1
                elif dest_node == west and second:
                    dest_ni = radix * dest_node + 0
                elif dest_node == south and not second:
                    dest_ni = radix * dest_node + 0
                elif dest_node == south and second:
                    dest_ni = radix * dest_node + 4
                else:
                    raise RuntimeError("Wrong dest node")
            elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                if dest_node == north and not second:
                    dest_ni = radix * dest_node + 2
                elif dest_node == north and second:
                    dest_ni = radix * dest_node + 1
                elif dest_node == west and not second:
                    dest_ni = radix * dest_node + 1
                elif dest_node == west and second:
                    dest_ni = radix * dest_node + 4
                else:
                    raise RuntimeError("Wrong dest node")
            elif row == nodes_in_dimension - 1 and col == 0:
                if dest_node == north and not second:
                    dest_ni = radix * dest_node + 2
                elif dest_node == north and second:
                    dest_ni = radix * dest_node + 4
                elif dest_node == east and not second:
                    dest_ni = radix * dest_node + 3
                elif dest_node == east and second:
                    dest_ni = radix * dest_node + 2
                else:
                    raise RuntimeError("Wrong dest node")
            else:
                if row == 0:
                    if dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 4
                    elif dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south:
                        dest_ni = radix * dest_node + 0
                    else:
                        raise RuntimeError("Wrong dest node")
                elif col == nodes_in_dimension - 1:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 4
                    elif dest_node == west:
                        dest_ni = radix * dest_node + 1
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1:
                    if dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 4
                    elif dest_node == north:
                        dest_ni = radix * dest_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif col == 0:
                    if dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 4
                    elif dest_node == east:
                        dest_ni = radix * dest_node + 3
                    else:
                        raise RuntimeError("Wrong dest node")
        else:
            if dest_node == north:
                dest_ni = radix * dest_node + 2
            elif dest_node == east:
                dest_ni = radix * dest_node + 3
            elif dest_node == south:
                dest_ni = radix * dest_node + 0
            elif dest_node == west:
                dest_ni = radix * dest_node + 1
    elif topology == 'SM_Alter':
        if row == 0 or col == 0 or row == nodes_in_dimension - 1 or col == nodes_in_dimension:
            if nodes_in_dimension % 2 == 0:
                if row == 0 and col == 0:
                    if dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 3
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == 0 and col == nodes_in_dimension - 1:
                    if dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 1
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == 0:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                else:
                    if row == 0:
                        if col % 2 == 0:
                            if dest_node == east and not second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == east and second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == west and not second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == west and second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            else:
                                raise RuntimeError("Wrong dest node")
                    elif col == nodes_in_dimension - 1:
                        if row % 2 == 0:
                            if dest_node == south and not second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == south and second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == north and not second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == north and second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            else:
                                raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1:
                        if col % 2 == 0:
                            if dest_node == east and not second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == east and second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == west and not second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == west and second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            else:
                                raise RuntimeError("Wrong dest node")
                    elif col == 0:
                        if row % 2 == 0:
                            if dest_node == south and not second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == south and second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == north and not second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == north and second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            else:
                                raise RuntimeError("Wrong dest node")
            else:
                if row == 0 and col == 0:
                    if dest_node == east and not second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east and second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south:
                        dest_ni = radix * dest_node + 0
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == 0 and col == nodes_in_dimension - 1:
                    if dest_node == south and not second:
                        dest_ni = radix * dest_node + 0
                    elif dest_node == south and second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west:
                        dest_ni = radix * dest_node + 1
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == nodes_in_dimension - 1:
                    if dest_node == west and not second:
                        dest_ni = radix * dest_node + 1
                    elif dest_node == west and second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north:
                        dest_ni = radix * dest_node + 2
                    else:
                        raise RuntimeError("Wrong dest node")
                elif row == nodes_in_dimension - 1 and col == 0:
                    if dest_node == north and not second:
                        dest_ni = radix * dest_node + 2
                    elif dest_node == north and second:
                        dest_ni = radix * dest_node + 3
                    elif dest_node == east:
                        dest_ni = radix * dest_node + 3
                    else:
                        raise RuntimeError("Wrong dest node")
                else:
                    if row == 0:
                        if col % 2 == 0:
                            if dest_node == east and not second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == east and second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == west and not second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == west and second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            else:
                                raise RuntimeError("Wrong dest node")
                    elif col == nodes_in_dimension - 1:
                        if row % 2 == 0:
                            if dest_node == south and not second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == south and second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == north and not second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == north and second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            else:
                                raise RuntimeError("Wrong dest node")
                    elif row == nodes_in_dimension - 1:
                        if col % 2 == 0:
                            if dest_node == west and not second:
                                dest_ni = radix * dest_node + 1
                            elif dest_node == west and second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == east and not second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == east and second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == west:
                                dest_ni = radix * dest_node + 1
                            else:
                                raise RuntimeError("Wrong dest node")
                    elif col == 0:
                        if row % 2 == 0:
                            if dest_node == north and not second:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == north and second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == south:
                                dest_ni = radix * dest_node + 0
                            else:
                                raise RuntimeError("Wrong dest node")
                        else:
                            if dest_node == south and not second:
                                dest_ni = radix * dest_node + 0
                            elif dest_node == south and second:
                                dest_ni = radix * dest_node + 3
                            elif dest_node == north:
                                dest_ni = radix * dest_node + 2
                            elif dest_node == east:
                                dest_ni = radix * dest_node + 3
                            else:
                                raise RuntimeError("Wrong dest node")
        else:
            if dest_node == north:
                dest_ni = radix * dest_node + 2
            elif dest_node == east:
                dest_ni = radix * dest_node + 3
            elif dest_node == south:
                dest_ni = radix * dest_node + 0
            elif dest_node == west:
                dest_ni = radix * dest_node + 1
    return dest_ni




if __name__ == '__main__':
    main()
