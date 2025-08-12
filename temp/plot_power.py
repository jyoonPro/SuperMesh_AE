import math

import numpy as np
import json
import os

import matplotlib.pyplot as plt
import numpy as np
from easypyplot import barchart, pdf
from easypyplot import format as fmt
from scipy import stats

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 16


def add_line(ax, xpos, ypos):
    line = plt.Line2D(
        #[xpos, xpos], [ypos + linelen, ypos],
        [xpos, xpos],
        [0, ypos],
        transform=ax.transAxes,
        color='black',
        linewidth=1)
    line.set_clip_on(False)
    ax.add_line(line)
    # ax.legend("AR Speedup")

# def draw_graph_power(ax, folder_path, schemes, total_nodes, names, folder_names, ylabel):
#     # benchmarks = ['AlphaGoZero', 'densenet201', 'Resnet152']
#     # entry_names = ['Router', 'Links']
#     # xlabels = ['AlphaGoZero', 'DenseNet201', 'ResNet152']
#     benchmarks = ['AlphaGoZero', 'Googlenet', 'inceptionv4', 'NCF_recommendation',
#                   'densenet161', 'densenet169', 'densenet201', 'resnet50',
#                   'resnet101', 'vgg16', 'vgg19', 'Resnet152', 'Transformer']
#     entry_names = ['Router', 'Links']
#     xlabels = ['AlphaGoZero', 'GoogLeNet', 'InceptionV4', 'NCF', 'DenseNet161',
#                'DenseNet169', 'DenseNet201', 'ResNet50', 'ResNet101', 'ResNet152', 'VGG16', 'VGG19', 'Transformer']
#     group_names = []
#
#     cycles = np.zeros(
#         (int(len(schemes)), int(len(benchmarks))), dtype=float)
#     cycles_breakdown = np.zeros((2, int(len(benchmarks) * len(schemes))), dtype=float)
#     norm_cycles_breakdown = np.zeros((2, int(len(benchmarks) * len(schemes))), dtype=float)
#     link_energy_per_bit = 1.75e-12
#     freq = 1e9
#
#     for b, bench in enumerate(benchmarks):
#         five_port_router_static_power = None
#         for s, name in enumerate(names):
#             if name == 'mesh_overlap_2d_1':
#                 filename = "%s/%s/%s_%s_%d_mesh_%s_express_ar.json" % (folder_path, folder_names[s], bench, name, total_nodes, bench)
#             else:
#                 filename = "%s/%s/%s_%s_%d_%s_%s_express_ar.json" % (folder_path, folder_names[s], bench, name, total_nodes, name, bench)
#
#             if os.path.exists(filename):
#                 # print(filename)
#                 with open(filename, 'r') as json_file:
#                     sim = json.load(json_file)
#                     total_ar_cycles = sim['results']['performance']['allreduce']['total']
#                     total_router_dynamic_power = sim['results']['power']['network']['router']['dynamic']
#                     total_router_static_power = sim['results']['power']['network']['router']['static']
#                     if name == 'fatmesh_all':
#                         six_port_router_static_power = total_router_static_power / total_nodes
#                         total_router_static_power = 16 * six_port_router_static_power + 20 * five_port_router_static_power
#                     total_flits = sim['results']['power']['network']['link']['flits']
#                     total_bits = total_flits * 4096 # Per flit 4096 bits
#                     total_link_dynamic_power = (total_bits * link_energy_per_bit) / (total_ar_cycles/freq)
#                     if name == 'mesh_overlap_2d_1':
#                         five_port_router_static_power = total_router_static_power / total_nodes
#                     cycles[s][b] = total_router_dynamic_power + total_router_static_power + total_link_dynamic_power
#                     cycles_breakdown[1][b * len(schemes) + s] = total_link_dynamic_power
#                     cycles_breakdown[0][b * len(schemes) + s] = total_router_dynamic_power + total_router_static_power
#                     json_file.close()
#             else:
#                 print(filename)
#                 cycles_breakdown[0][b * len(schemes) + s] = 1
#                 cycles_breakdown[1][b * len(schemes) + s] = 1
#
#     for b, bench in enumerate(benchmarks):
#         for s, name in enumerate(names):
#             group_names.append(schemes[s])
#             for e, entry in enumerate(entry_names):
#                 norm_cycles_breakdown[e][b * len(schemes) + s] = cycles_breakdown[e][b * len(schemes) + s] / cycles[0][
#                     b]
#     norm_cycles_breakdown[np.isnan(norm_cycles_breakdown)] = 0
#
#     colors = ['#8e7cc3ff', '#93c47dff']
#     xticks = []
#     for i in range(0, len(benchmarks)):
#         for j in range(0, len(schemes)):
#             xticks.append(i * (len(schemes) + 1) + j)
#     data = [list(i) for i in zip(*norm_cycles_breakdown)]
#     data = np.array(data, dtype=np.float64)
#     hdls = barchart.draw(
#         ax,
#         data,
#         group_names=group_names,
#         entry_names=entry_names,
#         breakdown=True,
#         xticks=xticks,
#         width=0.8,
#         colors=colors,
#         legendloc='upper center',
#         legendncol=len(entry_names),
#         xticklabelfontsize=20,
#         xticklabelrotation=90,
#         log=False)
#
#     ax.set_ylabel(ylabel)
#     ax.yaxis.grid(True, linestyle='--')
#     fmt.resize_ax_box(ax, hratio=0.95)
#     ly = len(benchmarks)
#     scale = 1. / ly
#     ypos = -0.34
#     for pos in range(ly + 1):
#         lxpos = (pos + 0.5) * scale
#         if pos < ly:
#             ax.text(
#                 lxpos, ypos, xlabels[pos], ha='center', transform=ax.transAxes)
#         add_line(ax, pos * scale, ypos)
#     temp_legend = ax.get_legend()
#     ax.get_legend().remove()
#     ax.tick_params(axis='both')
#     return temp_legend

# def get_power_numbers(folder_path, schemes, total_nodes, names, folder_names):
#     # benchmarks = ['AlphaGoZero', 'Googlenet', 'inceptionv4', 'NCF_recommendation',
#     #               'densenet161', 'densenet169', 'densenet201', 'resnet50',
#     #               'resnet101', 'vgg16', 'vgg19', 'Resnet152', 'Transformer']
#     # entry_names = ['Router', 'Links']
#     # xlabels = ['AlphaGoZero', 'GoogLeNet', 'InceptionV4', 'NCF', 'DenseNet161',
#     #            'DenseNet169', 'DenseNet201', 'ResNet50', 'ResNet101', 'ResNet152', 'VGG16', 'VGG19', 'Transformer']
#     benchmarks = ['AlphaGoZero', 'Googlenet', 'inceptionv4', 'NCF_recommendation', 'densenet201', 'Resnet152']
#     entry_names = ['Router', 'Links']
#     xlabels = ['AlphaGoZero', 'GoogLeNet', 'InceptionV4', 'NCF', 'DenseNet201', 'ResNet152']
#     group_names = []
#
#     cycles = np.zeros(
#         (int(len(schemes)), int(len(benchmarks))), dtype=float)
#     cycles_breakdown = np.zeros((2, int(len(benchmarks) * len(schemes))), dtype=float)
#     norm_cycles_breakdown = np.zeros((2, int(len(benchmarks) * len(schemes))), dtype=float)
#     link_energy_per_bit = 1.75e-12
#     freq = 1e9
#
#     for b, bench in enumerate(benchmarks):
#         five_port_router_static_power = None
#         for s, name in enumerate(names):
#             if name == 'mesh_overlap_2d_1':
#                 filename = "%s/%s/%s_%s_%d_mesh_%s_express_ar.json" % (folder_path, folder_names[s], bench, name, total_nodes, bench)
#             else:
#                 filename = "%s/%s/%s_%s_%d_%s_%s_express_ar.json" % (folder_path, folder_names[s], bench, name, total_nodes, name, bench)
#
#             if os.path.exists(filename):
#                 # print(filename)
#                 with open(filename, 'r') as json_file:
#                     sim = json.load(json_file)
#                     total_ar_cycles = sim['results']['performance']['allreduce']['total']
#                     total_router_dynamic_power = sim['results']['power']['network']['router']['dynamic']
#                     total_router_static_power = sim['results']['power']['network']['router']['static']
#                     if name == 'fatmesh_all':
#                         six_port_router_static_power = total_router_static_power / total_nodes
#                         total_router_static_power = 16 * six_port_router_static_power + 20 * five_port_router_static_power
#                     total_flits = sim['results']['power']['network']['link']['flits']
#                     total_bits = total_flits * 2048 # Per flit 4096 bits
#                     total_link_dynamic_power = (total_bits * link_energy_per_bit) / (total_ar_cycles/freq)
#                     if name == 'mesh_overlap_2d_1':
#                         five_port_router_static_power = total_router_static_power / total_nodes
#                     cycles[s][b] = total_router_dynamic_power + total_router_static_power + total_link_dynamic_power
#                     cycles_breakdown[1][b * len(schemes) + s] = total_link_dynamic_power
#                     cycles_breakdown[0][b * len(schemes) + s] = total_router_dynamic_power + total_router_static_power
#                     json_file.close()
#             else:
#                 print(filename)
#                 cycles_breakdown[0][b * len(schemes) + s] = 1
#                 cycles_breakdown[1][b * len(schemes) + s] = 1
#
#     for b, bench in enumerate(benchmarks):
#         for s, name in enumerate(names):
#             group_names.append(schemes[s])
#             for e, entry in enumerate(entry_names):
#                 norm_cycles_breakdown[e][b * len(schemes) + s] = cycles_breakdown[e][b * len(schemes) + s] / cycles[0][
#                     b]
#     norm_cycles_breakdown[np.isnan(norm_cycles_breakdown)] = 0
#
#     for s, name in enumerate(names):
#         if s is not 0:
#             lowest_power = 1000
#             highest_power = 0
#             for b, bench in enumerate(benchmarks):
#                 extra_power = cycles[s][b] / cycles[0][b]
#                 if extra_power < lowest_power:
#                     lowest_power = extra_power
#                 if extra_power > highest_power:
#                     highest_power = extra_power
#             print("Name: " + str(name) + ", Lowest power: " + str(lowest_power) + ", Highest power: " + str(highest_power))

def draw_graph_power(ax, folder_path, schemes, total_nodes, names, folder_names, ylabel):
    # benchmarks = ['AlphaGoZero', 'Googlenet', 'inceptionv4', 'NCF_recommendation',
    #               'densenet161', 'densenet169', 'densenet201', 'resnet50',
    #               'resnet101', 'vgg16', 'vgg19', 'Resnet152', 'Transformer']
    # entry_names = ['Router', 'Links']
    # xlabels = ['AlphaGoZero', 'GoogLeNet', 'InceptionV4', 'NCF', 'DenseNet161',
    #            'DenseNet169', 'DenseNet201', 'ResNet50', 'ResNet101', 'ResNet152', 'VGG16', 'VGG19', 'Transformer']
    benchmarks = ['AlphaGoZero', 'Googlenet', 'inceptionv4', 'NCF_recommendation', 'densenet201', 'Resnet152']
    entry_names = ['Router (Static)', 'Router (Dynamic)', 'Links (Static)', 'Links (Dynamic)']
    xlabels = ['AlphaGoZero', 'GoogLeNet', 'InceptionV4', 'NCF', 'DenseNet201', 'ResNet152']
    group_names = []

    cycles = np.zeros(
        (int(len(schemes)), int(len(benchmarks))), dtype=float)
    cycles_breakdown = np.zeros((4, int(len(benchmarks) * len(schemes))), dtype=float)
    norm_cycles_breakdown = np.zeros((4, int(len(benchmarks) * len(schemes))), dtype=float)
    link_energy_per_bit = 1.75e-12
    freq = 1e9
    total_imagenet_data = 1281167
    six_port_router_static_power = 0.5799568550547138
    five_port_router_static_power = 0.4776815224405175
    link_static_power = 0.20110108262399928

    for b, bench in enumerate(benchmarks):
        # five_port_router_static_power = None
        for s, name in enumerate(names):
            filename = "%s/%s/%s_pipeline_%d_%s_%s_express_128_AR.json" % (folder_path, folder_names[s], bench, total_nodes, folder_names[s], bench)

            if os.path.exists(filename):
                # print(filename)
                with open(filename, 'r') as json_file:
                    sim = json.load(json_file)
                    # if name == 'mesh':
                    #     total_iteration = math.ceil(total_imagenet_data / ((total_nodes - 1) * 16))
                    # else:
                    total_iteration = math.ceil(total_imagenet_data / (total_nodes * 16))
                    total_ar_cycles = sim['results']['performance']['allreduce']['total']
                    total_router_dynamic_power = sim['results']['power']['network']['router']['dynamic']
                    # total_router_static_power = sim['results']['power']['network']['router']['static']
                    if name == 'sm_bi':
                        # six_port_router_static_power = total_router_static_power / total_nodes
                        total_router_static_power = 16 * six_port_router_static_power + 20 * five_port_router_static_power
                    else:
                        total_router_static_power = 36 * five_port_router_static_power
                    if name == 'mesh':
                        total_links = 120
                    elif name == 'sm_bi':
                        total_links = 160
                    elif name == 'sm_uni':
                        total_links = 140
                    else:
                        total_links = 144
                    total_flits = sim['results']['power']['network']['link']['flits']
                    # print(filename)
                    # print(total_flits)
                    total_bits = total_flits * 2048 # Per flit 2048 bits
                    total_link_dynamic_power = (total_bits * link_energy_per_bit)
                    # print(total_link_dynamic_power)
                    # if name == 'mesh':
                    #     five_port_router_static_power = total_router_static_power / total_nodes
                    cycles[s][b] = total_router_dynamic_power * (total_ar_cycles/freq) * total_iteration + total_router_static_power + total_link_dynamic_power * total_iteration + link_static_power * total_links
                    cycles_breakdown[3][b * len(schemes) + s] = total_link_dynamic_power * total_iteration
                    cycles_breakdown[2][b * len(schemes) + s] = link_static_power * total_links
                    cycles_breakdown[1][b * len(schemes) + s] = total_router_dynamic_power * (total_ar_cycles/freq) * total_iteration
                    cycles_breakdown[0][b * len(schemes) + s] = total_router_static_power
                    # print("Topology " + str(name) + " Bench " + str(bench) + " Link static energy " + str())
                    # print(str(bench) + " " + str(name) + " " + str(total_router_static_power) + " " + str(total_router_dynamic_power * (total_ar_cycles/freq) * total_iteration) + " " + str(total_link_dynamic_power * total_iteration))
                    json_file.close()
            else:
                print(filename)
                cycles_breakdown[0][b * len(schemes) + s] = 1
                cycles_breakdown[1][b * len(schemes) + s] = 1

    for b, bench in enumerate(benchmarks):
        for s, name in enumerate(names):
            group_names.append(schemes[s])
            for e, entry in enumerate(entry_names):
                norm_cycles_breakdown[e][b * len(schemes) + s] = cycles_breakdown[e][b * len(schemes) + s] / cycles[0][b]
                # norm_cycles_breakdown[e][b * len(schemes) + s] = cycles_breakdown[e][b * len(schemes) + s]
    norm_cycles_breakdown[np.isnan(norm_cycles_breakdown)] = 0

    for s, name in enumerate(names):
        if s is not 0:
            lowest_power = 1000
            highest_power = 0
            for b, bench in enumerate(benchmarks):
                extra_power = cycles[s][b] / cycles[0][b]
                if extra_power < lowest_power:
                    lowest_power = extra_power
                if extra_power > highest_power:
                    highest_power = extra_power
            print("Name: " + str(name) + ", Lowest power: " + str(lowest_power) + ", Highest power: " + str(highest_power))

    colors = ['#2071f5', '#9cbff7', '#824479', '#a67ca0']
    xticks = []
    for i in range(0, len(benchmarks)):
        for j in range(0, len(schemes)):
            xticks.append(i * (len(schemes) + 1) + j)
    data = [list(i) for i in zip(*norm_cycles_breakdown)]
    data = np.array(data, dtype=np.float64)
    hdls = barchart.draw(
        ax,
        data,
        group_names=group_names,
        entry_names=entry_names,
        breakdown=True,
        xticks=xticks,
        width=0.8,
        colors=colors,
        legendloc='upper center',
        legendncol=len(entry_names),
        xticklabelfontsize=20,
        xticklabelrotation=90,
        log=False)

    ax.set_ylabel(ylabel)
    ax.yaxis.grid(True, linestyle='--')
    fmt.resize_ax_box(ax, hratio=0.95)
    ly = len(benchmarks)
    scale = 1. / ly
    ypos = -0.34
    for pos in range(ly + 1):
        lxpos = (pos + 0.5) * scale
        if pos < ly:
            ax.text(
                lxpos, ypos, xlabels[pos], ha='center', transform=ax.transAxes)
        add_line(ax, pos * scale, ypos)
    temp_legend = ax.get_legend()
    ax.get_legend().remove()
    ax.tick_params(axis='both')
    return temp_legend


def main():
    plt.rcParams["figure.figsize"] = [12.0, 5.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 1)
    # figure.subplots_adjust(top=1.3)

    folder_path = '{}/micro_2025/models'.format(os.environ['SIMHOME'])
    schemes = ['Mesh', '$SM_{Bi}$', '$SM_{Alter}$']
    names = ['mesh', 'sm_bi', 'sm_alter']
    folder_names = ['mesh', 'SM_Bi', 'SM_Alter']
    scalesim_config = 'express'
    # legend = draw_graph_power(ax1[0], folder_path, schemes, 36, names, folder_names, 'Power')
    # get_power_numbers(folder_path, schemes, 36, names, folder_names)
    legend = draw_graph_power(ax1, folder_path, schemes, 36, names, folder_names, 'Normalized Power')

    # legend = draw_graph(ax1, folder_path, odd_names, 81, schemes_odds, folder_names)

    # lines_labels = [ax1.get_legend_handles_labels()]
    labels = [] if legend is None else [str(x._text) for x in legend.texts]
    handles = [] if legend is None else legend.legendHandles
    # handles.append(lines_labels[0][0][0])
    # labels.append(lines_labels[0][1][0])
    figure.legend(handles, labels, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.06))
    figure.savefig('models_total_power_updated.pdf', bbox_inches='tight')



if __name__ == '__main__':

    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
