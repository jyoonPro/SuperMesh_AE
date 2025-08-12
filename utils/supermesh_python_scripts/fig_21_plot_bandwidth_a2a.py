#!/bin/python3.6
import json
import os
import sys

import matplotlib.pyplot as plt
from easypyplot import pdf

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 19

colors_dict = {'tacos': '#70ad47', 'multitree': '#ed7d31', 'sm_alter': '#4472c4', 'sm_uni': '#0D1282',
                   'tto': '#7A316F', 'sm_bi': '#31AA75', 'mesh': '#ed7d31'}
marker_colors_dict = {'tacos': '#d4f2bf', 'multitree': '#f5ad7d', 'sm_alter': '#b3cefc', 'sm_uni': '#7a7ca3',
                          'tto': '#e8a2de', 'sm_bi': '#a4e0c6', 'mesh': '#f5ad7d'}
markers_dict = {'tacos': 'D', 'multitree': 'X', 'sm_alter': 'o', 'sm_uni': '^',
                    'tto': '*', 'sm_bi': 'v', 'mesh': 'X'}

def draw_graph(ax, schemes, names, folder_names, ldata, xlabels, total_nodes, y_lim = None):
    folder_path = '{}/micro_2025/a2a/bandwidth'.format(os.environ['SIMHOME'])
    gbps = {}
    comm_cycles = {}

    for s, name in enumerate(names):
        if name not in comm_cycles.keys():
            comm_cycles[name] = {}
            for d, data in enumerate(ldata):
                filename = "%s/%s/json/bw_%d_teccl_%d_%s_1_ana.json" % (folder_path, folder_names[s], data, total_nodes, folder_names[s])
                if os.path.exists(filename):
                    with open(filename, 'r') as json_file:
                        sim = json.load(json_file)
                        comm_cycles[name][data] = int(sim['results']['performance']['a2a'])
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

    print(gbps)
    print("Topology " + str(folder_names[0]))
    for i in range(len(names)):
        if i < 1:
            continue
        lowest_speedup = 0
        highest_speedup = 0
        for d, data in enumerate(ldata):
            try:
                speedup = gbps[names[i]][d] / gbps['mesh'][d]
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
        # metrics[names[i]]['mesh'] = (lowest_speedup, highest_speedup)
        print("Name " + names[i] + "Lowest speedup " + str(lowest_speedup) + " Highest speedup " + str(highest_speedup))

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
        # ax.set_xticklabels(xlabels, fontsize=18)
        # ax.yaxis.set_tick_params(labelsize=18)
        ax.set_xticklabels(xlabels)
        ax.yaxis.set_tick_params(labelsize=20)
        if y_lim is not None:
            ax.set_ylim(0,  y_lim)
        # ax.set_xlabel('All-Reduce Data Size for ' + text_to_add, fontsize=18)
        # ax.set_ylabel('Bandwidth (GB/s)', fontsize=18)
        # ax.set_xlabel(text_to_add, y=5)
        ax.set_ylabel('Bandwidth (GB/s)')
        ax.yaxis.grid(True, linestyle='--', color='black')
        ax.xaxis.set_label_coords(0.5, -0.15)
        hdls, lab = ax.get_legend_handles_labels()


def main():
    # metrics = {'proposed': {}}
    schemes = ['Mesh', '$SM_{Alter}$', '$SM_{Bi}$']
    names = ['mesh', 'sm_alter', 'sm_bi']

    ldata = [262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432, 67108864, 134217728]
    xlabels = ['1MB', '', '4MB', '', '16MB', '', '64MB', '', '256MB', '']

    plt.rcParams["figure.figsize"] = [6.00, 4.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 1)

    total_nodes = 9
    folder_names = ['mesh', 'SM_Alter', 'SM_Bi']
    draw_graph(ax1, schemes, names, folder_names, ldata, xlabels, total_nodes, y_lim=22)

    # print("proposed")
    # print("Compared to NCCL: " + str(metrics['proposed']['nccl']))
    # print("Compared to TACCL: " + str(metrics['proposed']['taccl']))
    # print("Compared to TECCL: " + str(metrics['proposed']['teccl']))

    lines_labels = [ax1.get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    figure.legend(lines, labels, loc='upper center', ncol=7, bbox_to_anchor=(0.5, 1.1))
    figure.savefig('fig_21_bandwidth_a2a_' + str(total_nodes) + '.pdf', bbox_inches='tight')


    # plt.show()

if __name__== "__main__":
    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
