import copy

from network.network import Network

class Kite(Network):
    def __init__(self, args):
        super().__init__(args)


    '''
    build_graph() - build the topology graph
    @filename: filename to generate topology dotfile, optional
    '''
    def build_graph(self):
        # Connectivity based on Kite paper.
        self.switch_to_switch[0] = []
        self.switch_to_switch[0].append((1, 1))
        self.switch_to_switch[0].append((4, 1))
        self.switch_to_switch[0].append((5, 1))
        self.switch_to_switch[1] = []
        self.switch_to_switch[1].append((0, 1))
        self.switch_to_switch[1].append((2, 1))
        self.switch_to_switch[1].append((4, 1))
        self.switch_to_switch[1].append((6, 1))
        self.switch_to_switch[2] = []
        self.switch_to_switch[2].append((1, 1))
        self.switch_to_switch[2].append((3, 1))
        self.switch_to_switch[2].append((5, 1))
        self.switch_to_switch[2].append((7, 1))
        self.switch_to_switch[3] = []
        self.switch_to_switch[3].append((2, 1))
        self.switch_to_switch[3].append((6, 1))
        self.switch_to_switch[3].append((7, 1))
        self.switch_to_switch[4] = []
        self.switch_to_switch[4].append((0, 1))
        self.switch_to_switch[4].append((1, 1))
        self.switch_to_switch[4].append((8, 1))
        self.switch_to_switch[4].append((9, 1))
        self.switch_to_switch[5] = []
        self.switch_to_switch[5].append((0, 1))
        self.switch_to_switch[5].append((2, 1))
        self.switch_to_switch[5].append((8, 1))
        self.switch_to_switch[5].append((10, 1))
        self.switch_to_switch[6] = []
        self.switch_to_switch[6].append((1, 1))
        self.switch_to_switch[6].append((3, 1))
        self.switch_to_switch[6].append((9, 1))
        self.switch_to_switch[6].append((11, 1))
        self.switch_to_switch[7] = []
        self.switch_to_switch[7].append((2, 1))
        self.switch_to_switch[7].append((3, 1))
        self.switch_to_switch[7].append((10, 1))
        self.switch_to_switch[7].append((11, 1))
        self.switch_to_switch[8] = []
        self.switch_to_switch[8].append((4, 1))
        self.switch_to_switch[8].append((5, 1))
        self.switch_to_switch[8].append((12, 1))
        self.switch_to_switch[8].append((13, 1))
        self.switch_to_switch[9] = []
        self.switch_to_switch[9].append((4, 1))
        self.switch_to_switch[9].append((6, 1))
        self.switch_to_switch[9].append((12, 1))
        self.switch_to_switch[9].append((14, 1))
        self.switch_to_switch[10] = []
        self.switch_to_switch[10].append((5, 1))
        self.switch_to_switch[10].append((7, 1))
        self.switch_to_switch[10].append((13, 1))
        self.switch_to_switch[10].append((15, 1))
        self.switch_to_switch[11] = []
        self.switch_to_switch[11].append((6, 1))
        self.switch_to_switch[11].append((7, 1))
        self.switch_to_switch[11].append((14, 1))
        self.switch_to_switch[11].append((15, 1))
        self.switch_to_switch[12] = []
        self.switch_to_switch[12].append((8, 1))
        self.switch_to_switch[12].append((9, 1))
        self.switch_to_switch[12].append((13, 1))
        self.switch_to_switch[13] = []
        self.switch_to_switch[13].append((8, 1))
        self.switch_to_switch[13].append((10, 1))
        self.switch_to_switch[13].append((12, 1))
        self.switch_to_switch[13].append((14, 1))
        self.switch_to_switch[14] = []
        self.switch_to_switch[14].append((9, 1))
        self.switch_to_switch[14].append((11, 1))
        self.switch_to_switch[14].append((13, 1))
        self.switch_to_switch[14].append((15, 1))
        self.switch_to_switch[15] = []
        self.switch_to_switch[15].append((10, 1))
        self.switch_to_switch[15].append((11, 1))
        self.switch_to_switch[15].append((14, 1))

        self.switch_to_switch_rs = copy.deepcopy(self.switch_to_switch)
        self.switch_to_switch_ag = copy.deepcopy(self.switch_to_switch)


    '''
        distance() - distance between two nodes
        @src: source node ID
        @dest: destination node ID
        '''

    def distance(self, src, dest):
        src_x = src // self.dimension
        src_y = src % self.dimension
        dest_x = dest // self.dimension
        dest_y = dest % self.dimension
        if self.mesh:
            dist = abs(src_x - dest_x) + abs(dest_x - dest_y)
        else:
            dist_x = abs(src_x - dest_x)
            dist_y = abs(src_y - dest_y)
            if dist_x > self.dimension // 2:
                dist_x = self.dimension - dist_x
            if dist_y > self.dimension // 2:
                dist_y = self.dimension - dist_y
            dist = dist_x + dist_y

        return dist
    # end of distance()
