import argparse


class Topology:
    def __init__(self, args):
        self.args = args

    def print_topology(self):
        # Src: Kite: A Family of Heterogeneous Interposer Topologies Enabled via Accurate Interconnect Modeling
        # In mesh, per flit latency is 20. Based on Kite paper, we get the latency 24. All the connectivities are also based on Kite paper.
        # Currently, this script only generates topology for 64 nodes(16 routers due to 4 way concentration).
        latency = 24
        self.switch_to_switch = {}
        self.switch_to_switch[0] = []
        self.switch_to_switch[0].append((1, latency))
        self.switch_to_switch[0].append((4, latency))

        self.switch_to_switch[1] = []
        self.switch_to_switch[1].append((0, latency))
        self.switch_to_switch[1].append((2, latency))
        self.switch_to_switch[1].append((5, latency))

        self.switch_to_switch[2] = []
        self.switch_to_switch[2].append((1, latency))
        self.switch_to_switch[2].append((3, latency))
        self.switch_to_switch[2].append((6, latency))

        self.switch_to_switch[3] = []
        self.switch_to_switch[3].append((2, latency))
        self.switch_to_switch[3].append((7, latency))

        self.switch_to_switch[4] = []
        self.switch_to_switch[4].append((0, latency))
        self.switch_to_switch[4].append((5, latency))
        self.switch_to_switch[4].append((8, latency))

        self.switch_to_switch[5] = []
        self.switch_to_switch[5].append((1, latency))
        self.switch_to_switch[5].append((4, latency))
        self.switch_to_switch[5].append((6, latency))
        self.switch_to_switch[5].append((9, latency))

        self.switch_to_switch[6] = []
        self.switch_to_switch[6].append((2, latency))
        self.switch_to_switch[6].append((5, latency))
        self.switch_to_switch[6].append((7, latency))
        self.switch_to_switch[6].append((10, latency))

        self.switch_to_switch[7] = []
        self.switch_to_switch[7].append((3, latency))
        self.switch_to_switch[7].append((6, latency))
        self.switch_to_switch[7].append((11, latency))

        self.switch_to_switch[8] = []
        self.switch_to_switch[8].append((4, latency))
        self.switch_to_switch[8].append((9, latency))
        self.switch_to_switch[8].append((12, latency))

        self.switch_to_switch[9] = []
        self.switch_to_switch[9].append((5, latency))
        self.switch_to_switch[9].append((8, latency))
        self.switch_to_switch[9].append((10, latency))
        self.switch_to_switch[9].append((13, latency))

        self.switch_to_switch[10] = []
        self.switch_to_switch[10].append((6, latency))
        self.switch_to_switch[10].append((9, latency))
        self.switch_to_switch[10].append((11, latency))
        self.switch_to_switch[10].append((14, latency))

        self.switch_to_switch[11] = []
        self.switch_to_switch[11].append((7, latency))
        self.switch_to_switch[11].append((10, latency))
        self.switch_to_switch[11].append((15, latency))

        self.switch_to_switch[12] = []
        self.switch_to_switch[12].append((8, latency))
        self.switch_to_switch[12].append((13, latency))

        self.switch_to_switch[13] = []
        self.switch_to_switch[13].append((9, latency))
        self.switch_to_switch[13].append((12, latency))
        self.switch_to_switch[13].append((14, latency))

        self.switch_to_switch[14] = []
        self.switch_to_switch[14].append((10, latency))
        self.switch_to_switch[14].append((13, latency))
        self.switch_to_switch[14].append((15, latency))

        self.switch_to_switch[15] = []
        self.switch_to_switch[15].append((11, latency))
        self.switch_to_switch[15].append((14, latency))

        anynet_filename = ("cmesh_16_200.txt")

        with open(anynet_filename, 'w') as f:
            for node in range(16):
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
