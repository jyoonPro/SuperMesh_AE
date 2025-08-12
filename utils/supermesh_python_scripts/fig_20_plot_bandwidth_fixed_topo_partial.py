#!/bin/python3.6
import json
import os

import matplotlib.pyplot as plt
from easypyplot import pdf

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 17

def draw_graph_ar(ax, schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, text_to_add, used_names, colors_dict, marker_colors_dict,markers_dict):
    gbps = {}
    comm_cycles = {}

    # get the file names
    for s, name in enumerate(names):
        if name not in comm_cycles.keys():
            comm_cycles[name] = {}

            for d, data in enumerate(ldata):
                if data not in comm_cycles[name].keys():
                    comm_cycles[name][data] = []
                    # if name == 'tacos' or name == 'multitree' or (name == 'teccl' and folder_names[s] == 'SM_Bi') or (name == 'teccl' and folder_names[s] == 'SM_Alter'):
                    if name == 'teccl' and folder_names[s] == 'SM_Uni':
                        filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AG.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])
                    else:
                        filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])

                    #     if os.path.exists(filename):
                    #         # print(filename)
                    #         with open(filename, 'r') as json_file:
                    #             sim = json.load(json_file)
                    #             totals = float(sim['results']['performance']['allreduce']['total'])
                    #             rs = float(sim['results']['performance']['allreduce']['reduce_scatter'])
                    #             comm_cycles[name][data] = totals - rs
                    #     else:
                    #         print(filename)
                    #         comm_cycles[name][data] = 0
                    # else:
                    #     filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AG.json" % (
                    #     folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])

                    if os.path.exists(filename):
                        # print(filename)
                        with open(filename, 'r') as json_file:
                            sim = json.load(json_file)
                            if name == 'teccl' and folder_names[s] == 'SM_Uni':
                                comm_cycles[name][data] = float(sim['results']['performance']['allreduce']['total']) * 2
                            else:
                                comm_cycles[name][data] = float(sim['results']['performance']['allreduce']['total'])
                    else:
                        print(filename)
                        comm_cycles[name][data] = 0

                    # if name == 'teccl' and folder_names[s] == 'SM_Uni':
                    #     filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AG.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])
                    # else:
                    #     filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])
                    #
                    # if os.path.exists(filename):
                    #     # print(filename)
                    #     with open(filename, 'r') as json_file:
                    #         sim = json.load(json_file)
                    #         # comm_cycles[name][data] = float(sim['results']['performance']['allreduce']['total'])
                    #         totals = float(sim['results']['performance']['allreduce']['total'])
                    #         rs = float(sim['results']['performance']['allreduce']['reduce_scatter'])
                    #         comm_cycles[name][data] = totals - rs
                    # else:
                    #     print(filename)
                    #     comm_cycles[name][data] = 0

    for s, name in enumerate(names):
        if name not in gbps.keys():
            gbps[name] = []
            for d, data in enumerate(ldata):
                if comm_cycles[name][data] != 0:
                    gbps[name].append(((float(data * 4) / (1024 * 1024 * 1024))) / (comm_cycles[name][data] / (10 ** 9)))
                else:
                    gbps[name].append(0)

    print(gbps)

    # for i in range(len(names)-1):
    #     lowest_speedup = 0
    #     highest_speedup = 0
    #     for d, data in enumerate(ldata):
    #         speedup = gbps[names[i+1]][d] / gbps['tto'][d]
    #         if d == 0:
    #             lowest_speedup = speedup
    #             highest_speedup = speedup
    #         else:
    #             if speedup > highest_speedup:
    #                 highest_speedup = speedup
    #             if speedup < lowest_speedup:
    #                 lowest_speedup = speedup
    #     print(str(names[i+1]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    # colors = ['#70ad47', '#ed7d31', '#4472c4', '#0D1282', '#7A316F', '#31AA75', '#EC255A']
    # makercolors = ['#e2f0d9', '#fbe5d6', '#dae3f3', '#F0DE36', '#7A316F', '#31AA75', '#EC255A']
    # linestyles = ['-', '-', '-', '-', '-', '-', '-', '-']
    # markers = ['D', 'X', 'o', '^', '*', 'v', 'p', 'h']
    colors = []
    makercolors = []
    linestyles = []
    markers = []
    for name in names:
        if name == 'sm_uni' or name == 'sm_alter' or name == 'sm_bi':
            colors.append(colors_dict['sm'])
            makercolors.append(marker_colors_dict['sm'])
            linestyles.append('-')
            markers.append(markers_dict['sm'])
        else:
            colors.append(colors_dict[name])
            makercolors.append(marker_colors_dict[name])
            linestyles.append('-')
            markers.append(markers_dict[name])

    for s, scheme in enumerate(names):
        ax.plot(
            gbps[scheme],
            marker=markers[s],
            markersize=14,
            markeredgecolor=colors[s],
            markerfacecolor=makercolors[s],
            markeredgewidth=3,
            color=colors[s],
            linestyle=linestyles[s],
            linewidth=3,
            label=schemes[s],
        )
        ax.set_xticks(range(len(ldata)))
        ax.set_xticklabels(xlabels)
        ax.yaxis.set_tick_params(labelsize=20)
        ax.set_xlabel(text_to_add, y=5)
        ax.set_ylabel('Bandwidth (GB/s)')
        ax.yaxis.grid(True, linestyle='--', color='black')
        ax.xaxis.set_label_coords(0.5, -0.15)
        hdls, lab = ax.get_legend_handles_labels()

def draw_graph(ax, schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, text_to_add, used_names):
    gbps = {}
    comm_cycles = {}

    # get the file names
    for s, name in enumerate(names):
        if name not in comm_cycles.keys():
            comm_cycles[name] = {}

            for d, data in enumerate(ldata):
                if data not in comm_cycles[name].keys():
                    comm_cycles[name][data] = []
                    if name == 'tacos' or name == 'multitree' or name == 'tacos_mesh':
                        filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])

                        if os.path.exists(filename):
                            # print(filename)
                            with open(filename, 'r') as json_file:
                                sim = json.load(json_file)
                                totals = float(sim['results']['performance']['allreduce']['total'])
                                rs = float(sim['results']['performance']['allreduce']['reduce_scatter'])
                                comm_cycles[name][data] = totals - rs
                        else:
                            print(filename)
                            comm_cycles[name][data] = 0
                    else:
                        filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AG.json" % (
                        folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])

                        if os.path.exists(filename):
                            # print(filename)
                            with open(filename, 'r') as json_file:
                                sim = json.load(json_file)
                                comm_cycles[name][data] = float(sim['results']['performance']['allreduce']['total'])
                        else:
                            print(filename)
                            comm_cycles[name][data] = 0

                    # if name == 'teccl' and folder_names[s] == 'SM_Uni':
                    #     filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AG.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])
                    # else:
                    #     filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])
                    #
                    # if os.path.exists(filename):
                    #     # print(filename)
                    #     with open(filename, 'r') as json_file:
                    #         sim = json.load(json_file)
                    #         # comm_cycles[name][data] = float(sim['results']['performance']['allreduce']['total'])
                    #         totals = float(sim['results']['performance']['allreduce']['total'])
                    #         rs = float(sim['results']['performance']['allreduce']['reduce_scatter'])
                    #         comm_cycles[name][data] = totals - rs
                    # else:
                    #     print(filename)
                    #     comm_cycles[name][data] = 0

    for s, name in enumerate(names):
        if name not in gbps.keys():
            gbps[name] = []
            for d, data in enumerate(ldata):
                if comm_cycles[name][data] != 0:
                    gbps[name].append(((float(data * 4) / (1024 * 1024 * 1024))) / (comm_cycles[name][data] / (10 ** 9)))
                else:
                    gbps[name].append(0)

    print(gbps)

    # for i in range(len(names)-1):
    #     lowest_speedup = 0
    #     highest_speedup = 0
    #     for d, data in enumerate(ldata):
    #         speedup = gbps[names[i+1]][d] / gbps['tto'][d]
    #         if d == 0:
    #             lowest_speedup = speedup
    #             highest_speedup = speedup
    #         else:
    #             if speedup > highest_speedup:
    #                 highest_speedup = speedup
    #             if speedup < lowest_speedup:
    #                 lowest_speedup = speedup
    #     print(str(names[i+1]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    colors = ['#70ad47', '#ed7d31', '#4472c4', '#0D1282', '#7A316F', '#31AA75', '#EC255A']
    makercolors = ['#e2f0d9', '#fbe5d6', '#dae3f3', '#F0DE36', '#7A316F', '#31AA75', '#EC255A']
    linestyles = ['-', '-', '-', '-', '-', '-', '-', '-']
    markers = ['D', 'X', 'o', '^', '*', 'v', 'p', 'h']

    for s, scheme in enumerate(names):
        ax.plot(
            gbps[scheme],
            marker=markers[s],
            markersize=14,
            markeredgecolor=colors[s],
            markerfacecolor=makercolors[s],
            markeredgewidth=3,
            color=colors[s],
            linestyle=linestyles[s],
            linewidth=3,
            label=schemes[s],
        )
        ax.set_xticks(range(len(ldata)))
        ax.set_xticklabels(xlabels)
        ax.yaxis.set_tick_params(labelsize=20)
        ax.set_xlabel(text_to_add, y=5)
        ax.set_ylabel('Bandwidth (GB/s)')
        ax.yaxis.grid(True, linestyle='--', color='black')
        ax.xaxis.set_label_coords(0.5, -0.15)
        hdls, lab = ax.get_legend_handles_labels()


def main():
    colors_dict = {'tacos': '#70ad47', 'multitree': '#ed7d31', 'sm_alter': '#4472c4', 'sm_uni': '#0D1282',
                   'tto': '#7A316F', 'sm_bi': '#31AA75', 'mesh': '#ed7d31', 'teccl': '#e81416', 'sm': '#4472c4'}
    marker_colors_dict = {'tacos': '#d4f2bf', 'multitree': '#f5ad7d', 'sm_alter': '#b3cefc', 'sm_uni': '#7a7ca3',
                          'tto': '#e8a2de', 'sm_bi': '#a4e0c6', 'mesh': '#f5ad7d', 'teccl': '#db9394', 'sm': '#b3cefc'}
    markers_dict = {'tacos': 'D', 'multitree': 'X', 'sm_alter': 'o', 'sm_uni': '^',
                    'tto': '*', 'sm_bi': 'v', 'mesh': 'X', 'teccl': 'p', 'sm': 'o'}

    schemes = ['TTO', 'TACOS', 'MultiTree', 'SM']
    used_names = ['pipeline', 'tacos', 'multitree', 'pipeline']
    total_nodes = 16
    ldata = [262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432, 67108864, 134217728]
    xlabels = ['1MB', '', '', '8MB', '', '', '64MB', '', '', '512MB']

    plt.rcParams["figure.figsize"] = [10.00, 4.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 2)
    folder_path = '{}/micro_2025/bandwidth'.format(os.environ['SIMHOME'])

    # folder_names = ['mesh', 'Partial_SM_Alter', 'Partial_SM_Alter', 'Partial_SM_Alter']
    # names = ['tacos_mesh', 'tacos', 'multitree', 'sm_alter']
    # draw_graph(ax1[0], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, 'AG:$Partial SM_{Alter}$', used_names)
    # folder_names = ['mesh', 'Partial_SM_Bi', 'Partial_SM_Bi', 'Partial_SM_Bi']
    # names = ['tacos_mesh', 'tacos', 'multitree', 'sm_bi']
    # draw_graph(ax1[1], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, 'AG:$Partial SM_{Bi}$', used_names)

    folder_names = ['mesh', 'Partial_SM_Alter', 'Partial_SM_Alter', 'Partial_SM_Alter']
    names = ['tto','tacos', 'multitree', 'sm_alter']
    draw_graph_ar(ax1[0], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, '$SM_{Alter}$',
               used_names, colors_dict, marker_colors_dict,markers_dict)
    folder_names = ['mesh', 'Partial_SM_Bi', 'Partial_SM_Bi', 'Partial_SM_Bi']
    names = ['tto', 'tacos', 'multitree', 'sm_bi']
    draw_graph_ar(ax1[1], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, '$SM_{Bi}$', used_names, colors_dict, marker_colors_dict,markers_dict)

    
    lines_labels = [ax1[0].get_legend_handles_labels()]
    # lines_labels_2 = [ax1[1].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    # lines.insert(5, lines_labels_2[0][0][4])
    # labels.insert(5, lines_labels_2[0][1][4])
    figure.legend(lines, labels, loc='upper center', ncol=7, bbox_to_anchor=(0.5, 1.08))
    # figure.tight_layout()
    figure.savefig('fig_20_bandwidth_fixed_topo_partial.pdf', bbox_inches='tight')


    # plt.show()

if __name__== "__main__":
    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
