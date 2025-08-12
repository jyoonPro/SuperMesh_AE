from abc import ABC, abstractmethod

class Network(ABC):
    def __init__(self, args):
        self.args = args
        self.nodes = args.nodes
        self.switch_to_switch = {}
        self.switch_to_switch_track = {}
        self.links_usage = {}
        self.total_possible_links = 0
        self.link_start_times = {}
        self.link_end_times = {}
        self.switch_to_switch_rs = {}
        self.switch_to_switch_ag = {}
        self.priority = [0] * self.nodes  # used for allocation sequence

    '''
    build_graph() - build the topology graph
    @filename: filename to generate topology dotfile, optional
    '''

    @abstractmethod
    def build_graph(self):
        pass
