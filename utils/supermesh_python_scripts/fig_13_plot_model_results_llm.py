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
plt.rcParams['font.size'] = 18


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

def get_training_data():
    # Here we are using Device 16, Batch size 16 and Sequence Length 1024. Details can be found in model_simulation.log file. Here AR data is number of parameters where each parameter is 4B.
    # We use LLMCompass to get the compute time and data size. Then we use booksim to get communication time. LLMCompass results are in 'micro_2025/models/model_simulation.log'

    training_data = {}
    training_data['bloom176b'] = {}
    training_data['bloom176b']['training'] = 120910044
    training_data['bloom176b']['ar_data'] = 234881024
    training_data['gemma7b'] = {}
    training_data['gemma7b']['training'] = 15381314
    training_data['gemma7b']['ar_data'] = 50331648
    training_data['falcon40b'] = {}
    training_data['falcon40b']['training'] = 51574979
    training_data['falcon40b']['ar_data'] = 134217728
    training_data['llama405b'] = {}
    training_data['llama405b']['training'] = 143952001
    training_data['llama405b']['ar_data'] = 268435456
    training_data['gpt3'] = {}
    training_data['gpt3']['training'] = 93327644
    training_data['gpt3']['ar_data'] = 201326592
    training_data['qwen3'] = {}
    training_data['qwen3']['training'] = 30470250
    training_data['qwen3']['ar_data'] = 83886080
    return training_data


def draw_graph(ax, folder_path, schemes, total_nodes, names, folder_names, vaults):
    training_data = get_training_data()
    benchmarks = ['bloom176b', 'gemma7b', 'falcon40b', 'llama405b', 'gpt3', 'qwen3']
    entry_names = ['Compute Time', 'AllReduce Time']
    xlabels = ['BLOOM 176B', 'Gemma 7B', 'Falcon 40B', 'LLaMA 405B', 'GPT-3', 'Qwen3-32B']
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

    for s, name in enumerate(names):
        for b, bench in enumerate(benchmarks):
            training_time = training_data[bench]['training']
            ar_data = training_data[bench]['ar_data']
            filename = "%s/%s/vaults%d/json/bw_%d_pipeline_%d_%s_alexnet_express_128_AR.json" % (folder_path, folder_names[s], vaults, ar_data, total_nodes, folder_names[s])

            if os.path.exists(filename):
                with open(filename, 'r') as json_file:
                    sim = json.load(json_file)
                    ar_cycles = sim['results']['performance']['allreduce']['total']
                    allreduce_cycles[s][b] = ar_cycles
                    training_cycles[s][b] = training_time
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
            ax.plot(xpos, ypos, marker="o", linewidth=3, color='black', label='Inference Speedup')

    ax.set_ylabel('Normalized Runtime Breakdown')
    ax.yaxis.grid(True, linestyle='--')
    fmt.resize_ax_box(ax, hratio=0.95)
    ly = len(benchmarks)
    scale = 1. / ly
    ypos = -0.28
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
    plt.rcParams["figure.figsize"] = [13.00, 6.0]
    plt.rcParams["figure.autolayout"] = True
    figure, ax1 = plt.subplots(1, 1)
    vaults = 1

    folder_path = '{}/micro_2025/llm_models'.format(os.environ['SIMHOME'])
    schemes = ['TTO', '$SM_{Bi}$', '$SM_{Alter}$']
    names = ['tto', 'sm_bi', 'sm_alter']
    folder_names = ['mesh', 'SM_Bi', 'SM_Alter']
    legend = draw_graph(ax1, folder_path, schemes, 16, names, folder_names, vaults)

    lines_labels = [ax1.get_legend_handles_labels()]
    labels = [] if legend is None else [str(x._text) for x in legend.texts]
    handles = [] if legend is None else legend.legendHandles
    handles.append(lines_labels[0][0][0])
    labels.append(lines_labels[0][1][0])
    figure.legend(handles, labels, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 1.06))
    figure.savefig('fig_13_llm_models_vaults' + str(vaults) + '.pdf', bbox_inches='tight')


if __name__ == '__main__':
    main()
