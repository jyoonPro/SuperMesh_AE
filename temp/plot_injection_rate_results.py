#!/bin/python3.6
import json
import os
import re
import sys

import matplotlib.pyplot as plt
from easypyplot import pdf

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 19

colors_dict = {'sm_alter': '#4472c4', 'mesh': '#7A316F', 'sm_bi': '#31AA75'}
markers_dict = {'sm_alter': 'o', 'sm_bi': '^',
                    'mesh': '*'}

def draw_graph(ax, results_dir, rates, text_to_add, y_lim_start, y_lim_end):
    base_path = '{}/micro_2025/random_communication/'.format(os.environ['SIMHOME'])
    topologies = ['mesh', 'sm_alter', 'sm_bi']
    topologies_names = ['Mesh', '$SM_{Alter}$', '$SM_{Bi}$']
    pattern = re.compile(r"Packet latency average = ([\d.]+)")

    for idx, topo in enumerate(topologies):
        topo_dir = base_path + results_dir[idx]
        latencies = []

        for rate in rates:
            fname = "output_{:.2f}.txt".format(rate)
            print(fname)
            with open(os.path.join(topo_dir, fname)) as f:
                content = f.read()
                match = pattern.search(content)
                if match:
                    latency = float(match.group(1))
                    latencies.append(latency)
        print(latencies)
        ax.plot(rates, latencies,
                 marker=markers_dict[topo],
                 color=colors_dict[topo],
                 label=topologies_names[idx],
                 linewidth=2,
                 markersize=8)

    ax.set_ylim(y, y_lim)
    ax.text(0.5, -0.5, text_to_add, transform=ax.transAxes,
            ha='center', va='top')
    ax.set_xlabel("Injection Rate")
    ax.set_ylabel("Packet Latency Average")
    ax.yaxis.grid(True)


def main():

    plt.rcParams["figure.figsize"] = [8.00, 4.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 2)

    results_dir = ["results_latency_mesh", "results_latency_sm_alter", "results_latency_sm_bi"]
    rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    draw_graph(ax1[0], results_dir, rates, 'uniform traffic', y_lim_start=10, y_lim_end=40)
    results_dir = ["results_latency_mesh_tornado", "results_latency_sm_alter_tornado", "results_latency_sm_bi_tornado"]
    rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
    draw_graph(ax1[1], results_dir, rates, 'tornado traffic', y_lim_start = 10, y_lim_end=25)
    # results_dir = ["results_latency_mesh_bitcomp", "results_latency_sm_alter_bitcomp", "results_latency_sm_bi_bitcomp"]
    # rates = [0.05, 0.10, 0.15, 0.20]
    # draw_graph(ax1[2], results_dir, rates, 'bitcomp traffic', y_lim=60)

    lines_labels = [ax1[0].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    figure.legend(lines, labels, loc='upper center', ncol=7, bbox_to_anchor=(0.5, 1.1))
    figure.savefig('injection_rate_vs_latency_all.pdf', bbox_inches='tight')


    # plt.show()

if __name__== "__main__":
    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
