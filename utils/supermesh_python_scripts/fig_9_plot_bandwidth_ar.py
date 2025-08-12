#!/bin/python3.6
import json
import os

import matplotlib.pyplot as plt
from easypyplot import pdf

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 19

def draw_graph(ax, schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, text_to_add, used_names, metrics, colors_dict, marker_colors_dict, markers_dict):
    gbps = {}
    comm_cycles = {}

    # get the file names
    for s, name in enumerate(names):
        if name not in comm_cycles.keys():
            comm_cycles[name] = {}

            for d, data in enumerate(ldata):
                if data not in comm_cycles[name].keys():
                    comm_cycles[name][data] = []
                    filename = "%s/%s/bw_%d_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])

                    if os.path.exists(filename):
                        # print(filename)
                        with open(filename, 'r') as json_file:
                            sim = json.load(json_file)
                            comm_cycles[name][data] = float(sim['results']['performance']['allreduce']['total'])
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

    for i in range(len(names)):
        # We don't need comparison among TACOS, MultiTree and TTO
        if i < 2:
            continue
        lowest_speedup = 0
        highest_speedup = 0
        for d, data in enumerate(ldata):
            try:
                speedup = gbps[names[i]][d] / gbps['tto'][d]
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
        if 'tto' in metrics[names[i]].keys():
            if lowest_speedup < metrics[names[i]]['tto'][0]:
                metrics[names[i]]['tto'] = (lowest_speedup, metrics[names[i]]['tto'][1])
            if highest_speedup > metrics[names[i]]['tto'][1]:
                metrics[names[i]]['tto'] = (metrics[names[i]]['tto'][0], highest_speedup)
        else:
            metrics[names[i]]['tto'] = (lowest_speedup, highest_speedup)

    for i in range(len(names)):
        # We don't need comparison among TACOS, MultiTree and TTO
        if i < 2:
            continue
        lowest_speedup = 0
        highest_speedup = 0
        for d, data in enumerate(ldata):
            try:
                speedup = gbps[names[i]][d] / gbps['tacos'][d]
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
        if 'tacos' in metrics[names[i]].keys():
            if lowest_speedup < metrics[names[i]]['tacos'][0]:
                metrics[names[i]]['tacos'] = (lowest_speedup, metrics[names[i]]['tacos'][1])
            if highest_speedup > metrics[names[i]]['tacos'][1]:
                metrics[names[i]]['tacos'] = (metrics[names[i]]['tacos'][0], highest_speedup)
        else:
            metrics[names[i]]['tacos'] = (lowest_speedup, highest_speedup)

    # for i in range(len(names)):
    #     # We don't need comparison among TACOS, MultiTree and TTO
    #     if i < 3:
    #         continue
    #     lowest_speedup = 0
    #     highest_speedup = 0
    #     for d, data in enumerate(ldata):
    #         try:
    #             speedup = gbps[names[i]][d] / gbps['multitree'][d]
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
    #     if 'multitree' in metrics[names[i]].keys():
    #         if lowest_speedup < metrics[names[i]]['multitree'][0]:
    #             metrics[names[i]]['multitree'] = (lowest_speedup, metrics[names[i]]['multitree'][1])
    #         if highest_speedup > metrics[names[i]]['multitree'][1]:
    #             metrics[names[i]]['multitree'] = (metrics[names[i]]['multitree'][0], highest_speedup)
    #     else:
    #         metrics[names[i]]['multitree'] = (lowest_speedup, highest_speedup)

    colors = []
    makercolors = []
    linestyles = []
    markers = []
    for name in names:
        colors.append(colors_dict[name])
        makercolors.append(marker_colors_dict[name])
        linestyles.append('-')
        markers.append(markers_dict[name])

    # colors = ['#70ad47', '#ed7d31', '#4472c4', '#0D1282', '#7A316F', '#31AA75', '#EC255A']
    # makercolors = ['#e2f0d9', '#fbe5d6', '#dae3f3', '#F0DE36', '#7A316F', '#31AA75', '#EC255A']
    # linestyles = ['-', '-', '-', '-', '-', '-', '-', '-']
    # markers = ['D', 'X', 'o', '^', '*', 'v', 'p', 'h']

    for s, scheme in enumerate(names):
        # if s > 2:
        #     continue
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
        ax.set_ylim(8, 23)
        ax.set_xlabel(text_to_add, y=5)
        ax.set_ylabel('Bandwidth (GB/s)')
        ax.yaxis.grid(True, linestyle='--', color='black')
        ax.xaxis.set_label_coords(0.5, -0.15)
        hdls, lab = ax.get_legend_handles_labels()


def main():
    metrics = {'sm_uni': {}, 'sm_alter': {}, 'sm_bi': {}}
    colors_dict = {'tacos': '#70ad47', 'multitree': '#ed7d31', 'sm_alter': '#4472c4', 'sm_uni': '#0D1282',
                   'tto': '#7A316F', 'sm_bi': '#31AA75'}
    marker_colors_dict = {'tacos': '#d4f2bf', 'multitree': '#f5ad7d', 'sm_alter': '#b3cefc', 'sm_uni': '#7a7ca3',
                          'tto': '#e8a2de', 'sm_bi': '#a4e0c6'}
    markers_dict = {'tacos': 'D', 'multitree': 'X', 'sm_alter': 'o', 'sm_uni': '^',
                    'tto': '*', 'sm_bi': 'v'}

    schemes = ['TACOS', 'TTO', '$SM_{Alter}$', '$SM_{Bi}$']
    names = ['tacos', 'tto', 'sm_alter', 'sm_bi']
    used_names = ['tacos', 'pipeline', 'pipeline', 'pipeline']
    folder_names = ['mesh', 'mesh', 'SM_Alter', 'SM_Bi']

    ldata = [262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432, 67108864, 134217728]
    xlabels = ['1MB', '', '', '8MB', '', '', '64MB', '', '', '512MB']

    plt.rcParams["figure.figsize"] = [25.00, 4.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 4)
    folder_path = '{}/micro_2025/bandwidth'.format(os.environ['SIMHOME'])

    total_nodes = 16
    draw_graph(ax1[0], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, '4x4 Mesh & SuperMesh', used_names, metrics, colors_dict, marker_colors_dict, markers_dict)

    total_nodes = 25
    draw_graph(ax1[1], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, '5x5 Mesh & SuperMesh', used_names, metrics, colors_dict, marker_colors_dict, markers_dict)

    total_nodes = 64
    draw_graph(ax1[2], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, '8x8 Mesh & SuperMesh', used_names, metrics, colors_dict, marker_colors_dict, markers_dict)

    total_nodes = 81
    draw_graph(ax1[3], schemes, names, folder_names, ldata, xlabels, total_nodes, folder_path, '9x9 Mesh & SuperMesh', used_names, metrics, colors_dict, marker_colors_dict, markers_dict)

    print("SM_Bi")
    # print("Compared to Multitree: " + str(metrics['sm_bi']['multitree']))
    print("Compared to TACOS: " + str(metrics['sm_bi']['tacos']))
    print("Compared to TTO: " + str(metrics['sm_bi']['tto']))
    print("SM_Alter")
    # print("Compared to Multitree: " + str(metrics['sm_alter']['multitree']))
    print("Compared to TACOS: " + str(metrics['sm_alter']['tacos']))
    print("Compared to TTO: " + str(metrics['sm_alter']['tto']))
    # print("SM_Uni")
    # print("Compared to Multitree: " + str(metrics['sm_uni']['multitree']))
    # print("Compared to TACOS: " + str(metrics['sm_uni']['tacos']))
    # print("Compared to TTO: " + str(metrics['sm_uni']['tto']))


    lines_labels = [ax1[0].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    figure.legend(lines, labels, loc='upper center', ncol=6, bbox_to_anchor=(0.5, 1.1))
    # figure.tight_layout()
    figure.savefig('fig_9_bandwidth_pipeline_allreduce.pdf', bbox_inches='tight')


    # plt.show()

if __name__== "__main__":
    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
