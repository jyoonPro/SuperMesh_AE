import argparse
import configparser as cp
import json
import logging
import math
import os
import pickle
import sys
import time

from allreduce.Alternative_2D_ring_allreduce import Alternative2dRingAllreduce
from allreduce.teccl_allreduce import TecclAllreduce

sys.path.append('{}/src/SCALE-Sim'.format(os.environ['SIMHOME']))
sys.path.append('{}/src/booksim2/src'.format(os.environ['SIMHOME']))
sys.path.append('{}/src/allreduce'.format(os.environ['SIMHOME']))

from booksim import BookSim
from eventq import EventQueue
from hmc import HMC
from message_buffer import MessageBuffer
from model import Model
from allreduce.supermesh_pipeline_trees import SuperMeshPipelineTrees
from allreduce.tto_pipeline_trees import TTOPipelineTrees
from allreduce.multitree_allreduce import MultiTreeAllreduce
from allreduce.tacos_allreduce import TacosAllreduce
from allreduce.network.kncube import KNCube
from allreduce.network.kite_small import Kite
from allreduce.network.d_butterfly import DButterfly
from allreduce.network.cmesh import Cmesh
from allreduce.network.kite_medium import KiteMedium
from allreduce.network.folded_torus import FoldedTorus

logger = logging.getLogger(__name__)

'''
construct_network() - construct a network
@args: argumetns of the top simulation

return: a network object
'''
def construct_network(args):
    args.nodes = args.num_hmcs

    if (args.booksim_network == 'mesh' or args.booksim_network == 'SM_Bi'
            or args.booksim_network == 'SM_Alter' or args.booksim_network == 'SM_Uni'
            or args.booksim_network == 'Partial_SM_Bi' or args.booksim_network == 'Partial_SM_Alter'):
        network = KNCube(args, mesh=True)
    elif args.booksim_network == 'torus':
        network = KNCube(args)
    elif args.booksim_network == 'kite':
        network = Kite(args)
    elif args.booksim_network == 'dbutterfly':
        network = DButterfly(args)
    elif args.booksim_network == 'cmesh':
        network = Cmesh(args)
    elif args.booksim_network == 'kite_medium':
        network = KiteMedium(args)
    elif args.booksim_network == 'folded_torus':
        network = FoldedTorus(args)
    else:
        raise RuntimeError('Unknown network topology: ' + args.booksim_network)

    network.build_graph()
    network.nodes = args.num_hmcs

    return network

'''
construct_allreduce() - construct an allreduce schedule
@args: arguments of the top simulation

return: an allreduce object
'''
def construct_allreduce(args):
    args.nodes = args.num_hmcs
    network = construct_network(args)

    if args.allreduce == 'pipeline' and args.booksim_network == 'mesh':
        allreduce = TTOPipelineTrees(args, network)
    elif args.allreduce == 'pipeline':
        allreduce = SuperMeshPipelineTrees(args, network)
    elif args.allreduce == 'multitree':
        allreduce = MultiTreeAllreduce(args, network)
    elif args.allreduce == 'tacos':
        allreduce = TacosAllreduce(args, network)
    elif args.allreduce == 'teccl':
        allreduce = TecclAllreduce(args, network)
    elif args.allreduce == 'alternate_2d_ring':
        allreduce = Alternative2dRingAllreduce(args, network)
    else:
        raise RuntimeError('Unknown allreduce schedule: ' + args.allreduce)

    return allreduce

def add_scalesim_config(args):
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

    logger.info("====================================================")
    logger.info("******************* SCALE SIM **********************")
    logger.info("====================================================")
    logger.info("Array Size:    {} x {}".format(args.pe_array_height, args.pe_array_width))
    logger.info("SRAM IFMAP:    {}".format(args.ifmap_sram_size))
    logger.info("SRAM Filter:   {}".format(args.filter_sram_size))
    logger.info("SRAM OFMAP:    {}".format(args.ofmap_sram_size))
    logger.info("CSV file path: {}".format(args.network))
    logger.info("Dataflow:      {}".format(args.data_flow))
    logger.info("====================================================\n")

def get_other_sets_4(args):
    matrix = []
    for i in range(args.per_dim_nodes):
        sub_matrix = []
        for j in range(args.per_dim_nodes):
            sub_matrix.append(i * args.per_dim_nodes + j)
        matrix.append(sub_matrix)

    other_sets = []
    remainings = list(range(args.num_hmcs))
    for i in range(int(args.per_dim_nodes/2)):
        nodes_1 = matrix[i][i:args.per_dim_nodes-1-i]
        nodes_2 = []
        for j in range(i, args.per_dim_nodes-1-i):
            nodes_2.append(matrix[j][args.per_dim_nodes-1-i])
        nodes_3 = matrix[args.per_dim_nodes-1-i][i+1:args.per_dim_nodes-i]
        nodes_3.reverse()
        nodes_4 = []
        for j in reversed(range(i+1,args.per_dim_nodes-i)):
            nodes_4.append(matrix[j][i])
        for j in range(len(nodes_1)):
            other_sets.append([nodes_1[j], nodes_2[j], nodes_3[j], nodes_4[j]])
            remainings.remove(nodes_1[j])
            remainings.remove(nodes_2[j])
            remainings.remove(nodes_3[j])
            remainings.remove(nodes_4[j])

    other_sets.pop(0)
    multitree_set = None
    if len(remainings) > 0:
        # multitree_set = other_sets.pop()
        # multitree_set.extend(remainings)
        other_sets.append(remainings)
    return other_sets, multitree_set

def get_other_sets_3(args):
    matrix = []
    for i in range(args.per_dim_nodes):
        sub_matrix = []
        for j in range(args.per_dim_nodes):
            sub_matrix.append(i * args.per_dim_nodes + j)
        matrix.append(sub_matrix)

    corner_set = [0, args.per_dim_nodes - 1, args.num_hmcs - 1, args.per_dim_nodes * (args.per_dim_nodes - 1)]
    other_sets = []
    remainings = list(range(args.num_hmcs))
    remainings.remove(0)
    remainings.remove(args.per_dim_nodes - 1)
    remainings.remove(args.num_hmcs - 1)
    remainings.remove(args.per_dim_nodes * (args.per_dim_nodes - 1))
    other_set = []
    for i in range(int(args.per_dim_nodes/2)):
        nodes_1 = matrix[i][i:args.per_dim_nodes-1-i]
        nodes_2 = []
        for j in range(i, args.per_dim_nodes-1-i):
            nodes_2.append(matrix[j][args.per_dim_nodes-1-i])
        nodes_3 = matrix[args.per_dim_nodes-1-i][i+1:args.per_dim_nodes-i]
        nodes_3.reverse()
        nodes_4 = []
        for j in reversed(range(i+1,args.per_dim_nodes-i)):
            nodes_4.append(matrix[j][i])
        nodes_1 = [item for item in nodes_1 if item not in corner_set]
        nodes_2 = [item for item in nodes_2 if item not in corner_set]
        nodes_3 = [item for item in nodes_3 if item not in corner_set]
        nodes_4 = [item for item in nodes_4 if item not in corner_set]

        count = 0
        while len(nodes_1) > 0 or len(nodes_2) > 0 or len(nodes_3) > 0 or len(nodes_4) > 0:
            node = None
            if count % 4 == 0 and len(nodes_1) > 0:
                node = nodes_1.pop(0)
            elif count % 4 == 1 and len(nodes_2) > 0:
                node = nodes_2.pop(0)
            elif count % 4 == 2 and len(nodes_3) > 0:
                node = nodes_3.pop(0)
            elif count % 4 == 3 and len(nodes_4) > 0:
                node = nodes_4.pop(0)
            other_set.append(node)
            remainings.remove(node)
            if len(other_set) == 3:
                other_sets.append(other_set)
                other_set = []
            count += 1

    other_set.extend(remainings)
    multitree_set = None
    # if len(other_set) == 3:
    other_sets.append(other_set)
        # multitree_set = None
    # elif len(other_set) == 1 or len(other_set) == 2:
    #     multitree_set = other_sets.pop()
    #     multitree_set.extend(other_set)
    # if len(multitree_set) == 0:
    #     multitree_set = None

    # if len(remainings) > 0:
    #     multitree_set = other_sets.pop()
    #     multitree_set.extend(remainings)
    return other_sets, multitree_set

def get_other_sets_3_partial(args):
    matrix = []
    for i in range(args.per_dim_nodes):
        sub_matrix = []
        for j in range(args.per_dim_nodes):
            sub_matrix.append(i * args.per_dim_nodes + j)
        matrix.append(sub_matrix)

    corner_set = [0, args.per_dim_nodes - 1, args.num_hmcs - 1, args.per_dim_nodes * (args.per_dim_nodes - 1)]
    other_sets = []
    remainings = list(range(args.num_hmcs))
    remainings.remove(0)
    remainings.remove(args.per_dim_nodes - 1)
    remainings.remove(args.num_hmcs - 1)
    remainings.remove(args.per_dim_nodes * (args.per_dim_nodes - 1))
    other_set = []
    for i in range(int(args.per_dim_nodes/2)):
        nodes_1 = matrix[i][i:args.per_dim_nodes-1-i]
        nodes_2 = []
        for j in range(i, args.per_dim_nodes-1-i):
            nodes_2.append(matrix[j][args.per_dim_nodes-1-i])
        nodes_3 = matrix[args.per_dim_nodes-1-i][i+1:args.per_dim_nodes-i]
        nodes_3.reverse()
        nodes_4 = []
        for j in reversed(range(i+1,args.per_dim_nodes-i)):
            nodes_4.append(matrix[j][i])
        nodes_1 = [item for item in nodes_1 if item not in corner_set]
        nodes_2 = [item for item in nodes_2 if item not in corner_set]
        nodes_3 = [item for item in nodes_3 if item not in corner_set]
        nodes_4 = [item for item in nodes_4 if item not in corner_set]

        count = 0
        while len(nodes_1) > 0 or len(nodes_2) > 0 or len(nodes_3) > 0 or len(nodes_4) > 0:
            node = None
            if count % 4 == 0 and len(nodes_1) > 0:
                node = nodes_1.pop(0)
            elif count % 4 == 1 and len(nodes_2) > 0:
                node = nodes_2.pop(0)
            elif count % 4 == 2 and len(nodes_3) > 0:
                node = nodes_3.pop(0)
            elif count % 4 == 3 and len(nodes_4) > 0:
                node = nodes_4.pop(0)
            other_set.append(node)
            remainings.remove(node)
            if len(other_set) == 3:
                other_sets.append(other_set)
                other_set = []
            count += 1

    remainings.append(args.per_dim_nodes * (args.per_dim_nodes - 1))
    other_set.extend(remainings)
    multitree_set = None
    # if len(other_set) == 3:
    other_sets.append(other_set)
        # multitree_set = None
    # elif len(other_set) == 1 or len(other_set) == 2:
    #     multitree_set = other_sets.pop()
    #     multitree_set.extend(other_set)
    # if len(multitree_set) == 0:
    #     multitree_set = None

    # if len(remainings) > 0:
    #     multitree_set = other_sets.pop()
    #     multitree_set.extend(remainings)
    return other_sets, multitree_set

def get_analytical_cycle_number(args, allreduce):
    if args.booksim_network == 'mesh':
        if args.allreduce == 'mesh_overlap_2d_1':
            if args.collective == 'AR':
                return (args.total_partial_trees + allreduce.max_tree_height_for_pipeline - 1) * args.message_per_chunk * args.per_message_time * 2
            else:
                raise Exception("Only allreduce supports")
        elif args.allreduce == 'multitree':
            if args.collective == 'AR':
                return args.multitree_total_message * allreduce.timesteps * args.per_message_time * 2
            elif args.collective == 'RS' or args.collective == 'AG':
                return args.multitree_total_message * allreduce.timesteps * args.per_message_time
            else:
                raise Exception("Only allreduce and RS/AG supports")
    elif args.booksim_network == 'SM_Bi' or args.booksim_network == 'SM_Uni'  or args.booksim_network == 'SM_Alter':
        if args.allreduce == 'SM_Bi' or args.allreduce == 'SM_Uni':
            if args.collective == 'AR':
                return (args.total_partial_trees + allreduce.max_tree_height_for_pipeline - 1) * args.message_per_chunk * args.per_message_time * 2
            elif args.collective == 'RS' or args.collective == 'AG':
                return args.total_sets * (args.total_partial_trees + allreduce.max_tree_height_for_pipeline - 1) * args.message_per_chunk * args.per_message_time
            else:
                raise Exception("Only allreduce and RS/AG supports")
        elif args.allreduce == 'multitree':
            if args.collective == 'AR':
                return args.multitree_total_message * allreduce.timesteps * args.per_message_time * 2
            elif args.collective == 'RS' or args.collective == 'AG':
                return args.multitree_total_message * allreduce.timesteps * args.per_message_time
            else:
                raise Exception("Only allreduce and RS/AG supports")

def main():
    start_time = time.time()
    parser = argparse.ArgumentParser()

    parser.add_argument('--arch-config', default='{}/src/SCALE-Sim/configs/express_128.cfg'.format(os.environ['SIMHOME']),
                        help='accelerator architecture file, '
                             'default=SCALE-Sim/configs/express_64.cfg')
    parser.add_argument('--num-hmcs', default=256, type=int,
                        help='number of hybrid memory cubes, default=16')
    parser.add_argument('--num-vaults', default=1, type=int,
                        help='number of vaults per hybrid memory cube')
    parser.add_argument('--mini-batch-size', default=16, type=int,
                        help='number of mini batch size for all hmc accelerator, distributed to all vault npu of each accelerator')
    parser.add_argument('--network', default='SCALE-Sim/topologies/mlperf/AlphaGoZero.csv',
                        help='neural network architecture topology file')
    parser.add_argument('--run-name', default='bb',
                        help='naming for this experiment run, default is empty')
    parser.add_argument('-d', '--outdir', default='{}/results/mesh_logs'.format(os.environ['SIMHOME']),
                        help='naming for the output directory, default is empty')
    parser.add_argument('--booksim-network', default='mesh',
                        help='network topology (torus|mesh|SM_Bi|SM_Alter|SM_Uni), default is torus')
    parser.add_argument('--booksim-config',
                        default='{}/src/booksim2/runfiles/mesh/anynet_mesh_36_200.cfg'.format(os.environ['SIMHOME']),
                        required=False, help='required config file for booksim')
    parser.add_argument('--allreduce', default='tacos',
                        help='allreduce shedule (multitree|pipeline|tacos|taccl|teccl|alternate_2d_ring), default=multitree')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='Set the log level to debug, printing out detailed messages during execution.')
    parser.add_argument('--collective', default='AG',
                        help='Collective type(Compute|AR|RS|AG), default=AG')
    parser.add_argument('--message-buffer-size', default=32, type=int,
                        help='message buffer size, default is 0 (infinite)')
    parser.add_argument('--message-size', default=4096, type=int,
                        help='size of a message, default is 256 bytes, 0 means treat the whole chunk of gradients as a message')
    parser.add_argument('--synthetic-data-size', default=262144, type=int,
                        help='synthetic data size in number of parameters, default is 0 (run model)')
    parser.add_argument('--bandwidth', default=100, type=int,
                        help='On chip BW between chiplets')
    parser.add_argument('--load-tree', default=False, action='store_true',
                        help='Whether just build tree or run full simulation')
    parser.add_argument('--only-save-tree', default=False, action='store_true',
                        help='Whether just build tree or run full simulation')
    parser.add_argument('--messages-per-chunk', default=3, type=int, help='Number of messages per chunk')
    parser.add_argument('--save-link-utilization', default=False, action='store_true',
                        help='Save link utilization info')
    parser.add_argument('--analytical', default=False, action='store_true',
                        help='Save link utilization info')

    args = parser.parse_args()

    # Initialize some more parameters
    args.per_dim_nodes = int(math.sqrt(args.num_hmcs))
    assert args.num_hmcs == args.per_dim_nodes * args.per_dim_nodes
    # Each packet contains 16 body flits and one header flit.
    args.flits_per_packet = 17
    # For SM_Bi, radix should be 5, for other cases it should be 4
    # if args.allreduce == 'tacos' or args.allreduce == 'teccl':
    #     # For tacos and teccl topology, we halved the latency instead of adding extra link. So, radix is always 4.
    #     args.radix = 4
    # else:
    if args.booksim_network == 'SM_Bi' or args.booksim_network == 'Partial_SM_Bi':
        args.radix = 5
    elif args.booksim_network == 'SM_Alter' and args.per_dim_nodes % 2 != 0:
        args.radix = 5
    else:
        args.radix = 4

    # Both save tree and load tree can't be run simultaneously. We want to save first and then for other runs we want to load them.
    assert not (args.only_save_tree and args.load_tree)

    args.latency = math.ceil((args.message_size * 8 / args.flits_per_packet) / args.bandwidth)
    args.per_message_time = args.latency * (args.flits_per_packet + 1)

    # if args.outdir:
    #     args.logdir = args.outdir
    # else:
    #     logpath = '{}/results/logs'.format(os.environ['SIMHOME'])
    #     args.logdir = logpath
    # os.system('mkdir -p {}'.format(args.outdir))
    # args.outdir = '{}/outputs/{}'.format(args.outdir, args.run_name)

    if not args.outdir:
        args.outdir = '{}/results/logs'.format(os.environ['SIMHOME'])
    logfile_path = args.outdir + '/logs'
    jsonfile_path = args.outdir + '/json'
    utilization_path = args.outdir + '/utilization'
    os.system('mkdir -p {}'.format(logfile_path))
    os.system('mkdir -p {}'.format(jsonfile_path))
    os.system('mkdir -p {}'.format(utilization_path))

    net_name = args.network.split('/')[-1].split('.')[0]
    config_name = args.arch_config.split('/')[-1].split('.')[0]

    args.extension = args.collective

    logfile = '{}/{}_{}_{}_{}_{}_{}_{}.log'.format(logfile_path, args.run_name, args.allreduce, args.num_hmcs,
                                                   args.booksim_network, net_name, config_name, args.extension)
    jsonfile_name = '{}/{}_{}_{}_{}_{}_{}_{}.json'.format(jsonfile_path, args.run_name, args.allreduce, args.num_hmcs,
                                                     args.booksim_network, net_name, config_name, args.extension)
    link_utilization_file = '{}/{}_{}_{}_{}_{}.pkl'.format(utilization_path, args.run_name, args.allreduce, args.num_hmcs,
                                                           args.booksim_network, args.extension)

    # Add ScaleSim Config
    add_scalesim_config(args)

    global_eventq = EventQueue()
    # Initialize model or synthetic data size
    model = Model(args)

    if args.verbose:
        logging.basicConfig(filename=logfile, format='%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(filename=logfile, format='%(message)s', level=logging.INFO)

    logger.info('NN model size: {} parameters'.format(model.size))
    # TODO: Refactor this part

    if args.allreduce == 'pipeline':
        args.total_partial_trees = None
        args.corner_partial_trees = None
        args.other_partial_trees = None
        args.corner_set = None
        args.other_pipeline_sets = None
        args.remaining_multitree_set = None
        # Here chunk size is in bytes. 3 is because we have 3 parallel disjoint trees.
        three_tree_chunk_size = math.ceil((args.message_size * args.messages_per_chunk * 3))
        # Here chunk size is in bytes. 4 is because we have 4 parallel disjoint trees.
        four_tree_chunk_size = math.ceil((args.message_size * args.messages_per_chunk * 4))

        if args.booksim_network == 'mesh':
            args.corner_set = [0, args.per_dim_nodes - 1, args.num_hmcs - 1]
        elif args.booksim_network == 'SM_Bi':
            args.corner_set = [0, args.per_dim_nodes - 1, args.num_hmcs - 1,
                               args.per_dim_nodes * (args.per_dim_nodes - 1)]
            args.other_pipeline_sets, args.remaining_multitree_set = get_other_sets_4(args)
        elif args.booksim_network == 'SM_Alter':
            args.corner_set = [0, args.per_dim_nodes - 1, args.num_hmcs - 1,
                               args.per_dim_nodes * (args.per_dim_nodes - 1)]
            if args.per_dim_nodes % 2 == 0:
                args.other_pipeline_sets, args.remaining_multitree_set = get_other_sets_4(args)
            else:
                args.other_pipeline_sets, args.remaining_multitree_set = get_other_sets_3(args)
        elif args.booksim_network == 'SM_Uni':
            args.corner_set = [0, args.per_dim_nodes - 1, args.num_hmcs - 1,
                               args.per_dim_nodes * (args.per_dim_nodes - 1)]
            args.other_pipeline_sets, args.remaining_multitree_set = get_other_sets_3(args)
        elif args.booksim_network == 'Partial_SM_Bi' or args.booksim_network == 'Partial_SM_Alter':
            args.corner_set = [0, args.per_dim_nodes - 1, args.num_hmcs - 1]
            args.other_pipeline_sets, args.remaining_multitree_set = get_other_sets_3_partial(args)

        # args.total_sets_str = []
        # args.corner_sets_str = []
        # args.other_pipeline_sets_str = []
        # args.remaining_multitree_set_str = []
        # args.total_sets_str.append('_'.join(map(str, args.corner_set)))
        # args.corner_sets_str.append('_'.join(map(str, args.corner_set)))
        # for tree_roots in args.other_pipeline_sets:
        #     args.total_sets_str.append('_'.join(map(str, tree_roots)))
        #     args.other_pipeline_sets_str.append('_'.join(map(str, tree_roots)))
        # if args.remaining_multitree_set is not None:
        #     args.total_sets_str.append('_'.join(map(str, args.remaining_multitree_set)))
        #     args.remaining_multitree_set_str.append('_'.join(map(str, args.remaining_multitree_set)))

        if args.collective == 'AR':
            if args.booksim_network == 'mesh' or args.booksim_network == 'Partial_SM_Bi' or args.booksim_network == 'Partial_SM_Alter':
                # Here 4 is because each parameter is 4 bytes. For allreduce, TTO makes 3 disjoint trees
                args.total_partial_trees = math.ceil((model.size * 4) / three_tree_chunk_size)
            else:
                # Here 4 is because each parameter is 4 bytes. For allreduce, all SM topologies can make 4 disjoint trees
                args.total_partial_trees = math.ceil((model.size * 4) / four_tree_chunk_size)
            args.multitree_message_for_pipeline = 0
        elif args.collective == 'RS' or args.collective == 'AG':
            if args.booksim_network == 'SM_Bi':
                # For corner trees, we can always make 4 trees
                args.corner_partial_trees = math.ceil(
                    (model.size * 4 * len(args.corner_set)) / (args.num_hmcs * four_tree_chunk_size))
                # For other trees in SM_Bi, we can make 4 disjoint trees at a time as well
                # if args.per_dim_nodes != 3:
                args.other_partial_trees = math.ceil(
                        (model.size * 4 * len(args.other_pipeline_sets[0])) / (args.num_hmcs * four_tree_chunk_size))
                args.multitree_message_for_pipeline = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)
            elif args.booksim_network == 'SM_Alter':
                # For corner trees, we can always make 4 trees
                args.corner_partial_trees = math.ceil(
                    (model.size * 4 * len(args.corner_set)) / (args.num_hmcs * four_tree_chunk_size))
                args.multitree_message_for_pipeline = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)
                # if args.per_dim_nodes != 3:
                if args.per_dim_nodes % 2 == 0:
                    # For other trees in SM_Alter_Even, we can make 4 disjoint trees at a time as well
                    args.other_partial_trees = math.ceil(
                        (model.size * 4 * len(args.other_pipeline_sets[0])) / (args.num_hmcs * four_tree_chunk_size))
                else:
                    # For other trees in SM_Alter_Odd, we can make 3 disjoint trees at a time as well
                    args.other_partial_trees = math.ceil(
                        (model.size * 4 * len(args.other_pipeline_sets[0])) / (args.num_hmcs * three_tree_chunk_size))
            elif args.booksim_network == 'SM_Uni':
                # For corner trees, we can always make 4 trees
                args.corner_partial_trees = math.ceil(
                    (model.size * 4 * len(args.corner_set)) / (args.num_hmcs * four_tree_chunk_size))
                # For other trees in SM_Uni, we can make 3 disjoint trees at a time as well
                # if args.per_dim_nodes != 3:
                args.other_partial_trees = math.ceil(
                        (model.size * 4 * len(args.other_pipeline_sets[0])) / (args.num_hmcs * three_tree_chunk_size))
                args.multitree_message_for_pipeline = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)
            elif args.booksim_network == 'Partial_SM_Bi' or args.booksim_network == 'Partial_SM_Alter':
                # This is a test case, for senstivity test. We only test this for 16 node case.
                # For corner trees, we can always make 3 trees
                args.corner_partial_trees = math.ceil(
                    (model.size * 4 * len(args.corner_set)) / (args.num_hmcs * three_tree_chunk_size))
                # For other trees in SM_Uni, we can make 3 disjoint trees at a time as well
                # if args.per_dim_nodes != 3:
                args.other_partial_trees = math.ceil(
                    (model.size * 4 * len(args.other_pipeline_sets[0])) / (args.num_hmcs * three_tree_chunk_size))
                args.multitree_message_for_pipeline = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)

        if args.collective != "Compute":
            logger.info('Three Tree Chunk Size {}'.format(three_tree_chunk_size))
            logger.info('Four Tree Chunk Size {}'.format(four_tree_chunk_size))
            logger.info('Total partial trees {}'.format(args.total_partial_trees))
            logger.info('Corner partial trees {}'.format(args.corner_partial_trees))
            logger.info('Other partial trees {}'.format(args.other_partial_trees))
            logger.info('Multitree messages for pipeline {}'.format(args.multitree_message_for_pipeline))
            logger.info('Corner set {}'.format(args.corner_set))
            logger.info('Other pipelining set {}'.format(args.other_pipeline_sets))
            logger.info('Remaining multitree set {}'.format(args.remaining_multitree_set))
            logger.info('Messages in each chunk {}'.format(args.messages_per_chunk))
    elif args.allreduce == 'multitree':
        args.multitree_total_message = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)
        logger.info('Message in each timestep {}'.format(args.multitree_total_message))
    elif args.allreduce == 'tacos':
        args.tacos_total_message = math.ceil(model.size * 4 / args.message_size / args.num_hmcs / 4) # We make 4 chunks to per node data
        logger.info('Message in each timestep {}'.format(args.tacos_total_message))
    elif args.allreduce == 'taccl':
        args.taccl_total_message = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)
        logger.info('Message in each timestep {}'.format(args.taccl_total_message))
    elif args.allreduce == 'teccl':
        args.teccl_total_message = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)
        logger.info('Message in each timestep {}'.format(args.teccl_total_message))
    elif args.allreduce == 'alternate_2d_ring':
        assert args.per_dim_nodes % 2 == 0
        args.alternate_2d_first_dim_messages = math.ceil(model.size * 4 / args.message_size / (2 * args.per_dim_nodes))
        args.alternate_2d_second_dim_messages = math.ceil(model.size * 4 / args.message_size / args.num_hmcs)
        logger.info('Message in each timestep alternate 2d first dim {}'.format(args.alternate_2d_first_dim_messages))
        logger.info('Message in each timestep alternate 2d second dim {}'.format(args.alternate_2d_second_dim_messages))

    network = BookSim(args, global_eventq)
    allreduce = construct_allreduce(args)
    allreduce.build_trees(verbose=args.verbose)
    if args.only_save_tree:
        return
    allreduce.compute_schedule(verbose=args.verbose)

    # TODO: Figure  out whether everything is required or not
    link_dict = {}
    messages_sent = {}
    sending = {}
    temp_radix = args.radix
    available_nis_src = {}
    available_nis_dest = {}
    ni_packets = {}
    if args.booksim_network == 'SM_Alter' and args.per_dim_nodes % 2 != 0:
        temp_radix = 5
    for i in range(args.num_hmcs):
        messages_sent[i] = [0] * temp_radix
        sending[i] = [None for j in range(temp_radix)]
        link_dict[i] = {}
        available_nis_src[i] = [0] * args.radix
        available_nis_dest[i] = [0] * args.radix
        ni_packets[i] = {}
        for j in range(args.radix):
            ni_packets[i][j] = []
        for key in allreduce.reduce_scatter_schedule[i].keys():
            link_dict[i][key] = False
        for key in allreduce.all_gather_schedule[i].keys():
            if key not in link_dict[i]:
                link_dict[i][key] = False
    allreduce.link_dict = link_dict
    allreduce.messages_sent = messages_sent
    allreduce.sending = sending
    allreduce.available_nis_src = available_nis_src
    allreduce.available_nis_dest = available_nis_dest
    allreduce.ni_packets = ni_packets

    # TODO: Figure out whether everything is required or not
    optimal_messages_sent = []
    optimal_sending = []
    optimal_free_nis = []
    for i in range(args.num_hmcs):
        optimal_messages_sent.append([0] * temp_radix)
        optimal_sending.append([None for i in range(temp_radix)])
        optimal_free_nis.append(set([i for i in range(temp_radix)]))

    hmcs = []
    from_network_message_buffers = []
    to_network_message_buffers = []
    for i in range(args.num_hmcs):
        hmcs.append(HMC(i, args, global_eventq))
        hmcs[i].load_model(model)
        hmcs[i].startup()
        from_network_message_buffers.append([])
        to_network_message_buffers.append([])
        for j in range(temp_radix):
            from_network_message_buffers[i].append(
                MessageBuffer('from_network_node{}_ni{}'.format(i, j), args.message_buffer_size))
            to_network_message_buffers[i].append(
                MessageBuffer('to_network_node{}_ni{}'.format(i, j), args.message_buffer_size))
            from_network_message_buffers[i][j].set_consumer(hmcs[i])
            to_network_message_buffers[i][j].set_consumer(network)
        hmcs[i].set_message_buffers(from_network_message_buffers[i],
                                    to_network_message_buffers[i])
        hmcs[i].set_allreduce(allreduce)

    network.set_message_buffers(to_network_message_buffers, from_network_message_buffers)
    start_time = time.time()
    while not global_eventq.empty():
        cur_cycle, events = global_eventq.next_events()

        for event in events:
            event.process(cur_cycle)
    end_time = time.time()
    time_difference = end_time - start_time
    print(f"Time taken: {time_difference:.2f} seconds")

    # TODO: Clean this code
    assert network.booksim.Idle()
    for i, hmc in enumerate(hmcs):
        if args.collective == 'RS':
            all_rs_done = True
            for key in hmc.link_dict[hmc.id].keys():
                if key in hmc.reduce_scatter_schedule and len(hmc.reduce_scatter_schedule[key]) > 0:
                    all_rs_done = False
                    break
            assert all_rs_done is True
        elif args.collective == 'AG':
            all_ag_done = True
            for key in hmc.link_dict[hmc.id].keys():
                if key in hmc.all_gather_schedule and len(hmc.all_gather_schedule[key]) > 0:
                    all_ag_done = False
                    break
            assert all_ag_done is True
        elif not args.collective == 'Compute':
            assert len(hmc.pending_aggregations) == 0
            all_ag_done = True
            for key in hmc.link_dict[hmc.id].keys():
                if key in hmc.all_gather_schedule and len(hmc.all_gather_schedule[key]) > 0:
                    all_ag_done = False
                    break
            assert all_ag_done is True
            all_rs_done = True
            for key in hmc.link_dict[hmc.id].keys():
                if key in hmc.reduce_scatter_schedule and len(hmc.reduce_scatter_schedule[key]) > 0:
                    all_rs_done = False
                    break
            assert all_rs_done is True
        for i, message_buffer in enumerate(hmc.from_network_message_buffers):
            assert message_buffer.size == 0
        for i, message_buffer in enumerate(hmc.to_network_message_buffers):
            assert message_buffer.size == 0

    # TODO: Change the code so that we can simulate multiple cycles in the booksim at a time.
    logger.debug('booksim network idle? {}'.format(network.booksim.Idle()))
    for i, hmc in enumerate(hmcs):
        logger.debug('HMC {}:'.format(i))
        logger.debug('   reduce-scatter-schedule:')
        for schedule in hmc.reduce_scatter_schedule:
            logger.debug('       {}'.format(schedule))
        logger.debug('   all-gather-schedule:')
        for schedule in hmc.all_gather_schedule:
            logger.debug('       {}'.format(schedule))
        logger.debug('   from network message buffers:')
        for i, message_buffer in enumerate(hmc.from_network_message_buffers):
            logger.debug('       {}-{}: has {} messages'.format(i, message_buffer.name, message_buffer.size))
        logger.debug('   to network message buffers:')
        for i, message_buffer in enumerate(hmc.to_network_message_buffers):
            logger.debug('       {}-{}: has {} messages'.format(i, message_buffer.name, message_buffer.size))

    compute_cycles = hmcs[0].compute_cycles
    cycles = global_eventq.cycles
    allreduce_cycles = cycles - compute_cycles

    if args.collective != 'Compute':
        reduce_scatter_time = 0
        for i, hmc in enumerate(hmcs):
            reduce_scatter_time = max(reduce_scatter_time, hmc.reduce_scatter_done)
        if args.collective != 'RS':
            total_allgather_packets = 0
            total_allgather_waiting_cycles = 0
            total_allgather_waiting_cycles_before = 0
            for hmc in hmcs:
                total_allgather_packets += hmc.all_gather_packets
                total_allgather_waiting_cycles += hmc.all_gather_waiting_time
                total_allgather_waiting_cycles_before += hmc.all_gather_waiting_time_before
            average_allgather_waiting_cycles = int(total_allgather_waiting_cycles / total_allgather_packets)
            average_allgather_waiting_cycles_before = int(total_allgather_waiting_cycles_before / total_allgather_packets)
            average_allgather_waiting_cycles_total = int((total_allgather_waiting_cycles_before + total_allgather_waiting_cycles) / total_allgather_packets)

    compute_percentile = compute_cycles / cycles * 100
    allreduce_percentile = allreduce_cycles / cycles * 100
    if args.save_link_utilization:
        save_object = {}
        save_object['link_start_time'] = network.link_start_times
        save_object['link_end_time'] = network.link_end_times
        save_object['total_time'] = cycles
        save_object['total_links'] = allreduce.network.total_possible_links
        pickle.dump(save_object, open(link_utilization_file, "wb"))

    logger.info('\n======== Simulation Summary ========')
    logger.info('Training epoch runtime: {} cycles'.format(cycles))
    logger.info(' - computation: {} cycles ({:.2f}%)'.format(compute_cycles, compute_percentile))
    logger.info(' - allreduce: {} cycles ({:.2f}%)'.format(allreduce_cycles, allreduce_percentile))
    total_messages_sent = 0
    for i, hmc in enumerate(hmcs):
        logger.debug(' - HMC {} sends {} messages'.format(i, hmc.total_messages_sent))
        total_messages_sent += hmc.total_messages_sent
    logger.info('Total number of messages: {}\n'.format(total_messages_sent))

    # dump configuration and results
    sim = {}
    sim['configuration'] = vars(args)
    sim['results'] = {}

    sim['results']['performance'] = {}
    sim['results']['performance']['training'] = compute_cycles
    sim['results']['performance']['training_by_layer'] = hmcs[0].back_time
    if args.allreduce == 'teccl':
        # For TE-CCL, we only simulate AG time and multiply with 2.
        sim['results']['performance']['total'] = cycles * 2
    else:
        sim['results']['performance']['total'] = cycles
    sim['results']['performance']['allreduce'] = {}
    if args.allreduce == 'teccl':
        # For TE-CCL, we only simulate AG time and multiply with 2.
        sim['results']['performance']['allreduce']['total'] = allreduce_cycles * 2
    else:
        sim['results']['performance']['allreduce']['total'] = allreduce_cycles
    if args.collective != 'Compute':
        if args.allreduce == 'teccl':
            sim['results']['performance']['allreduce']['reduce_scatter'] = allreduce_cycles
        else:
            sim['results']['performance']['allreduce']['reduce_scatter'] = reduce_scatter_time
        if args.collective != 'RS':
            sim['results']['performance']['total_allgather_packets'] = total_allgather_packets
            sim['results']['performance']['total_allgather_waiting_cycles'] = total_allgather_waiting_cycles
            sim['results']['performance']['total_allgather_waiting_cycles_before'] = total_allgather_waiting_cycles_before
            sim['results']['performance']['average_allgather_waiting_cycles'] = average_allgather_waiting_cycles
            sim['results']['performance']['average_allgather_waiting_cycles_before'] = average_allgather_waiting_cycles_before
            sim['results']['performance']['average_allgather_waiting_cycles_total'] = average_allgather_waiting_cycles_total

    network.booksim.CalculatePower()
    net_dyn_power = network.booksim.GetNetDynPower()
    net_leak_power = network.booksim.GetNetLeakPower()
    router_dyn_power = network.booksim.GetRouterDynPower()
    router_leak_power = network.booksim.GetRouterLeakPower()
    link_dyn_power = network.booksim.GetLinkDynPower()
    link_leak_power = network.booksim.GetLinkLeakPower()
    net_link_activities = network.booksim.GetNetLinkActivities()

    # print("Active area: " + str(network.booksim.GetActiveArea()))

    # TODO: Add area analysis
    sim['results']['power'] = {}
    sim['results']['power']['network'] = {}
    sim['results']['power']['network']['dynamic'] = net_dyn_power
    sim['results']['power']['network']['static'] = net_leak_power
    sim['results']['power']['network']['total'] = net_dyn_power + net_leak_power
    sim['results']['power']['network']['router'] = {}
    sim['results']['power']['network']['router']['dynamic'] = router_dyn_power
    sim['results']['power']['network']['router']['static'] = router_leak_power
    sim['results']['power']['network']['router']['total'] = router_dyn_power + router_leak_power
    sim['results']['power']['network']['link'] = {}
    sim['results']['power']['network']['link']['dynamic'] = link_dyn_power
    sim['results']['power']['network']['link']['static'] = link_leak_power
    sim['results']['power']['network']['link']['total'] = link_dyn_power + link_leak_power
    sim['results']['power']['network']['link']['flits'] = net_link_activities

    with open(jsonfile_name, 'w') as simfile:
        json.dump(sim, simfile, indent=4)
        simfile.close()
    logger.info('Simulation Done \n')
    logger.info("Total time " + str(time.time() - start_time))


if __name__ == '__main__':
    main()
