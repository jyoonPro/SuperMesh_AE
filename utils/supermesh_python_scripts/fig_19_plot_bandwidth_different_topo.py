#!/bin/python3.6
import json
import os

import matplotlib.pyplot as plt
from easypyplot import pdf

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 17

def draw_graph(ax, schemes, names, folder_names, ldata, xlabels, folder_path, used_names, text_to_add, colors_dict, marker_colors_dict, markers_dict):
    gbps = {}
    comm_cycles = {}

    # get the file names
    for s, name in enumerate(names):
        if name not in comm_cycles.keys():
            comm_cycles[name] = {}

            for d, data in enumerate(ldata):
                if data not in comm_cycles[name].keys():
                    comm_cycles[name][data] = []
                    if name == 'cmesh' or name == 'fb' or name == 'kite_s' or name == 'kite_m':
                        nodes = 16
                        # When we use concentration, each node sends 4 times data to the neighbors. However, 4 nodes in the
                        # concentration needs to use the same router. Also, we are only using concentration to reduce number of
                        # routers and links, but 64 nodes are actually using for collective. So, compared to 8x8, in 4x4 each
                        # router in the concentration needs to send 16 times more data. So, for fair comparison, we should
                        # multiply the data_size with 4 so that after dividing by 16, each router in the 4x4 topology sends 16
                        # times compared to 8x8 topology.
                        updated_data_size = data * 4
                        filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s],
                                                                                         updated_data_size, used_names[s], nodes,
                                                                                         folder_names[s])
                    else:
                        nodes = 64
                        filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data, used_names[s], nodes, folder_names[s])

                    if os.path.exists(filename):
                        # print(filename)
                        with open(filename, 'r') as json_file:
                            sim = json.load(json_file)
                            # comm_cycles[name][data] = float(sim['results']['performance']['allreduce']['total'])
                            totals = float(sim['results']['performance']['allreduce']['total'])
                            # rs = float(sim['results']['performance']['allreduce']['reduce_scatter'])
                            # comm_cycles[name][data] = totals - rs
                            comm_cycles[name][data] = totals
                    else:
                        print(filename)
                        comm_cycles[name][data] = 0

    for s, name in enumerate(names):
        if name not in gbps.keys():
            gbps[name] = []
            for d, data in enumerate(ldata):
                if comm_cycles[name][data] != 0:
                    gbps[name].append(((float(data * 4) / (1024 * 1024 * 1024))) / (comm_cycles[name][data] / (10 ** 9)))
                else:
                    gbps[name].append(0)

    # print(gbps)
    # print("SM Uni")
    # for i in range(len(names)-1):
    #     if i > 5:
    #         continue
    #     lowest_speedup = 0
    #     highest_speedup = 0
    #     for d, data in enumerate(ldata):
    #         try:
    #             speedup = gbps[names[6]][d] / gbps[names[i]][d]
    #         except Exception as e:
    #             continue
    #         if d == 0:
    #             lowest_speedup = speedup
    #             highest_speedup = speedup
    #         else:
    #             if speedup > highest_speedup:
    #                 highest_speedup = speedup
    #             if speedup < lowest_speedup:
    #                 lowest_speedup = speedup
    #     print(str(names[i]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    print("SM Alter")
    for i in range(len(names) - 1):
        if i > 5:
            continue
        lowest_speedup = 0
        highest_speedup = 0
        for d, data in enumerate(ldata):
            try:
                speedup = gbps[names[6]][d] / gbps[names[i]][d]
            except Exception as e:
                continue
            if d == 0:
                lowest_speedup = speedup
                highest_speedup = speedup
            else:
                if speedup > highest_speedup:
                    highest_speedup = speedup
                if speedup < lowest_speedup:
                    lowest_speedup = speedup
        print(str(names[i]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    print("SM Bi")
    for i in range(len(names) - 1):
        if i > 5:
            continue
        lowest_speedup = 0
        highest_speedup = 0
        for d, data in enumerate(ldata):
            try:
                speedup = gbps[names[7]][d] / gbps[names[i]][d]
            except Exception as e:
                continue
            if d == 0:
                lowest_speedup = speedup
                highest_speedup = speedup
            else:
                if speedup > highest_speedup:
                    highest_speedup = speedup
                if speedup < lowest_speedup:
                    lowest_speedup = speedup
        print(str(names[i]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    # colors = ['#70ad47', '#ed7d31', '#4472c4', '#0D1282', '#7A316F', '#31AA75', '#EC255A', '#FFAAA6', '#B8A6A6']
    # makercolors = ['#e2f0d9', '#fbe5d6', '#dae3f3', '#F0DE36', '#7A316F', '#31AA75', '#EC255A', '#FFAAA6', '#B8A6A6']
    # linestyles = ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-']
    # markers = ['D', 'X', 'o', '^', '*', 'v', 'p', 'h', 'h', 'h']

    colors = []
    makercolors = []
    linestyles = []
    markers = []
    for name in names:
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
        # ax.set_xlabel(text_to_add, y=5)
        ax.set_ylabel('Bandwidth (GB/s)')
        ax.yaxis.grid(True, linestyle='--', color='black')
        ax.xaxis.set_label_coords(0.5, -0.15)
        hdls, lab = ax.get_legend_handles_labels()


def main():
    colors_dict = {'tacos': '#70ad47', 'multitree': '#ed7d31', 'sm_alter': '#4472c4', 'sm_uni': '#0D1282',
                   'tto': '#7A316F', 'sm_bi': '#31AA75', 'mesh': '#ed7d31', 'teccl': '#e81416', 'sm': '#4472c4', 'cmesh': '#70ad47', 'fb': '#7A316F', 'ft': '#e81416', 'kite_s': '#0caff5', 'kite_m': '#078003'}
    marker_colors_dict = {'tacos': '#d4f2bf', 'multitree': '#f5ad7d', 'sm_alter': '#b3cefc', 'sm_uni': '#7a7ca3',
                          'tto': '#e8a2de', 'sm_bi': '#a4e0c6', 'mesh': '#f5ad7d', 'teccl': '#db9394', 'sm': '#b3cefc', 'cmesh': '#d4f2bf', 'fb': '#e8a2de', 'ft': '#db9394', 'kite_s': '#d4f2ff', 'kite_m': '#93c291'}
    markers_dict = {'tacos': 'D', 'multitree': 'X', 'sm_alter': 'o', 'sm_uni': '^',
                    'tto': '*', 'sm_bi': 'v', 'mesh': 'X', 'teccl': 'p', 'sm': 'o', 'cmesh': 'D', 'fb': '*', 'ft': 'p', 'kite_s': 'h', 'kite_m': '8'}

    schemes = ['Mesh', 'CMesh', 'DB', 'FT', 'Kite(S)', 'Kite(M)', '$SM_{Alter}$', '$SM_{Bi}$']
    names = ['mesh', 'cmesh', 'fb', 'ft', 'kite_s', 'kite_m', 'sm_alter', 'sm_bi']
    folder_names = ['mesh', 'cmesh', 'dbutterfly', 'folded_torus', 'kite', 'kite_medium', 'SM_Alter', 'SM_Bi']
    total_nodes = 64
    ldata = [262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432]
    xlabels = ['1MB', '', '', '8MB', '', '', '64MB', '']

    plt.rcParams["figure.figsize"] = [7.00, 3.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 1)
    folder_path = '{}/micro_2025/bandwidth'.format(os.environ['SIMHOME'])
    used_names = ['pipeline', 'tacos', 'tacos', 'tacos', 'tacos', 'tacos', 'pipeline', 'pipeline']
    draw_graph(ax1, schemes, names, folder_names, ldata, xlabels, folder_path, used_names, 'Mesh with TTO', colors_dict, marker_colors_dict, markers_dict)

    # used_names = ['tacos', 'tacos', 'tacos', 'tacos', 'tacos', 'tacos', 'pipeline', 'pipeline', 'pipeline']
    # draw_graph(ax1[1], schemes, names, folder_names, ldata, xlabels, folder_path, used_names, "Mesh with TACOS")
    
    lines_labels = [ax1.get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    figure.legend(lines, labels, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.22))
    # figure.tight_layout()
    figure.savefig('fig_19_bandwidth_different_topo_updated.pdf', bbox_inches='tight')


    # plt.show()

if __name__== "__main__":
    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
