import copy
import math

from network.network import Network

class FoldedTorus(Network):
    def __init__(self, args):
        super().__init__(args)

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

    '''
    build_graph() - build the topology graph
    @filename: filename to generate topology dotfile, optional
    '''
    def build_graph(self):
        # https://tenstorrent.com/en/vision/community-highlight-tenstorrent-wormhole-series-part-1-physicalities
        per_dim_nodes = int(math.sqrt(self.args.num_hmcs))
        for node in range(self.args.num_hmcs):
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
                    self.switch_to_switch[node].append((dimension_nodes[2], 1))
                    self.switch_to_switch[node].append((dimension_nodes[1], 1))
                elif node_index == 1:
                    self.switch_to_switch[node].append((dimension_nodes[3], 1))
                    self.switch_to_switch[node].append((dimension_nodes[0], 1))
                elif node_index == len(dimension_nodes) - 2:
                    self.switch_to_switch[node].append((dimension_nodes[node_index + 1], 1))
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 2], 1))
                elif node_index == len(dimension_nodes) - 1:
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 1], 1))
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 2], 1))
                else:
                    self.switch_to_switch[node].append((dimension_nodes[node_index + 2], 1))
                    self.switch_to_switch[node].append((dimension_nodes[node_index - 2], 1))

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
