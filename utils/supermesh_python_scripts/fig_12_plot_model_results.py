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
plt.rcParams['font.size'] = 17


def add_line(ax, xpos, ypos):
    line = plt.Line2D(
        [xpos, xpos],
        [0, ypos],
        transform=ax.transAxes,
        color='black',
        linewidth=1)
    line.set_clip_on(False)
    ax.add_line(line)
    # ax.legend("AR Speedup")

def get_training_time():
    # All the numbers from 'micro_2025/models/compute'
    training_time = {}
    training_time['bs_256_vaults_16_array_128'] = {}
    training_time['bs_256_vaults_16_array_128']['AlphaGoZero'] = 102547
    training_time['bs_256_vaults_16_array_128']['alexnet'] = 9927124
    training_time['bs_256_vaults_16_array_128']['densenet121'] = 497899
    training_time['bs_256_vaults_16_array_128']['densenet161'] = 1311843
    training_time['bs_256_vaults_16_array_128']['densenet169'] = 689528
    training_time['bs_256_vaults_16_array_128']['densenet201'] = 864190
    training_time['bs_256_vaults_16_array_128']['inceptionv3'] = 1271729
    training_time['bs_256_vaults_16_array_128']['inceptionv4'] = 2093041
    training_time['bs_256_vaults_16_array_128']['NCF_recommendation'] = 1197354
    training_time['bs_256_vaults_16_array_128']['resnet50'] = 728986
    training_time['bs_256_vaults_16_array_128']['resnet101'] = 1204391
    training_time['bs_256_vaults_16_array_128']['Resnet152'] = 4203243
    training_time['bs_256_vaults_16_array_128']['Transformer'] = 3195439
    training_time['bs_256_vaults_16_array_128']['vgg13'] = 715059
    training_time['bs_256_vaults_16_array_128']['vgg16'] = 843253
    training_time['bs_256_vaults_16_array_128']['vgg19'] = 971447
    folder_path = '{}/micro_2025/models/compute'.format(os.environ['SIMHOME'])
    models = ['alexnet', 'AlphaGoZero', 'NCF_recommendation', 'inceptionv4', 'densenet121', 'densenet161', 'densenet169',
              'densenet201', 'resnet50', 'resnet101', 'Resnet152', 'vgg16', 'vgg19', 'Transformer']
    # (bs, vaults, array)
    configs = [(256, 16, 32), (1, 1, 128), (2, 1, 128), (4, 1, 128), (16, 1, 128)]
    config_names = ['bs_256_vaults_16_array_32', 'bs_16_vaults_1_array_128', 'bs_32_vaults_1_array_128', 'bs_64_vaults_1_array_128', 'bs_256_vaults_1_array_128']
    for i in range(len(configs)):
        config = configs[i]
        config_name = config_names[i]
        training_time[config_name] = {}
        for model in models:
            if config[2] == 32:
                filename = "%s/compute_short_%d_b%d/json/%s_multitree_16_mesh_%s_express_Compute.json" % (folder_path, config[2], config[0], model, model)
            else:
                filename = "%s/compute_short_%d_b%d/json/%s_multitree_16_mesh_%s_express_128_Compute.json" % (folder_path,
                                                                                                          config[2],
                                                                                                          config[0],
                                                                                                          model, model)
            if os.path.exists(filename):
                with open(filename, 'r') as json_file:
                    sim = json.load(json_file)
                    training_time[config_name][model] = sim['results']['performance']['training']
                    json_file.close()
            else:
                print(filename)
    return training_time


def draw_graph(ax, folder_path, schemes, total_nodes, names, folder_names, exp_type, text_to_add):
    training_time = get_training_time()
    # training_time['Googlenet'] = 9400243 # Not done yet

    # benchmarks = ['alexnet', 'AlphaGoZero', 'NCF_recommendation', 'inceptionv4', 'densenet121',
    #               'densenet161', 'densenet169', 'densenet201', 'resnet50', 'resnet101', 'Resnet152', 'vgg16',
    #               'vgg19', 'Transformer']
    # benchmarks = ['alexnet', 'NCF_recommendation', 'inceptionv4', 'densenet201', 'Resnet152', 'vgg19', 'Transformer']
    benchmarks = ['inceptionv4', 'densenet201', 'Resnet152', 'vgg19']
    entry_names = ['Forward+Back-Propagation', 'AllReduce']
    # xlabels = ['AlexNet', 'AlphaGoZero', 'NCF', 'InceptionV4', 'DenseNet121', 'DenseNet161',
    #            'DenseNet169', 'DenseNet201', 'ResNet50', 'ResNet101', 'ResNet152', 'VGG16', 'VGG19',
    #            'Transformer']
    # xlabels = ['AlexNet', 'NCF', 'InceptionV4', 'DenseNet201', 'ResNet152', 'VGG19', 'Transformer']
    xlabels = ['InceptionV4', 'DenseNet201', 'ResNet152', 'VGG19']
    group_names = []

    cycles = np.zeros(
        (int(len(schemes)), int(len(benchmarks))), dtype=float)
    norm_cycles = np.zeros(
        (int(len(schemes)), int(len(xlabels))), dtype=float)
    norm_allreduce_cycles = np.zeros(
        (int(len(schemes)), int(len(xlabels))), dtype=float)
    training_cycles = np.zeros((int(len(schemes)), int(len(benchmarks))), dtype=float)
    allreduce_cycles = np.zeros((int(len(schemes)), int(len(benchmarks))), dtype=float)
    cycles_breakdown = np.zeros((2, int(len(benchmarks) * len(schemes))), dtype=float)
    norm_cycles_breakdown = np.zeros((2, int(len(benchmarks) * len(schemes))), dtype=float)
    total_imagenet_data = 1281167

    for s, name in enumerate(names):
        for b, bench in enumerate(benchmarks):
            filename = "%s/%s/%s_pipeline_%d_%s_%s_express_128_AR.json" % (folder_path, folder_names[s], bench, total_nodes, folder_names[s], bench)

            if os.path.exists(filename):
                with open(filename, 'r') as json_file:
                    sim = json.load(json_file)
                    if name == 'tto':
                        total_iteration = math.ceil(total_imagenet_data / ((total_nodes - 1) * 16))
                    else:
                        total_iteration = math.ceil(total_imagenet_data / (total_nodes * 16))
                    initial_ar_cycles = sim['results']['performance']['allreduce']['total']
                    allreduce_cycles[s][b] = initial_ar_cycles * total_iteration
                    training_cycles[s][b] = training_time[exp_type][bench] * total_iteration
                    cycles[s][b] = training_cycles[s][b] + allreduce_cycles[s][b]
                    norm_cycles[s][b] = cycles[s][b] / cycles[0][b]
                    norm_allreduce_cycles[s][b] = allreduce_cycles[s][b] / allreduce_cycles[0][b]
                    cycles_breakdown[1][b * len(schemes) + s] = allreduce_cycles[s][b]
                    cycles_breakdown[0][b * len(schemes) + s] = training_cycles[s][b]
                    json_file.close()
            else:
                print(filename)
                norm_cycles[s][b] = 1
                norm_allreduce_cycles[s][b] = 1
                cycles_breakdown[0][b * len(schemes) + s] = 1
                cycles_breakdown[1][b * len(schemes) + s] = 1

    speedup = 1.0 / norm_cycles
    allreduce_speedup = 1.0 / norm_allreduce_cycles
    speedup[np.isnan(speedup)] = 0
    allreduce_speedup[np.isnan(allreduce_speedup)] = 0

    for j in range(len(names)):
        lowest_speedup = 1000
        highest_speedup = 0
        for i in range(len(benchmarks)):
            if speedup.T[i][j] > highest_speedup:
                highest_speedup = speedup.T[i][j]
            if speedup.T[i][j] < lowest_speedup:
                lowest_speedup = speedup.T[i][j]
        print(str(names[j]) + ' ' + str(lowest_speedup) + ' ' + str(highest_speedup))

    for b, bench in enumerate(benchmarks):
        for s, name in enumerate(names):
            group_names.append(schemes[s])
            for e, entry in enumerate(entry_names):
                norm_cycles_breakdown[e][b * len(schemes) + s] = cycles_breakdown[e][b * len(schemes) + s] / cycles[0][
                    b]
    norm_cycles_breakdown[np.isnan(norm_cycles_breakdown)] = 0

    colors = ['#8e7cc3ff', '#93c47dff']
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

    for i in range(len(benchmarks)):
        xpos = []
        ypos = []
        for j in range(len(names)):
            ypos.append(speedup.T[i][j])
            xpos.append(i*len(names) + i + j)
            ax.plot(xpos, ypos, marker="o", linewidth=3, color='black', label='End-to-end Training Speedup')

    ax.set_ylabel('Normalized Runtime Breakdown')
    ax.yaxis.grid(True, linestyle='--')
    # ax.set_xlabel(text_to_add, y=-0.15)
    ax.annotate(text_to_add, xy=(0.5, -0.4), xycoords='axes fraction', ha='center')
    fmt.resize_ax_box(ax, hratio=0.95)
    ly = len(benchmarks)
    scale = 1. / ly
    ypos = -0.31
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
    # pdf.plot_teardown(pdfpage)

def main():
    # exp_types = ['bs_256_vaults_16_array_128', 'bs_256_vaults_16_array_32', 'bs_16_vaults_1_array_128', 'bs_32_vaults_1_array_128', 'bs_64_vaults_1_array_128', 'bs_256_vaults_1_array_128']
    # for exp_type in exp_types:
    plt.rcParams["figure.figsize"] = [15.00, 6.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 2)
    # figure.subplots_adjust(top=1.3)

    folder_path = '{}/micro_2025/models'.format(os.environ['SIMHOME'])
    schemes = ['TTO', '$SM_{Bi}$', '$SM_{Alter}$']
    names = ['tto', 'sm_bi', 'sm_alter']
    folder_names = ['mesh', 'SM_Bi', 'SM_Alter']
    scalesim_config = 'express'
    legend = draw_graph(ax1[0], folder_path, schemes, 36, names, folder_names, 'bs_256_vaults_16_array_128', 'Training time with 128x128 MAC array')
    legend = draw_graph(ax1[1], folder_path, schemes, 36, names, folder_names, 'bs_256_vaults_16_array_32', 'Training time with 32x32 MAC array')

    lines_labels = [ax1[0].get_legend_handles_labels()]
    labels = [] if legend is None else [str(x._text) for x in legend.texts]
    handles = [] if legend is None else legend.legendHandles
    handles.append(lines_labels[0][0][0])
    labels.append(lines_labels[0][1][0])
    figure.legend(handles, labels, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 1.06))
    figure.subplots_adjust(bottom=0.3)
    figure.savefig('fig_12_models_dnn_results.pdf', bbox_inches='tight')


if __name__ == '__main__':
    main()
