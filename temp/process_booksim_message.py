import sys
import os
sys.path.append('booksim3/src')

from sim_object import SimObject
import pybooksim
from eventq import EventQueue
from message_buffer import *

def main():
    # booksim = pybooksim.BookSim('{}/src/booksim4/runfiles/mesh/anynet_fatmesh_uni_9_200.cfg'.format(os.environ['SIMHOME']))
    # # Node 0
    # msg_id = booksim.IssueMessage(3, 0, 4, 0, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, False)
    # msg_id = booksim.IssueMessage(3, 1, 7, 1, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 2, 12, 2, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 1
    # msg_id = booksim.IssueMessage(3, 4, 8, 3, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 5, 11, 4, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 6, 16, 5, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 7, 1, 6, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 2
    # msg_id = booksim.IssueMessage(3, 9, 21, 7, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 10, 20, 8, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 11, 5, 9, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 3
    # msg_id = booksim.IssueMessage(3, 12, 2, 10, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 13, 19, 11, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 14, 24, 12, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 15, 3, 13, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 4
    # msg_id = booksim.IssueMessage(3, 16, 6, 14, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 17, 23, 15, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 18, 28, 16, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 19, 13, 17, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 5
    # msg_id = booksim.IssueMessage(3, 20, 10, 18, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 21, 33, 19, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 22, 32, 20, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 23, 17, 21, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 6
    # msg_id = booksim.IssueMessage(3, 24, 14, 22, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 25, 31, 23, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 27, 15, 24, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 7
    # msg_id = booksim.IssueMessage(3, 28, 18, 25, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 29, 35, 26, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 30, 26, 27, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 31, 25, 28, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    #
    # # Node 8
    # msg_id = booksim.IssueMessage(3, 32, 22, 29, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 34, 30, 30, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    # msg_id = booksim.IssueMessage(3, 35, 29, 31, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    booksim = pybooksim.BookSim('{}/src/booksim3/runfiles/mesh/anynet_fatmesh_all_9_200.cfg'.format(os.environ['SIMHOME']))
    # Node 0
    msg_id = booksim.IssueMessage(3, 0, 9, 0, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, False)
    msg_id = booksim.IssueMessage(3, 1, 8, 1, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 2, 15, 2, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 3, 18, 3, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 1
    msg_id = booksim.IssueMessage(3, 5, 14, 4, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 6, 13, 5, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 7, 20, 6, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 8, 1, 7, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 9, 0, 8, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 2
    msg_id = booksim.IssueMessage(3, 11, 29, 9, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 12, 25, 10, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 13, 6, 11, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 14, 5, 12, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 3
    msg_id = booksim.IssueMessage(3, 15, 2, 13, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 16, 23, 14, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 17, 30, 15, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 18, 4, 16, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 19, 33, 17, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 4
    msg_id = booksim.IssueMessage(3, 20, 7, 18, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 21, 28, 19, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 22, 35, 20, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 23, 16, 21, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 5
    msg_id = booksim.IssueMessage(3, 25, 12, 22, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 26, 44, 23, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 27, 40, 24, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 28, 21, 25, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 29, 11, 26, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 6
    msg_id = booksim.IssueMessage(3, 30, 17, 27, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 31, 38, 28, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 32, 37, 29, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 33, 19, 30, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 7
    msg_id = booksim.IssueMessage(3, 35, 22, 31, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 36, 43, 32, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 37, 34, 33, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 38, 31, 34, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 39, 42, 35, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    # Node 8
    msg_id = booksim.IssueMessage(3, 40, 27, 36, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 41, 26, 37, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 42, 39, 38, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
    msg_id = booksim.IssueMessage(3, 43, 36, 39, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)

    for i in range(100000):
        booksim.SetSimTime(i+1)
        booksim.WakeUp()
        # booksim.SetSimTime(2)
        # booksim.WakeUp()

if __name__ == '__main__':
    main()


# class ProcessBookSim(SimObject):
#     def __init__(self, args, eventq):
#         super().__init__(eventq)
#         self.name = 'BookSimNI'
#         self.args = args
#         self.booksim = pybooksim.BookSim(args.booksim_config)
#         # self.local_eventq = EventQueue()
#         # self.in_message_buffers = None
#         # self.out_message_buffers = None
#         # self.reduce_scatter_time_track_dict = None
#         # self.all_gather_time_track_dict = None
#         # self.per_message_max_latency = None
#         # self.links_usage = None
#         # self.link_start_times = {}
#         # self.link_end_times = {}
#
#
#     '''
#     set_message_buffers() - set message buffers connected with HMCs
#     @in_message_buffers: message buffers for incoming messages
#     @out_message_buffers: message buffers for outgoing messages
#     '''
#     # def set_message_buffers(self, in_message_buffers, out_message_buffers):
#     #     self.in_message_buffers = in_message_buffers
#     #     self.out_message_buffers = out_message_buffers
#     # end of set_message_buffers
#
#     # def set_parameters(self, reduce_scatter_time_track_dict, all_gather_time_track_dict, per_message_max_latency, links_usage, link_start_times, link_end_times):
#     #     self.reduce_scatter_time_track_dict = reduce_scatter_time_track_dict
#     #     self.all_gather_time_track_dict = all_gather_time_track_dict
#     #     self.per_message_max_latency = per_message_max_latency
#     #     self.links_usage = links_usage
#     #     self.link_start_times = link_start_times
#     #     self.link_end_times = link_end_times
#
#
#     '''
#     schedule() - schedule the event at a given time
#     @event: the event to be scheduled
#     @cycle: scheduled time
#     '''
#     # def schedule(self, event, cycle):
#     #     self.global_eventq.schedule(self, cycle)
#     # end of schedule()
#
#
#     '''
#     process() - event processing function in a particular cycle
#     @cur_cycle: the current cycle that with events to be processed
#     '''
#     def process(self, cur_cycle):
#         msg_id = self.booksim.IssueMessage(0, 0, 1, 1, 8192, pybooksim.Message.ReduceData, pybooksim.Message.HeadTail, 0, True)
#         print(msg_id)
#     #     # send messages
#     #     for i in range(self.args.num_hmcs):
#     #         for j in range(self.args.radix):
#     #             message = self.in_message_buffers[i][j].peek(cur_cycle)
#     #             if message != None:
#     #                 src = message.src // self.args.radix
#     #                 src_ni = message.src % self.args.radix
#     #                 dest = message.dest // self.args.radix
#     #                 dest_ni = message.dest % self.args.radix
#     #                 assert src == i
#     #                 assert src_ni == j
#     #                 msg_id = self.booksim.IssueMessage(message.flow, message.src, message.dest, message.id, message.size, message.type, message.submsgtype, message.priority, message.end)
#     #                 if msg_id == -1:
#     #                     self.schedule(self, cur_cycle + 1)
#     #                     continue
#     #                 self.in_message_buffers[i][j].dequeue(cur_cycle)
#     #                 # total_in_flight_message = self.links_usage[src, dest][0]
#     #                 # total_unused_cycles = self.links_usage[src, dest][1]
#     #                 # last_used_cycle = self.links_usage[src, dest][2]
#     #                 # if total_in_flight_message == 0 and last_used_cycle != -1:
#     #                 #     total_unused_cycles += (cur_cycle - last_used_cycle - 1)
#     #                 # total_in_flight_message += 1
#     #                 # self.links_usage[src, dest] = (total_in_flight_message, total_unused_cycles, last_used_cycle)
#     #                 # print("Src " + str(src) + " Dest " + "Dest " + str(dest))
#     #                 if (src, dest) not in self.link_start_times.keys():
#     #                     self.link_start_times[src, dest] = []
#     #                 self.link_start_times[src, dest].append(cur_cycle)
#     #                 #print('{} | {} | issues a {} message for flow {} from HMC-{} (NI {}) to HMC-{} (NI {})'.format(cur_cycle, self.name, message.type, message.flow, src, src_ni, dest, dest_ni))
#     #
#     #     self.booksim.SetSimTime(cur_cycle)
#     #     self.booksim.WakeUp()
#     #
#     #     # peek and receive messages
#     #     for i in range(self.args.num_hmcs):
#     #         for j in range(self.args.radix):
#     #             dest_node = i * self.args.radix + j
#     #             flow, src_node, msgtype, end, priority = self.booksim.PeekMessage(dest_node, 0)
#     #             if src_node != -1:
#     #                 assert flow != -1
#     #                 src = src_node // self.args.radix
#     #                 src_ni = src_node % self.args.radix
#     #                 if self.out_message_buffers[i][j].is_full():
#     #                     continue
#     #                 message = Message(flow, None, src_node, dest_node, self.args.sub_message_size, msgtype, None, priority, end)
#     #                 self.out_message_buffers[i][j].enqueue(message, cur_cycle, 1)
#     #                 self.booksim.DequeueMessage(dest_node, 0)
#     #                 # total_in_flight_message = self.links_usage[src, i][0]
#     #                 # total_unused_cycles = self.links_usage[src, i][1]
#     #                 # last_used_cycle = self.links_usage[src, i][2]
#     #                 # assert total_in_flight_message > 0
#     #                 # total_in_flight_message -= 1
#     #                 # if total_in_flight_message == 0:
#     #                 #     last_used_cycle = cur_cycle
#     #                 # self.links_usage[src, i] = (total_in_flight_message, total_unused_cycles, last_used_cycle)
#     #                 if (src, i) not in self.link_end_times.keys():
#     #                     self.link_end_times[src, i] = []
#     #                 self.link_end_times[src, i].append(cur_cycle)
#     #                 #print('{} | {} | peek a {} message for flow {} to HMC-{} (NI {}) from HMC-{} (NI {})'.format(cur_cycle, self.name, msgtype, flow, i, j, src, src_ni))
#     #
#     #     if not self.booksim.Idle():
#     #         self.schedule(self, cur_cycle + 1)
#     # # end of process()
