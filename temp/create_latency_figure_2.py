#!/bin/python3.6
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter
from matplotlib.ticker import LogLocator

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 18

def draw_graph_2(ax):
    labels = ['MultiTree', 'TACOS', 'SM_Bi', 'SM_Alter', 'SM_Uni']
    network_latency = [45565, 34753, 671, 671, 671]
    packet_latency = [46727, 35334, 687, 687, 687]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    rects1 = ax.bar(x, network_latency, width, label='Average Network Latency', color='blue', edgecolor='black', linestyle='--')
    rects2 = ax.bar(x, packet_latency, width, bottom=network_latency, label='Average Packet Latency', color='red', edgecolor='black', linestyle='--')

    totals = [n + p for n, p in zip(network_latency, packet_latency)]
    for i, total in enumerate(totals):
        ax.text(x[i], total + 500, f'{total}', ha='center', va='bottom')
    max_total = max(totals) + 10000

    formatter = ScalarFormatter(useMathText=True)  # Enables math text for scientific notation
    formatter.set_scientific(True)  # Enable scientific notation
    formatter.set_powerlimits((0, 0))  # Sets the threshold for scientific notation
    ax.yaxis.set_major_formatter(formatter)
    ax.set_ylim(0, max_total)
    ax.set_ylabel('Cycles')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)

def draw_graph(ax):
    labels = ['MultiTree', 'TACOS', 'SM_Bi', 'SM_Alter', 'SM_Uni']
    network_latency = [45565, 34753, 671, 671, 671]
    packet_latency = [46727, 35334, 687, 687, 687]
    waiting_cycles = [456283, 379776, 124044, 124033, 135303]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    # fig, ax = plt.subplots(figsize=(12, 8))
    rects1 = ax.bar(x, network_latency, width, label='Average Network Latency', color='blue', edgecolor='black', linestyle='--')
    rects2 = ax.bar(x, packet_latency, width, bottom=network_latency, label='Average Packet Latency', color='red', edgecolor='black', linestyle='--')
    rects3 = ax.bar(x, waiting_cycles, width, bottom=np.array(network_latency) + np.array(packet_latency),
                    label='Average Waiting Cycles', color='#63f7c6', edgecolor='black', linestyle='--')

    formatter = ScalarFormatter(useMathText=True)  # Enables math text for scientific notation
    formatter.set_scientific(True)  # Enable scientific notation
    formatter.set_powerlimits((0, 0))  # Sets the threshold for scientific notation
    ax.yaxis.set_major_formatter(formatter)
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Cycles')
    # ax.set_title('Comparison of Network and Packet Latency, and Waiting Cycles')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)
    # ax.legend()


def main():
    plt.rcParams["figure.figsize"] = [14.00, 4.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 2)

    draw_graph_2(ax1[0])
    draw_graph(ax1[1])

    lines_labels = [ax1[1].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    figure.legend(lines, labels, loc='upper center', ncol=6, bbox_to_anchor=(0.5, 1.1))
    # figure.tight_layout()
    figure.savefig('latency_figure.pdf', bbox_inches='tight')


    # plt.show()

if __name__== "__main__":
    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
