#!/bin/python3.6
import json
import os

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 19

def plot_allreduce(ax, nodes, names, schemes, folder_names, xlim, ylim, xlabel, ylabel, xticks, used_names, colors_dict, marker_colors_dict, markers_dict):
    # colors = ['#70ad47', '#ed7d31', '#0D1282', '#7A316F', '#31AA75', '#EC255A', '#1E235A']
    # makercolors = ['#e2f0d9', '#fbe5d6', '#F0DE36', '#7A316F', '#31AA75', '#EC255A', '#1E235A']
    # linestyles = ['-', '-', '-', '-', '-', '-', '-']
    # markers = ['D', 'X', '^', '*', 'v', 'p', 'h']

    colors = []
    makercolors = []
    linestyles = []
    markers = []
    for name in names:
        colors.append(colors_dict[name])
        makercolors.append(marker_colors_dict[name])
        linestyles.append('-')
        markers.append(markers_dict[name])

    folder_path = '{}/micro_2025/scalability'.format(os.environ['SIMHOME'])
    algorithmic_scalability = {}
    cycles = np.zeros(
        (int(len(schemes)), int(len(nodes))), dtype=np.float64)

    for s, name in enumerate(names):
        for n, node in enumerate(nodes):

            filename = "%s/%s/scalability_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], used_names[s], node, folder_names[s])

            if os.path.exists(filename):
                # print(filename)
                with open(filename, 'r') as json_file:
                    sim = json.load(json_file)
                    cycles[s][n] = float(sim['results']['performance']['allreduce']['total'])
            else:
                print(filename)
                cycles[s][n] = 0


            # if name == 'mesh_overlap_2d_1':
            #     filename = "%s/%s/pipeline/scalability_%s_%d_mesh_alexnet_express_ar.json" % (folder_path, folder_names[s], name, node)
            # else:
            #     filename = "%s/%s/pipeline/scalability_%s_%d_%s_alexnet_express_ar.json" % ( folder_path, folder_names[s], name, node, name)
            # # print (filename)
            # if os.path.exists(filename):
            #     # print(filename)
            #     with open(filename, 'r') as json_file:
            #         sim = json.load(json_file)
            #         cycles[s][n] = sim['results']['performance']['total']
            # else:
            #     print(filename)1
            #     cycles[s][n] = 0

        algorithmic_scalability[name] = [int(ele)/cycles[0][0] for ele in cycles[s]]

    # print(algorithmic_scalability)

    print("Compared to TACOS")
    for j in range(len(names)):
        if j < 3:
            continue
        lowest_speedup = 1000
        highest_speedup = 0
        for i in range(len(nodes)):
            speedup = cycles[0][i] / cycles[j][i]
            if speedup > highest_speedup:
                highest_speedup = speedup
            if speedup < lowest_speedup:
                lowest_speedup = speedup
        print(str(names[j]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    # print("Compared to Multitree")
    # for j in range(len(names)):
    #     if j < 3:
    #         continue
    #     lowest_speedup = 1000
    #     highest_speedup = 0
    #     for i in range(len(nodes)):
    #         speedup = cycles[1][i] / cycles[j][i]
    #         if speedup > highest_speedup:
    #             highest_speedup = speedup
    #         if speedup < lowest_speedup:
    #             lowest_speedup = speedup
    #     print(str(names[j]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    print("Compared to TTO")
    for j in range(len(names)):
        if j < 3:
            continue
        lowest_speedup = 1000
        highest_speedup = 0
        for i in range(len(nodes)):
            speedup = cycles[2][i] / cycles[j][i]
            if speedup > highest_speedup:
                highest_speedup = speedup
            if speedup < lowest_speedup:
                lowest_speedup = speedup
        print(str(names[j]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    for s, scheme in enumerate(names):
        ax.plot(
            nodes,
            algorithmic_scalability[scheme],
            marker=markers[s],
            markersize=12,
            markeredgecolor=colors[s],
            markerfacecolor=makercolors[s],
            markeredgewidth=3,
            color=colors[s],
            linestyle=linestyles[s],
            linewidth=3,
            label=schemes[s]
            )
        ax.set_xticks(nodes)
        ax.set_xticklabels(xticks)
        ax.set_xlim(0, xlim)
        # ax.set_ylim(0, ylim)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.yaxis.grid(True, linestyle='--', color='black')
        hdls, lab = ax.get_legend_handles_labels()


def plot_reducescatter(ax, nodes, names, schemes, folder_names, xlim, ylim, xlabel, ylabel, collective, xticks, used_names, colors_dict, marker_colors_dict, markers_dict):
    # colors = ['#70ad47', '#ed7d31', '#7A316F', '#31AA75', '#EC255A', '#1E235A']
    # makercolors = ['#e2f0d9', '#fbe5d6', '#7A316F', '#31AA75', '#EC255A', '#1E235A']
    # linestyles = ['-', '-', '-', '-', '-', '-']
    # markers = ['D', 'X', '*', 'v', 'p', 'h']
    colors = []
    makercolors = []
    linestyles = []
    markers = []
    for name in names:
        colors.append(colors_dict[name])
        makercolors.append(marker_colors_dict[name])
        linestyles.append('-')
        markers.append(markers_dict[name])

    folder_path = '{}/micro_2025/scalability'.format(os.environ['SIMHOME'])
    algorithmic_scalability = {}
    cycles = np.zeros(
        (int(len(schemes)), int(len(nodes))), dtype=np.float64)

    for s, name in enumerate(names):
        for n, node in enumerate(nodes):
            if used_names[s] == 'tacos' or used_names[s] == 'multitree':
                filename = "%s/%s/scalability_%s_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], used_names[s], node, folder_names[s])

                if os.path.exists(filename):
                    # print(filename)
                    with open(filename, 'r') as json_file:
                        sim = json.load(json_file)
                        totals = float(sim['results']['performance']['allreduce']['total'])
                        rs = float(sim['results']['performance']['allreduce']['reduce_scatter'])
                        if collective == 'RS':
                            cycles[s][n] = rs
                        else:
                            cycles[s][n] = totals - rs
                else:
                    print(filename)
                    cycles[s][n] = 0
            else:
                filename = "%s/%s/scalability_%s_%d_%s_alexnet_express_128_%s.json" % (
                    folder_path, folder_names[s], used_names[s], node, folder_names[s], collective)

                if os.path.exists(filename):
                    # print(filename)
                    with open(filename, 'r') as json_file:
                        sim = json.load(json_file)
                        cycles[s][n] = float(sim['results']['performance']['allreduce']['total'])
                else:
                    print(filename)
                    cycles[s][n] = 0
        algorithmic_scalability[name] = [int(ele)/cycles[0][0] for ele in cycles[s]]

    print("Compared to TACOS")
    for j in range(len(names)):
        if j < 2:
            continue
        lowest_speedup = 1000
        highest_speedup = 0
        for i in range(len(nodes)):
            speedup = cycles[0][i]/ cycles[j][i]
            if speedup > highest_speedup:
                highest_speedup = speedup
            if speedup < lowest_speedup:
                lowest_speedup = speedup
        print(str(names[j]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    # print("Compared to MultiTree")
    # for j in range(len(names)):
    #     if j < 2:
    #         continue
    #     lowest_speedup = 1000
    #     highest_speedup = 0
    #     for i in range(len(nodes)):
    #         speedup = cycles[1][i] / cycles[j][i]
    #         if speedup > highest_speedup:
    #             highest_speedup = speedup
    #         if speedup < lowest_speedup:
    #             lowest_speedup = speedup
    #     print(str(names[j]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    for s, scheme in enumerate(names):
        ax.plot(
            nodes,
            algorithmic_scalability[scheme],
            marker=markers[s],
            markersize=10,
            markeredgecolor=colors[s],
            markerfacecolor=makercolors[s],
            markeredgewidth=2,
            color=colors[s],
            linestyle=linestyles[s],
            linewidth=3,
            label=schemes[s]
            )
        ax.set_xticks(nodes)
        ax.set_xticklabels(xticks)
        ax.set_xlim(0, xlim)
        # ax.set_ylim(0, ylim)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.yaxis.grid(True, linestyle='--', color='black')
        hdls, lab = ax.get_legend_handles_labels()


def main():
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

    nodes = [9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256]
    xticks = ['', '16', '', '36', '', '64', '', '100', '', '144', '', '196', '', '256']

    plt.rcParams["figure.figsize"] = [12.00, 4.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 2)
    print("Allreduce Scalability")
    plot_allreduce(ax1[0], nodes, names, schemes, folder_names, 260, 26, 'AllReduce', 'Normalized Runtime', xticks, used_names, colors_dict, marker_colors_dict, markers_dict)

    schemes = ['TACOS', '$SM_{Alter}', '$SM_{Bi}$']
    names = ['tacos', 'sm_alter', 'sm_bi']
    used_names = ['tacos', 'pipeline', 'pipeline']
    folder_names = ['mesh', 'SM_Alter', 'SM_Bi']
    collective = 'AG'
    print("Allgather Scalability")
    plot_reducescatter(ax1[1], nodes, names, schemes, folder_names, 260, 26, 'AllGather', 'Normalized Runtime', collective, xticks, used_names, colors_dict, marker_colors_dict, markers_dict)

    lines_labels = [ax1[0].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    figure.legend(lines, labels, loc='upper center', ncol=6, bbox_to_anchor=(0.5, 1.1))
    figure.savefig('fig_11_scalability_both.pdf', bbox_inches='tight')


if __name__== "__main__":
    main()
