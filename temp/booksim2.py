import argparse
import os
import sys

sys.path.append('../src/booksim2/src')

from sim_object import SimObject
import pybooksim
from eventq import EventQueue
from message_buffer import *


class BookSim2(SimObject):
    def __init__(self, args, eventq):
        super().__init__(eventq)
        self.name = 'BookSimNI'
        self.args = args
        self.booksim = pybooksim.BookSim(args.booksim_config)
        self.local_eventq = EventQueue()
        self.in_message_buffers = None
        self.out_message_buffers = None
        self.reduce_scatter_time_track_dict = None
        self.all_gather_time_track_dict = None
        self.per_message_max_latency = None
        self.links_usage = None
        self.link_start_times = {}
        self.link_end_times = {}


    # '''
    # set_message_buffers() - set message buffers connected with HMCs
    # @in_message_buffers: message buffers for incoming messages
    # @out_message_buffers: message buffers for outgoing messages
    # '''
    # def set_message_buffers(self, in_message_buffers, out_message_buffers):
    #     self.in_message_buffers = in_message_buffers
    #     self.out_message_buffers = out_message_buffers
    # # end of set_message_buffers
    #
    # def set_parameters(self, reduce_scatter_time_track_dict, all_gather_time_track_dict, per_message_max_latency, links_usage, link_start_times, link_end_times):
    #     self.reduce_scatter_time_track_dict = reduce_scatter_time_track_dict
    #     self.all_gather_time_track_dict = all_gather_time_track_dict
    #     self.per_message_max_latency = per_message_max_latency
    #     self.links_usage = links_usage
    #     self.link_start_times = link_start_times
    #     self.link_end_times = link_end_times


    '''
    schedule() - schedule the event at a given time
    @event: the event to be scheduled
    @cycle: scheduled time
    '''
    def schedule(self, event, cycle):
        self.global_eventq.schedule(self, cycle)
    # end of schedule()


    '''
    process() - event processing function in a particular cycle
    @cur_cycle: the current cycle that with events to be processed
    '''
    def process(self, cur_cycle):
        # send messages
        for i in range(self.args.num_hmcs):
            for j in range(self.args.radix):
                print("Yah")
                msg_id = self.booksim.IssueMessage(3, 1, 4, 1, 8192, pybooksim.Message.ReduceData,
                                              pybooksim.Message.HeadTail, 0, True)
                print(msg_id)
                # message = self.in_message_buffers[i][j].peek(cur_cycle)
                # if message != None:
                #     src = message.src // self.args.radix
                #     src_ni = message.src % self.args.radix
                #     dest = message.dest // self.args.radix
                #     dest_ni = message.dest % self.args.radix
                #     assert src == i
                #     assert src_ni == j
                #     print(message.flow)
                #     print(message.src)
                #     print(message.dest)
                #     print(message.id)
                #     print(message.size)
                #     print(message.type)
                #     print(message.submsgtype)
                #     print(message.priority)
                #     print(message.end)
                #     msg_id = self.booksim.IssueMessage(message.flow, message.src, message.dest, message.id, message.size, message.type, message.submsgtype, message.priority, message.end)
                #     if msg_id == -1:
                #         self.schedule(self, cur_cycle + 1)
                #         continue
                #     self.in_message_buffers[i][j].dequeue(cur_cycle)
                #     # total_in_flight_message = self.links_usage[src, dest][0]
                #     # total_unused_cycles = self.links_usage[src, dest][1]
                #     # last_used_cycle = self.links_usage[src, dest][2]
                #     # if total_in_flight_message == 0 and last_used_cycle != -1:
                #     #     total_unused_cycles += (cur_cycle - last_used_cycle - 1)
                #     # total_in_flight_message += 1
                #     # self.links_usage[src, dest] = (total_in_flight_message, total_unused_cycles, last_used_cycle)
                #     # print("Src " + str(src) + " Dest " + "Dest " + str(dest))
                #     if (src, dest) not in self.link_start_times.keys():
                #         self.link_start_times[src, dest] = []
                #     self.link_start_times[src, dest].append(cur_cycle)
                #     #print('{} | {} | issues a {} message for flow {} from HMC-{} (NI {}) to HMC-{} (NI {})'.format(cur_cycle, self.name, message.type, message.flow, src, src_ni, dest, dest_ni))

        self.booksim.SetSimTime(cur_cycle)
        self.booksim.WakeUp()

        # # peek and receive messages
        # for i in range(self.args.num_hmcs):
        #     for j in range(self.args.radix):
        #         dest_node = i * self.args.radix + j
        #         flow, src_node, msgtype, end, priority = self.booksim.PeekMessage(dest_node, 0)
        #         if src_node != -1:
        #             assert flow != -1
        #             src = src_node // self.args.radix
        #             src_ni = src_node % self.args.radix
        #             if self.out_message_buffers[i][j].is_full():
        #                 continue
        #             message = Message(flow, None, src_node, dest_node, self.args.sub_message_size, msgtype, None, priority, end)
        #             self.out_message_buffers[i][j].enqueue(message, cur_cycle, 1)
        #             self.booksim.DequeueMessage(dest_node, 0)
        #             # total_in_flight_message = self.links_usage[src, i][0]
        #             # total_unused_cycles = self.links_usage[src, i][1]
        #             # last_used_cycle = self.links_usage[src, i][2]
        #             # assert total_in_flight_message > 0
        #             # total_in_flight_message -= 1
        #             # if total_in_flight_message == 0:
        #             #     last_used_cycle = cur_cycle
        #             # self.links_usage[src, i] = (total_in_flight_message, total_unused_cycles, last_used_cycle)
        #             if (src, i) not in self.link_end_times.keys():
        #                 self.link_end_times[src, i] = []
        #             self.link_end_times[src, i].append(cur_cycle)
        #             #print('{} | {} | peek a {} message for flow {} to HMC-{} (NI {}) from HMC-{} (NI {})'.format(cur_cycle, self.name, msgtype, flow, i, j, src, src_ni))
        #
        # if not self.booksim.Idle():
        #     self.schedule(self, cur_cycle + 1)
    # end of process()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--num-hmcs', default=16, type=int,
                        help='number of hybrid memory cubes, default=16')
    parser.add_argument('--num-vaults', default=16, type=int,
                        help='number of vaults per hybrid memory cube')
    parser.add_argument('--mini-batch-size', default=256, type=int,
                        help='number of mini batch size for all hmc accelerator, distributed to all vault npu of each accelerator')
    parser.add_argument('--booksim-config',
                        default='{}/src/booksim2/runfiles/mesh/anynet_mesh_16_200.cfg'.format(os.environ['SIMHOME']),
                        required=False,
                        help='required config file for booksim')
    parser.add_argument('--booksim-network', default='mesh',
                        help='network topology (torus|mesh|bigraph|mesh_fermat), default is torus')
    parser.add_argument('--message-size', default=8192, type=int,
                        help='size of a message, default is 256 bytes, 0 means treat the whole chunk of gradients as a message')
    parser.add_argument('--sub-message-size', default=8192, type=int,
                        help='size of a sub message, default is 256 bytes')
    parser.add_argument('--flits-per-packet', default=16, type=int,
                        help='Number of payload flits per packet, packet header is not considered here, that will be added in booksim')
    parser.add_argument('--bandwidth', default=200, type=int,
                        help='On chip BW between chiplets')

    args = parser.parse_args()
    global_eventq = EventQueue()
    network = BookSim2(args, global_eventq)
    network.process(1)