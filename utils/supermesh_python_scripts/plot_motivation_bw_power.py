import json
import math
import os

import matplotlib.pyplot as plt
import numpy as np
from easypyplot import barchart
from easypyplot import format as fmt

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 12

def get_energy_numbers(folder_path, schemes, names, folder_names, data_size, folder_path_2, ax1, type):
    # Ratio is from "Kite: A Family of Heterogeneous Interposer Topologies Enabled via Accurate Interconnect Modeling"
    link_energy_per_bit = 1.75e-12
    link_energy_per_bit_kite = 1.75e-12 * 2.8
    link_energy_per_bit_kite_medium = 1.75e-12 * 4
    link_energy_per_bit_cmesh = 1.75e-12 * 2
    link_energy_per_bit_folded_torus = 1.75e-12 * 2
    link_energy_per_bit_dbutterfly = 1.75e-12 * 4.45
    link_static_power = 0.20110108262399928
    link_static_power_kite = 0.20110108262399928 * 2.8
    link_static_power_kite_medium = 0.20110108262399928 * 4
    link_static_power_cmesh = 0.20110108262399928 * 2
    link_static_power_folded_torus = 0.20110108262399928 * 2
    link_static_power_dbutterfly = 0.20110108262399928 * 4.45
    five_port_router_static_power = 0.4776815224405175
    freq = 1e9
    bandwidths = []
    link_energy = []
    bandwidth_per_energy = []

    for s, name in enumerate(names):
        if name == 'cmesh' or name == 'kite' or name == 'kite_medium' or name == 'dbutterfly':
            total_nodes = 16
        else:
            total_nodes = 64

        if name == 'mesh':
            filename = "%s/%s/bw_%d_tacos_64_%s_alexnet_express_128_AR.json" % (
            folder_path_2, folder_names[s], data_size, folder_names[s])
        elif name == 'folded_torus':
            filename = "%s/%s/bw_%d_tacos_64_%s_alexnet_express_128_AR.json" % (
            folder_path_2, folder_names[s], data_size, folder_names[s])
        elif name == 'sm_alter':
            filename = "%s/%s/bw_%d_pipeline_64_%s_alexnet_express_128_AR.json" % (
            folder_path_2, folder_names[s], data_size, folder_names[s])
        elif name == 'cmesh' or name == 'kite' or name == 'kite_medium' or name == 'dbutterfly':
            # When we use concentration, each node sends 4 times data to the neighbors. However, 4 nodes in the
            # concentration needs to use the same router. Also, we are only using concentration to reduce number of
            # routers and links, but 64 nodes are actually using for collective. So, compared to 8x8, in 4x4 each
            # router in the concentration needs to send 16 times more data. So, for fair comparison, we should
            # multiply the data_size with 4 so that after dividing by 16, each router in the 4x4 topology sends 16
            # times compared to 8x8 topology.
            updated_data_size = data_size * 4
            filename = "%s/%s/bw_%d_tacos_16_%s_alexnet_express_128_AR.json" % (
            folder_path_2, folder_names[s], updated_data_size, folder_names[s])
        else:
            raise RuntimeError("Wrong topology")

        if os.path.exists(filename):
            with open(filename, 'r') as json_file:
                sim = json.load(json_file)
                total_ar_cycles = sim['results']['performance']['allreduce']['total']
                required_time = (total_ar_cycles / freq)
                dimension = int(math.sqrt(total_nodes))

                # TODO: Incorporate eight port router static power
                total_router_static_power = total_nodes * five_port_router_static_power
                total_router_static_energy = total_router_static_power * required_time

                # Router Dynamic Power
                total_router_dynamic_power = sim['results']['power']['network']['router']['dynamic']
                total_router_dynamic_energy = total_router_dynamic_power * required_time

                # Link Static Power
                # Link Static Power
                if name == 'cmesh' or name == 'kite' or name == 'kite_medium' or name == 'dbutterfly':
                    # Here we get static power for all the inject and eject channels of 16 nodes.
                    per_link_static_power = (sim['results']['power']['network']['link']['static']) / 32
                else:
                    per_link_static_power = (sim['results']['power']['network']['link']['static']) / 128
                if name == 'mesh':
                    total_links = 2 * dimension * (dimension - 1) * 2
                    total_link_static_power = per_link_static_power * total_links
                    total_link_static_power += per_link_static_power * 128  # For inject and eject channels
                elif name == 'sm_bi':
                    total_links = 2 * dimension * (dimension - 1) * 2 + 4 * (dimension - 1) * 2
                    total_link_static_power = per_link_static_power * total_links
                    total_link_static_power += per_link_static_power * 128  # For inject and eject channels
                elif name == 'sm_alter':
                    total_links = 2 * dimension * (dimension - 1) * 2 + 4 * (dimension // 2) * 2
                    total_link_static_power = per_link_static_power * total_links
                    total_link_static_power += per_link_static_power * 128  # For inject and eject channels
                elif name == 'cmesh':
                    total_links = 48
                    total_link_static_power = per_link_static_power * total_links * 2  # As links are 2 times longer
                    total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                elif name == 'dbutterfly':
                    total_links = 48
                    total_link_static_power = per_link_static_power * total_links * 4.45  # As links are 4.45 times longer
                    total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                elif name == 'folded_torus':
                    total_links = 256
                    total_link_static_power = per_link_static_power * total_links * 2  # As links are 2 times longer
                    total_link_static_power += per_link_static_power * 128  # For inject and eject channels
                elif name == 'kite':
                    total_links = 60
                    total_link_static_power = per_link_static_power * total_links * 2.8  # As links are 2.8 times longer
                    total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                elif name == 'kite_medium':
                    total_links = 60
                    total_link_static_power = per_link_static_power * total_links * 4  # As links are 4 times longer
                    total_link_static_power += per_link_static_power * 32  # For inject and eject channels
                else:
                    raise RuntimeError("Wrong topology")
                total_link_static_energy = total_link_static_power * required_time

                total_flits = sim['results']['power']['network']['link']['flits']
                total_bits = total_flits * 2048  # Per flit 2048 bits

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
                total_energy = total_router_static_energy + total_router_dynamic_energy + total_link_static_energy + total_link_dynamic_energy

                bw = (float(data_size * 4) / (1024 * 1024 * 1024)) / (total_ar_cycles / (10 ** 9))
                bandwidths.append(bw)
                link_energy.append(total_energy)
                bandwidth_per_energy.append(bw / total_energy)
                json_file.close()
        else:
            print(name)
            print(filename)


    print("Mesh energy " + str(link_energy[0]) + ", bandwidths: " + str(bandwidths[0]) + ", Bandwidth per joule link: " + str(bandwidth_per_energy[0]))
    print("CMesh energy " + str(link_energy[1]) + ", bandwidths: " + str(bandwidths[1]) + ", Bandwidth per joule link: " + str(bandwidth_per_energy[1]))
    print("DbutterFly energy " + str(link_energy[2]) + ", bandwidths: " + str(bandwidths[2]) + ", Bandwidth per joule link: " + str(bandwidth_per_energy[2]))
    print("Kite Small energy " + str(link_energy[3]) + ", bandwidths: " + str(bandwidths[3]) + ", Bandwidth per joule link: " + str(bandwidth_per_energy[3]))
    print("Kite Medium energy " + str(link_energy[4]) + ", bandwidths: " + str(bandwidths[4]) + ", Bandwidth per joule link: " + str(bandwidth_per_energy[4]))
    print("Supermesh energy " + str(link_energy[5]) + ", bandwidths: " + str(bandwidths[5]) + ", Bandwidth per joule link: " + str(bandwidth_per_energy[5]))

    normalized_bw = [bandwidths[i]/bandwidths[0] for i in range(len(bandwidths))]
    normalized_bandwidth_per_energy = [bandwidth_per_energy[i]/bandwidth_per_energy[0] for i in range(len(bandwidth_per_energy))]

    # corporate_colors = [
    #     '#F28E2B',  # Orange
    #     '#E15759',  # Coral Red
    #     '#76B7B2',  # Turquoise
    #     '#59A14F',  # Forest Green
    #     '#EDC948',  # Golden Yellow
    #     '#B07AA1',  # Dusty Purple
    #     '#FF9DA7',  # Soft Pink
    # ]
    #
    # # Option 2: Modern/Vibrant Colors
    # vibrant_colors = [
    #     '#2AB7CA',  # Bright Turquoise
    #     '#FED766',  # Bright Yellow
    #     '#FF6B6B',  # Bright Coral
    #     '#4ECDC4',  # Mint
    #     '#45B7D1',  # Sky Blue
    #     '#96CEB4',  # Sage Green
    #     '#D4A5A5',  # Dusty Rose
    #     '#9B5DE5',  # Bright Purple
    # ]
    #
    # # Option 3: Pastel Colors (still visible with black border)
    # pastel_colors = [
    #     '#A8E6CE',  # Mint Green
    #     '#DCEDC2',  # Light Green
    #     '#FFD3B5',  # Peach
    #     '#FFAAA6',  # Salmon
    #     '#FF8C94',  # Pink
    #     '#A8C0FF',  # Light Blue
    #     '#CAB1DE',  # Lavender
    #     '#B5EAD7',  # Sea Foam
    # ]

    plt.xticks(rotation=90)
    scheme_names = ['Mesh', 'Cmesh', 'DB', 'Kite(S)', 'Kite(M)', 'FT', '$\mathbf{SM}$']

    if type == 'bw':
        ax1.bar(scheme_names, bandwidths, color='#E15759', edgecolor='black', width=0.6)
        ax1.set_ylabel('Bandwidth (GB/s)')
        ax1.set_xticks(scheme_names)  # Set the tick positions
        ax1.set_xticklabels(scheme_names, rotation=90)  # Set the labels and rotate them
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        for i, v in enumerate(bandwidths):
            ax1.text(scheme_names[i], v + 0.8, f'{normalized_bw[i]:.2f}×', ha='center', va='bottom', rotation=90)
    else:
        ax1.bar(scheme_names, bandwidth_per_energy, color='#59A14F', edgecolor='black', width=0.6)
        ax1.set_ylabel('BW/Energy (GB/Js)')
        ax1.set_xticks(scheme_names)  # Set the tick positions
        ax1.set_xticklabels(scheme_names, rotation=90)  # Set the labels and rotate them
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        for i, v in enumerate(bandwidth_per_energy):
            ax1.text(scheme_names[i], v + 0.8, f'{normalized_bandwidth_per_energy[i]:.2f}×', ha='center', va='bottom', rotation=90)


def main():
    plt.rcParams["figure.figsize"] = [3.0, 3.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 1)
    figure2, ax2 = plt.subplots(1, 1)

    folder_path = '{}/micro_2025/motivation'.format(os.environ['SIMHOME'])
    folder_path_2 = '{}/micro_2025/bandwidth'.format(os.environ['SIMHOME'])
    schemes = ['mesh', 'cmesh', 'dbutterfly', 'kite', 'kite_medium', 'folded_torus', 'sm_alter']
    names = ['mesh', 'cmesh', 'dbutterfly', 'kite', 'kite_medium', 'folded_torus', 'sm_alter']
    folder_names = ['mesh', 'cmesh', 'dbutterfly', 'kite', 'kite_medium', 'folded_torus', 'SM_Alter']
    data_size = 33554432
    print("Energy Analysis")
    get_energy_numbers(folder_path, schemes, names, folder_names, data_size, folder_path_2, ax1, 'bw')
    figure.savefig('motivation_bw_tacos_updated.pdf', bbox_inches='tight')
    get_energy_numbers(folder_path, schemes, names, folder_names, data_size, folder_path_2, ax2, 'energy')
    figure2.savefig('motivation_energy_tacos_updated.pdf', bbox_inches='tight')



if __name__ == '__main__':

    # if len(sys.argv) != 2:
    #     print('usage: ' + sys.argv[0] + ' folder_path')
    #     exit()
    main()
