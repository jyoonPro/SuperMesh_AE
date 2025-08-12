import argparse
import math


class Topology:
    def __init__(self, args):
        self.args = args

    def get_first_dimension_nodes(self, node, nodes_in_first_dim):
        row_index = node//nodes_in_first_dim
        row_start_index = row_index * nodes_in_first_dim
        node_list = []
        for i in range(nodes_in_first_dim):
            node_list.append(row_start_index+i)
        return node_list

    def get_second_dimension_nodes(self, node, nodes_in_first_dim, nodes_in_second_dim):
        col_index = node % nodes_in_first_dim
        node_list = []
        for i in range(nodes_in_second_dim):
            node_list.append(nodes_in_first_dim * i + col_index)
        return node_list

    def print_topology(self):
        # Src: Kite: A Family of Heterogeneous Interposer Topologies Enabled via Accurate Interconnect Modeling
        # In mesh, per flit latency is 20. Based on Kite paper, we get the longer link latency 33.
        # Currently, this script only generates topology for 64 nodes.
        total_nodes = 64
        per_dim_nodes = int(math.sqrt(total_nodes))
        self.switch_to_switch = {}
        latency_high = 33
        latency_low = 20
        for node in range(total_nodes):
            self.switch_to_switch[node] = []
            for dim in range(2):
                if dim == 0:
                    dimension_nodes = self.get_first_dimension_nodes(node, per_dim_nodes)
                elif dim == 1:
                    dimension_nodes = self.get_second_dimension_nodes(node, per_dim_nodes, per_dim_nodes)
                else:
                    raise RuntimeError('Error: Dimension {} is not supported yet'.format(dim))

                node_index = dimension_nodes.index(node)
                if node_index == 0:
                    self.switch_to_switch[node].append((dimension_nodes[2], latency_high))
                    self.switch_to_switch[node].append((dimension_nodes[1], latency_low))
                elif node_index == 1:
                    self.switch_to_switch[node].append((dimension_nodes[3], latency_high))
                    self.switch_to_switch[node].append((dimension_nodes[0], latency_low))
                elif node_index == len(dimension_nodes) - 2:
                    self.switch_to_switch[node].append((dimension_nodes[node_index + 1], latency_low))
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 2], latency_high))
                elif node_index == len(dimension_nodes) - 1:
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 1], latency_low))
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 2], latency_high))
                else:
                    self.switch_to_switch[node].append((dimension_nodes[node_index + 2], latency_high))
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 2], latency_high))

        anynet_filename = ("generate_anynet_files/folded_torus_64_200.txt")

        with open(anynet_filename, 'w') as f:
            for node in range(64):
                line = "router " + str(node)
                for i in range(4):
                    line += " node " + str(node * 4 + i)
                for neighbor_node in self.switch_to_switch[node]:
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
