import copy

from network.network import Network

class KNCube(Network):
    def __init__(self, args, mesh=False):
        super().__init__(args)
        self.mesh = mesh
        self.dimension = args.per_dim_nodes
        if mesh == True:
            self.type = 'Mesh'
            corners = [0, self.dimension - 1, self.nodes - self.dimension, self.nodes - 1]
            for node in range(self.nodes):
                depth = 0
                for corner in corners:
                    distance = self.distance(node, corner)
                    if depth < distance:
                        depth = distance
                self.priority[node] = depth
        else:
            self.type = 'Torus'
        self.corner_links = {}
        self.border_links = {}
        self.internal_links = {}
        self.added_links = []


    '''
    build_graph() - build the topology graph
    @filename: filename to generate topology dotfile, optional
    '''
    def build_graph(self):
        for node in range(self.nodes):
            self.switch_to_switch[node] = []
            self.switch_to_switch_track[node] = []

            row = node // self.dimension
            col = node % self.dimension

            north = None
            south = None
            east = None
            west = None
            if row == 0 and not self.mesh:
                if self.dimension > 2:
                    north = node + self.dimension * (self.dimension - 1)
            elif row != 0:
                north = node - self.dimension

            if row == self.dimension - 1 and not self.mesh:
                if self.dimension > 2:
                    south = node - self.dimension * (self.dimension - 1)
            elif row != self.dimension - 1:
                south = node + self.dimension

            if col == 0 and not self.mesh:
                if self.dimension > 2:
                    west = node + self.dimension - 1
            elif col != 0:
                west = node - 1

            if col == self.dimension - 1 and not self.mesh:
                if self.dimension > 2:
                    east = node - self.dimension + 1
            elif col != self.dimension - 1:
                east = node + 1

            if north != None:
                self.switch_to_switch[node].append((north, 1))
                self.links_usage[node, north] = (0, 0, -1)
                self.link_start_times[node, north] = []
                self.link_end_times[node, north] = []
                self.total_possible_links += 1
            if south != None:
                self.switch_to_switch[node].append((south, 1))
                self.links_usage[node, south] = (0, 0, -1)
                self.link_start_times[node, south] = []
                self.link_end_times[node, south] = []
                self.total_possible_links += 1
            if west != None:
                self.switch_to_switch[node].append((west, 1))
                self.links_usage[node, west] = (0, 0, -1)
                self.link_start_times[node, west] = []
                self.link_end_times[node, west] = []
                self.total_possible_links += 1
            if east != None:
                self.switch_to_switch[node].append((east, 1))
                self.links_usage[node, east] = (0, 0, -1)
                self.link_start_times[node, east] = []
                self.link_end_times[node, east] = []
                self.total_possible_links += 1

            if row == 0 and col == 0:
                self.corner_links[(node, east)] = set()
                self.corner_links[(node, south)] = set()
            elif row == 0 and col == self.dimension-1:
                self.corner_links[(node, west)] = set()
                self.corner_links[(node, south)] = set()
            elif row == self.dimension-1 and col == 0:
                self.corner_links[(node, east)] = set()
                self.corner_links[(node, north)] = set()
            elif row == self.dimension-1 and col == self.dimension-1:
                self.corner_links[(node, west)] = set()
                self.corner_links[(node, north)] = set()
            elif row == 0:
                self.border_links[(node, east)] = set()
                self.border_links[(node, west)] = set()
                self.internal_links[(node, south)] = set()
            elif row == self.dimension-1:
                self.border_links[(node, east)] = set()
                self.border_links[(node, west)] = set()
                self.internal_links[(node, north)] = set()
            elif col == 0:
                self.border_links[(node, north)] = set()
                self.border_links[(node, south)] = set()
                self.internal_links[(node, east)] = set()
            elif col == self.dimension-1:
                self.border_links[(node, north)] = set()
                self.border_links[(node, south)] = set()
                self.internal_links[(node, west)] = set()
            else:
                self.internal_links[(node, north)] = set()
                self.internal_links[(node, south)] = set()
                self.internal_links[(node, east)] = set()
                self.internal_links[(node, west)] = set()

        self.switch_to_switch_rs = copy.deepcopy(self.switch_to_switch)
        self.switch_to_switch_ag = copy.deepcopy(self.switch_to_switch)

        for node in range(self.nodes):
            row = node // self.dimension
            col = node % self.dimension

            north = None
            south = None
            east = None
            west = None
            if row == 0 and not self.mesh:
                if self.dimension > 2:
                    north = node + self.dimension * (self.dimension - 1)
            elif row != 0:
                north = node - self.dimension

            if row == self.dimension - 1 and not self.mesh:
                if self.dimension > 2:
                    south = node - self.dimension * (self.dimension - 1)
            elif row != self.dimension - 1:
                south = node + self.dimension

            if col == 0 and not self.mesh:
                if self.dimension > 2:
                    west = node + self.dimension - 1
            elif col != 0:
                west = node - 1

            if col == self.dimension - 1 and not self.mesh:
                if self.dimension > 2:
                    east = node - self.dimension + 1
            elif col != self.dimension - 1:
                east = node + 1

            if self.args.booksim_network == 'SM_Bi':
                if row == 0 and col == 0:
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.total_possible_links += 2
                elif row == 0 and col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 2
                elif row == self.dimension - 1 and col == 0:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.total_possible_links += 2
                elif row == self.dimension - 1 and col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 2
                elif row == 0 or row == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 2
                elif col == 0 or col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.total_possible_links += 2
            elif self.args.booksim_network == 'Partial_SM_Bi':
                if row == 0 and col == 0:
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.total_possible_links += 2
                elif row == 0 and col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 2
                elif row == self.dimension - 1 and col == 0:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    # self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.total_possible_links += 1
                elif row == self.dimension - 1 and col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    # self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 1
                elif row == 0:
                    self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 2
                elif col == 0 or col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.total_possible_links += 2
            elif self.args.booksim_network == 'SM_Alter':
                if self.dimension % 2 == 0:
                    if row == 0 or row == self.dimension - 1:
                        if col % 2 == 0:
                            if east is not None:
                                self.switch_to_switch_ag[node].insert(0, (east, 0))
                                self.total_possible_links += 1
                                self.added_links.append((node, east))
                        else:
                            if west is not None:
                                self.switch_to_switch_ag[node].insert(0, (west, 0))
                                self.total_possible_links += 1
                                self.added_links.append((node, west))
                    if col == 0 or col == self.dimension - 1:
                        if row % 2 == 0:
                            if south is not None:
                                self.switch_to_switch_ag[node].insert(0, (south, 0))
                                self.total_possible_links += 1
                                self.added_links.append((node, south))
                        else:
                            if north is not None:
                                self.switch_to_switch_ag[node].insert(0, (north, 0))
                                self.total_possible_links += 1
                                self.added_links.append((node, north))
                else:
                    if row == 0 and col == 0:
                        if east is not None:
                            self.switch_to_switch_ag[node].insert(0, (east, 0))
                            self.total_possible_links += 1
                    elif row == 0 and col == self.dimension - 1:
                        if south is not None:
                            self.switch_to_switch_ag[node].insert(0, (south, 0))
                            self.total_possible_links += 1
                    elif row == self.dimension - 1 and col == self.dimension - 1:
                        if west is not None:
                            self.switch_to_switch_ag[node].insert(0, (west, 0))
                            self.total_possible_links += 1
                    elif row == self.dimension - 1 and col == 0:
                        if north is not None:
                            self.switch_to_switch_ag[node].insert(0, (north, 0))
                            self.total_possible_links += 1
                    elif row == 0:
                        if col % 2 == 0:
                            if east is not None:
                                self.switch_to_switch_ag[node].insert(0, (east, 0))
                                self.total_possible_links += 1
                        else:
                            if west is not None:
                                self.switch_to_switch_ag[node].insert(0, (west, 0))
                                self.total_possible_links += 1
                    elif col == self.dimension - 1:
                        if row % 2 == 0:
                            if south is not None:
                                self.switch_to_switch_ag[node].insert(0, (south, 0))
                                self.total_possible_links += 1
                        else:
                            if north is not None:
                                self.switch_to_switch_ag[node].insert(0, (north, 0))
                                self.total_possible_links += 1
                    elif row == self.dimension - 1:
                        if col % 2 == 1:
                            if east is not None:
                                self.switch_to_switch_ag[node].insert(0, (east, 0))
                                self.total_possible_links += 1
                        else:
                            if west is not None:
                                self.switch_to_switch_ag[node].insert(0, (west, 0))
                                self.total_possible_links += 1
                    elif col == 0:
                        if row % 2 == 1:
                            if south is not None:
                                self.switch_to_switch_ag[node].insert(0, (south, 0))
                                self.total_possible_links += 1
                        else:
                            if north is not None:
                                self.switch_to_switch_ag[node].insert(0, (north, 0))
                                self.total_possible_links += 1
            elif self.args.booksim_network == 'Partial_SM_Alter':
                if self.dimension % 2 == 0:
                    if row == 0:
                        if col % 2 == 0:
                            if east is not None:
                                self.switch_to_switch_ag[node].insert(0, (east, 0))
                                self.total_possible_links += 1
                        else:
                            if west is not None:
                                self.switch_to_switch_ag[node].insert(0, (west, 0))
                                self.total_possible_links += 1
                    if col == 0 or col == self.dimension - 1:
                        if row % 2 == 0:
                            if south is not None:
                                self.switch_to_switch_ag[node].insert(0, (south, 0))
                                self.total_possible_links += 1
                        else:
                            if north is not None:
                                self.switch_to_switch_ag[node].insert(0, (north, 0))
                                self.total_possible_links += 1
                else:
                    raise RuntimeError("Partial SM_Alter for odd dimension is not implemented yet")
            # TODO: Add comments why we add reverse order links for RS topology for SM_Uni
            elif self.args.booksim_network == 'SM_Uni':
                if row == 0 and col == 0:
                    self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (south, 0))
                elif row == 0 and col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (west, 0))
                elif row == self.dimension - 1 and col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (north, 0))
                elif row == self.dimension - 1 and col == 0:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (east, 0))
                elif row == 0:
                    self.switch_to_switch_ag[node].insert(0, (east, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (west, 0))
                elif col == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (south, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (north, 0))
                elif row == self.dimension - 1:
                    self.switch_to_switch_ag[node].insert(0, (west, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (east, 0))
                elif col == 0:
                    self.switch_to_switch_ag[node].insert(0, (north, 0))
                    self.total_possible_links += 1
                    self.switch_to_switch_rs[node].insert(0, (south, 0))

        if (self.args.booksim_network == 'SM_Bi' or self.args.booksim_network == 'SM_Alter' or
                self.args.booksim_network == 'Partial_SM_Bi' or self.args.booksim_network == 'Partial_SM_Alter'):
            self.switch_to_switch_rs = copy.deepcopy(self.switch_to_switch_ag)

        computed_links = 0
        mesh_computed_links = 2 * self.dimension * (self.dimension - 1) * 2
        if self.args.booksim_network == 'mesh':
            computed_links = mesh_computed_links
        elif self.args.booksim_network == 'SM_Bi':
            computed_links = mesh_computed_links + 4 * (self.dimension - 1) * 2
        elif self.args.booksim_network == 'SM_Uni':
            computed_links = mesh_computed_links + 4 * (self.dimension - 1) * 1
        elif self.args.booksim_network == 'SM_Alter':
            computed_links = mesh_computed_links + 4 * (self.dimension // 2) * 2
        if (self.args.booksim_network == 'mesh' or self.args.booksim_network == 'SM_Bi' or
                self.args.booksim_network == 'SM_Uni' or self.args.booksim_network == 'SM_Alter'):
            assert computed_links == self.total_possible_links, "Added links in topology is not equal to the theoretically computed links"

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
