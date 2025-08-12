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
        [xpos, xpos],
        [0, ypos],
        transform=ax.transAxes,
        color='black',
        linewidth=1)
    line.set_clip_on(False)
    ax.add_line(line)


def draw_energy_or_power(ax, folder_path, schemes, total_nodes, names, folder_names, ylabel, type, exp_type='power_energy'):
    data_sizes = ['524288', '8388608', '33554432']
    entry_names = ['Router (Static)', 'Router (Dynamic)', 'Links (Static)', 'Links (Dynamic)']
    # xlabels = ['AlphaGoZero', 'GoogLeNet', 'InceptionV4', 'NCF', 'DenseNet201', 'ResNet152']
    xlabels = ['2 MB', '32 MB', '128 MB']
    assert len(data_sizes) == len(xlabels)

    group_names = []
    total_requirement = np.zeros((int(len(schemes)), int(len(data_sizes))), dtype=float)
    requirement_breakdown = np.zeros((len(entry_names), int(len(data_sizes) * len(schemes))), dtype=float)
    norm_requirement_breakdown = np.zeros((len(entry_names), int(len(data_sizes) * len(schemes))), dtype=float)
    freq = 1e9
    link_energy_per_bit = 1.75e-12
    six_port_router_static_power = 0.5799568550547138
    five_port_router_static_power = 0.4776815224405175

    link_energy_per_bit_kite = link_energy_per_bit * 2.8
    link_energy_per_bit_kite_medium = link_energy_per_bit * 4
    link_energy_per_bit_cmesh = link_energy_per_bit * 2
    link_energy_per_bit_folded_torus = link_energy_per_bit * 2
    link_energy_per_bit_dbutterfly = link_energy_per_bit * 4.45

    for d, data_size in enumerate(data_sizes):
        for s, name in enumerate(names):
            if name == 'mesh':
                filename = "%s/%s/bw_%s_tacos_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data_size, total_nodes, folder_names[s])
            elif name == 'sm_alter':
                filename = "%s/%s/bw_%s_pipeline_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data_size, total_nodes, folder_names[s])
            elif name == 'sm_bi':
                filename = "%s/%s/bw_%s_pipeline_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data_size, total_nodes, folder_names[s])
            elif name == 'folded_torus':
                filename = "%s/%s/bw_%s_tacos_64_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], data_size, folder_names[s])
            elif name == 'cmesh' or name == 'kite' or name == 'kite_medium' or name == 'dbutterfly':
                # When we use concentration, each node sends 4 times data to the neighbors. However, 4 nodes in the
                # concentration needs to use the same router. Also, we are only using concentration to reduce number of
                # routers and links, but 64 nodes are actually using for collective. So, compared to 8x8, in 4x4 each
                # router in the concentration needs to send 16 times more data. So, for fair comparison, we should
                # multiply the data_size with 4 so that after dividing by 16, each router in the 4x4 topology sends 16
                # times compared to 8x8 topology.
                updated_data_size = str(int(data_size) * 4)
                filename = "%s/%s/bw_%s_tacos_16_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], updated_data_size, folder_names[s])
            else:
                raise RuntimeError("Wrong topology")

            if os.path.exists(filename):
                with open(filename, 'r') as json_file:
                    sim = json.load(json_file)
                    total_ar_cycles = sim['results']['performance']['allreduce']['total']
                    required_time = (total_ar_cycles / freq)
                    # print("Required time " + str(required_time))

                    # Router Static Power
                    dimension = int(math.sqrt(total_nodes))
                    if name == 'sm_bi':
                        assert total_nodes == 16 or total_nodes == 64
                        six_port_routers = 4 * (dimension - 2)
                        five_port_routers = total_nodes - six_port_routers
                        total_router_static_power = six_port_routers * six_port_router_static_power + five_port_routers * five_port_router_static_power
                    elif name == 'cmesh' or name == 'kite' or name == 'kite_medium' or name == 'dbutterfly':
                        # TODO: Consider 8 port router for cmesh, kite, kite_medium and dbutterfly.
                        total_router_static_power = 16 * five_port_router_static_power
                    else:
                        total_router_static_power = total_nodes * five_port_router_static_power
                    total_router_static_energy = total_router_static_power * required_time

                    # Router Dynamic Power
                    total_router_dynamic_power = sim['results']['power']['network']['router']['dynamic']
                    total_router_dynamic_energy = total_router_dynamic_power * required_time

                    # Link Static Power
                    if name == 'cmesh' or name == 'kite' or name == 'kite_medium' or name == 'dbutterfly':
                        # Here we get static power for all the inject and eject channels of 16 nodes.
                        per_link_static_power = (sim['results']['power']['network']['link']['static'])/32
                    else:
                        per_link_static_power = (sim['results']['power']['network']['link']['static']) / (2 * total_nodes)
                    if name == 'mesh':
                        total_links = 2 * dimension * (dimension - 1) * 2
                        total_link_static_power = per_link_static_power * total_links
                        total_link_static_power += per_link_static_power * (2 * total_nodes) # For inject and eject channels
                    elif name == 'sm_bi':
                        total_links = 2 * dimension * (dimension - 1) * 2 + 4 * (dimension - 1) * 2
                        total_link_static_power = per_link_static_power * total_links
                        total_link_static_power += per_link_static_power * (2 * total_nodes)  # For inject and eject channels
                    elif name == 'sm_alter':
                        total_links = 2 * dimension * (dimension - 1) * 2 + 4 * (dimension // 2) * 2
                        total_link_static_power = per_link_static_power * total_links
                        total_link_static_power += per_link_static_power * (2 * total_nodes)  # For inject and eject channels
                    elif name == 'cmesh':
                        total_links = 48
                        total_link_static_power = per_link_static_power * total_links * 2 # As links are 2 times longer
                        total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                    elif name == 'dbutterfly':
                        total_links = 48
                        total_link_static_power = per_link_static_power * total_links * 4.45 # As links are 4.45 times longer
                        total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                    elif name == 'folded_torus':
                        total_links = 256
                        total_link_static_power = per_link_static_power * total_links * 2 # As links are 2 times longer
                        total_link_static_power += per_link_static_power * (2 * total_nodes)  # For inject and eject channels
                    elif name == 'kite':
                        total_links = 60
                        total_link_static_power = per_link_static_power * total_links * 2.8 # As links are 2.8 times longer
                        total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                    elif name == 'kite_medium':
                        total_links = 60
                        total_link_static_power = per_link_static_power * total_links * 4 # As links are 4 times longer
                        total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                    else:
                        raise RuntimeError("Wrong topology")
                    total_link_static_energy = total_link_static_power * required_time

                    total_flits = sim['results']['power']['network']['link']['flits']
                    total_bits = total_flits * 2048 # Per flit 2048 bits
                    if name == 'kite':
                        total_link_dynamic_energy = (total_bits * link_energy_per_bit_kite)
                    elif name == 'kite_medium':
                        total_link_dynamic_energy = (total_bits * link_energy_per_bit_kite_medium)
                    elif name == 'cmesh':
                        total_link_dynamic_energy = (total_bits * link_energy_per_bit_cmesh)
                    elif name == 'folded_torus':
                        total_link_dynamic_energy = (total_bits * link_energy_per_bit_folded_torus)
                    elif name == 'dbutterfly':
                        total_link_dynamic_energy = (total_bits * link_energy_per_bit_dbutterfly)
                    else:
                        total_link_dynamic_energy = (total_bits * link_energy_per_bit)
                    total_link_dynamic_power = int(total_link_dynamic_energy / required_time)

                    if type == 'energy':
                        total_requirement[s][d] = total_router_static_energy + total_router_dynamic_energy + total_link_static_energy + total_link_dynamic_energy
                        requirement_breakdown[3][d * len(schemes) + s] = total_link_dynamic_energy
                        requirement_breakdown[2][d * len(schemes) + s] = total_link_static_energy
                        requirement_breakdown[1][d * len(schemes) + s] = total_router_dynamic_energy
                        requirement_breakdown[0][d * len(schemes) + s] = total_router_static_energy
                    else:
                        total_requirement[s][d] = total_router_static_power + total_router_dynamic_power + total_link_static_power + total_link_dynamic_power
                        requirement_breakdown[3][d * len(schemes) + s] = total_link_dynamic_power
                        requirement_breakdown[2][d * len(schemes) + s] = total_link_static_power
                        requirement_breakdown[1][d * len(schemes) + s] = total_router_dynamic_power
                        requirement_breakdown[0][d * len(schemes) + s] = total_router_static_power
                        json_file.close()
            else:
                print(filename)
                requirement_breakdown[0][d * len(schemes) + s] = 1
                requirement_breakdown[1][d * len(schemes) + s] = 1

    for d, data_size in enumerate(data_sizes):
        for s, name in enumerate(names):
            group_names.append(schemes[s])
            for e, entry in enumerate(entry_names):
                norm_requirement_breakdown[e][d * len(schemes) + s] = requirement_breakdown[e][d * len(schemes) + s] / total_requirement[0][d]
    norm_requirement_breakdown[np.isnan(norm_requirement_breakdown)] = 0

    # for s, name in enumerate(names):
    #     if s is not 7:
    #         lowest = 100000000000
    #         highest = 0
    #         for d, data_size in enumerate(data_sizes):
    #             extra = total_requirement[s][d] / total_requirement[7][d]
    #             if extra < lowest:
    #                 lowest = extra
    #             if extra > highest:
    #                 highest = extra
    #         if type == 'power':
    #             print("Name: " + str(name) + ", Lowest power: " + str(lowest) + ", Highest power: " + str(highest))
    #         else:
    #             print("Name: " + str(name) + ", Lowest energy: " + str(lowest) + ", Highest energy: " + str(highest))

    colors = ['#2071f5', '#9cbff7', '#824479', '#a67ca0']
    xticks = []
    for i in range(0, len(data_sizes)):
        for j in range(0, len(schemes)):
            xticks.append(i * (len(schemes) + 1) + j)
    data = [list(i) for i in zip(*norm_requirement_breakdown)]
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
    ly = len(data_sizes)
    scale = 1. / ly
    if exp_type == 'power_energy':
        ypos = -0.34
    else:
        ypos = -0.5
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
    exp_types = ["all_energy", "power_energy"]
    for exp_type in exp_types:
        if exp_type == "power_energy":
            plt.rcParams["figure.figsize"] = [12.0, 5.0]
            plt.rcParams["figure.autolayout"] = True
            figure, ax1 = plt.subplots(1, 2)
            total_nodes = 64

            folder_path = '{}/micro_2025/bandwidth'.format(os.environ['SIMHOME'])
            schemes = ['Mesh', '$SM_{Bi}$', '$SM_{Alter}$']
            names = ['mesh', 'sm_bi', 'sm_alter']
            folder_names = ['mesh', 'SM_Bi', 'SM_Alter']
            legend = draw_energy_or_power(ax1[0], folder_path, schemes, total_nodes, names, folder_names, 'Normalized Power', 'power')
            legend = draw_energy_or_power(ax1[1], folder_path, schemes, total_nodes, names, folder_names, 'Normalized Energy', 'energy')

            labels = [] if legend is None else [str(x._text) for x in legend.texts]
            handles = [] if legend is None else legend.legendHandles
            figure.legend(handles, labels, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.06))
            figure.savefig('fig_14_data_size_power_energy_' + str(total_nodes) + '.pdf', bbox_inches='tight')
        elif exp_type == 'all_energy':
            plt.rcParams["figure.figsize"] = [12.0, 5.0]
            plt.rcParams["figure.autolayout"] = True
            figure, ax1 = plt.subplots(1, 1)
            total_nodes = 64

            folder_path = '{}/micro_2025/bandwidth'.format(os.environ['SIMHOME'])
            schemes = ['Mesh', 'CMesh', 'DB', 'Kite(S)', 'Kite(M)', 'FT', '$SM_{Alter}$', '$SM_{Bi}$']
            names = ['mesh', 'cmesh', 'dbutterfly', 'kite', 'kite_medium', 'folded_torus', 'sm_bi', 'sm_alter']
            folder_names = ['mesh', 'cmesh', 'dbutterfly', 'kite', 'kite_medium', 'folded_torus', 'SM_Bi', 'SM_Alter']
            legend = draw_energy_or_power(ax1, folder_path, schemes, total_nodes, names, folder_names,
                                          'Normalized Energy', 'energy', exp_type)

            labels = [] if legend is None else [str(x._text) for x in legend.texts]
            handles = [] if legend is None else legend.legendHandles
            figure.legend(handles, labels, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.06))
            figure.savefig('fig_15_data_size_all_topo_energy_' + str(total_nodes) + '.pdf', bbox_inches='tight')
        else:
            raise RuntimeError("Wrong exp type")



if __name__ == '__main__':
    main()
