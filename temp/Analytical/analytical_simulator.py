import argparse
import configparser as cp
import os
import sys
import math
import pickle

sys.path.append('{}/src/SCALE-Sim'.format(os.environ['SIMHOME']))
sys.path.append('{}/src/booksim2/src'.format(os.environ['SIMHOME']))
sys.path.append('{}/src/allreduce'.format(os.environ['SIMHOME']))

from model import Model


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--arch-config', default='{}/src/SCALE-Sim/configs/express.cfg'.format(os.environ['SIMHOME']),
                        help='accelerator architecture file, '
                             'default=SCALE-Sim/configs/express.cfg')
    parser.add_argument('--num-hmcs', default=256, type=int,
                        help='number of hybrid memory cubes, default=16')
    parser.add_argument('--num-vaults', default=16, type=int,
                        help='number of vaults per hybrid memory cube')
    parser.add_argument('--network', default='SCALE-Sim/topologies/conv_nets/alexnet.csv',
                        help='neural network architecture topology file, '
                             'default=SCALE-Sim/topologies/conv_nets/Googlenet.csv')
    # parser.add_argument('--radix', default=4, type=int,
    #                     help='node radix connected to router (end node NIs), default is 4')
    parser.add_argument('--anynet_bkp-file',
                        default='{}/src/booksim2/runfiles/hetero/anynet_bkp/3D_FC_Ring_SW_4_8_8_200_400_400.txt'.format(
                            os.environ['SIMHOME']), required=False,
                        help='required config file for booksim')
    parser.add_argument('--message-size', default=8480, type=int,
                        help='size of a message, default is 256 bytes, 0 means treat the whole chunk of gradients as a message')
    parser.add_argument('--synthetic-data-size', default=0, type=int,
                        help='synthetic data size in number of parameters, default is 0 (run model)')
    parser.add_argument('--flits-per-packet', default=16, type=int,
                        help='Number of payload flits per packet, packet header is not considered here, that will be added in booksim')
    parser.add_argument('--bandwidth_list', default="200_400_400",
                        help='Off chip latency across different dimensions')
    parser.add_argument('--multiplier-calculator', default='round',
                        help='network topology (floor|ceil|round), default is floor')
    parser.add_argument('--total-dimensions', default=3, type=int,
                        help='Total dimensions in the topology')
    parser.add_argument('--nodes-in-dimension-list', default="4_8_8",
                        help='Nodes in each dimension')
    parser.add_argument('--topology-in-dimension-list', default="FC_Ring_SW",
                        help='Nodes in each dimension')
    parser.add_argument('--tree-file', default='{}/src/SavedTrees_2/base-2-homogeneous-algo_heterogeneous-edge/multitree_heterogeneous_4_8_8_FC_Ring_SW_hiererchical_256_2_1_2'.format(os.environ['SIMHOME']), required=False,
                        help='Tree to load')

    args = parser.parse_args()
    if args.flits_per_packet != 16:
        raise RuntimeError('Warnings: Flits per packet is not 16, be cautious with floating point calculation')
    # args.bandwidths = [int(s) for s in args.bandwidth_list.split('_')]
    # args.nodes_in_dimension = [int(x) for x in args.nodes_in_dimension_list.split('_')]
    # args.topology_in_dimension = args.topology_in_dimension_list.split('_')
    # latency_list = []
    # for i in range(len(args.bandwidths)):
    #     computed_latency = math.ceil((args.message_size * 8 / args.flits_per_packet) / args.bandwidths[i])
    #     if args.topology_in_dimension[i] == 'SW':
    #         latency_list.append(2 * computed_latency)
    #     else:
    #         latency_list.append(computed_latency)
    #     # latency_list.append(math.ceil((args.message_size * 8 / args.flits_per_packet) / args.bandwidths[i]))
    # min_latency = min(latency_list)
    # args.per_message_time = min_latency * (args.flits_per_packet + 1)
    # latency_multiplier = []
    # for latency in latency_list:
    #     if args.multiplier_calculator == 'floor':
    #         latency_multiplier.append(math.floor(latency/min_latency))
    #     elif args.multiplier_calculator == 'ceil':
    #         latency_multiplier.append(math.ceil(latency/min_latency))
    #     elif args.multiplier_calculator == 'round':
    #         latency_multiplier.append(round(latency / min_latency))
    #     else:
    #         raise RuntimeError('Error: This latency multiplier is not implemented yet')
    # args.latency_multiplier = latency_multiplier
    # args.max_latency_multiplier = max(latency_multiplier)
    # args.max_latency = max(latency_list)

    config = cp.ConfigParser()
    config.read(args.arch_config)
    arch_sec = 'architecture_presets'

    args.pe_array_height = int(config.get(arch_sec, 'ArrayHeight'))
    args.pe_array_width = int(config.get(arch_sec, 'ArrayWidth'))

    args.ifmap_sram_size = int(config.get(arch_sec, 'IfmapSramSz')) << 10  # * 1024
    args.filter_sram_size = int(config.get(arch_sec, 'FilterSramSz')) << 10  # * 1024
    args.ofmap_sram_size = int(config.get(arch_sec, 'OfmapSramSz')) << 10  # * 1024

    args.ifmap_offset = int(config.get(arch_sec, 'IfmapOffset'))
    args.filter_offset = int(config.get(arch_sec, 'FilterOffset'))
    args.ofmap_offset = int(config.get(arch_sec, 'OfmapOffset'))
    args.ifmap_grad_offset = int(config.get(arch_sec, 'IfmapGradOffset'))
    args.filter_grad_offset = int(config.get(arch_sec, 'FilterGradOffset'))
    args.ofmap_grad_offset = int(config.get(arch_sec, 'OfmapGradOffset'))

    args.data_flow = config.get(arch_sec, 'Dataflow')

    # TODO: compute mode size based on model or synthetic data. Then calculate message size.
    args.only_allreduce = True
    model = Model(args)
    model_size = model.size
    # if args.synthetic_data_size > 0:
    #     data_size = args.synthetic_data_size
    # else:
    #     data_size = model_size
    base_num_messages = math.ceil(model_size * 4 / args.message_size / args.num_hmcs)

    # TODO: get the tree.
    # allreduce = construct_allreduce(args)
    # allreduce.compute_schedule(args.kary, verbose=args.verbose)
    save_object = pickle.load(open(args.tree_file, 'rb'))
    trees = save_object['tree']
    timesteps = save_object['timesteps']

    # TODO: get latency from booksim network file. compute overall message latencies.
    file1 = open(args.anynet_file, 'r')
    Lines = file1.readlines()
    distance_dict = {}
    for line in Lines:
        splitted_line = line.split()
        main_router = int(splitted_line[1])
        splitted_line.pop(0)
        splitted_line.pop(0)
        while splitted_line[0] == 'node':
            splitted_line.pop(0)
            splitted_line.pop(0)
        while len(splitted_line) > 0 and splitted_line[0] == 'router':
            splitted_line.pop(0)
            connected_router = int(splitted_line.pop(0))
            distance = int(splitted_line.pop(0))
            distance_dict[main_router, connected_router] = distance
    # TODO: Finally compute comm time based on tree length. Compute a rough approximation of reduction time.

    tree_0 = trees[0]
    activation_time = {}
    activation_time[0] = 0
    activation_timestep = {}
    activation_timestep[0] = 0
    max_time = 0
    for link in tree_0:
        child, parent, timestep, dist, _ = link
        message_time = base_num_messages * args.flits_per_packet * distance_dict[child, parent] + 10
        message_time_multiplier = math.floor((timestep - activation_timestep[parent]) / dist)
        # if message_time_multiplier - int(message_time_multiplier) != 0:
        #     raise Exception("message time multiplier should be integer")
        new_time = activation_time[parent] + message_time * (message_time_multiplier + 1)
        activation_time[child] = new_time
        activation_timestep[child] = timestep + dist
        if new_time > max_time:
            max_time = new_time

    total_time = 2 * max_time
    print(total_time)
    print("Done")


if __name__ == '__main__':
    main()
