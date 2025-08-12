import json
import os
import pickle

import matplotlib.pyplot as plt

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42


class DrawLinkUtilization:

    def get_used_cycles(self, link_start_time, link_end_time, current_last):
        assert len(link_start_time) == len(link_end_time)
        used_cycles = []
        for i in range(len(link_start_time)):
            start_time = link_start_time[i]
            end_time = link_end_time[i]
            if current_last < start_time:
                current_last = start_time
            while current_last <= end_time:
                used_cycles.append(current_last)
                current_last += 1
        return set(used_cycles)

    def get_utilized_link_info(self, file_name, time_diff):
        print(file_name)
        save_object = pickle.load(open(file_name, 'rb'))
        link_start_time = save_object['link_start_time']
        link_end_time = save_object['link_end_time']
        max_time = save_object['total_time']
        total_links = save_object['total_links']

        time_series = {}
        new_time = time_diff
        required_times = []
        while new_time < max_time:
            time_series[new_time] = []
            required_times.append(new_time)
            new_time += time_diff
        per_cycle_usage = {}
        for i in range(max_time):
            per_cycle_usage[i] = 0
        # print("Done initialization")
        for key in link_start_time.keys():
            if len(link_start_time[key]) > 0:
                starts = link_start_time[key]
                ends = link_end_time[key]
                current_last = 0
                for i in range(len(starts)):
                    start_time = starts[i]
                    end_time = ends[i]
                    if current_last < start_time:
                        current_last = start_time
                    while current_last <= end_time:
                        per_cycle_usage[current_last] += 1
                        current_last += 1
            else:
                raise RuntimeError('No start time of link')
        # print("Done per cycle usage computation")
        utilization_percentage = []
        start_counter = 0
        for r_time in required_times:
            total_used = 0
            all_total_links = 0
            while start_counter < r_time:
                total_used += per_cycle_usage[start_counter]
                all_total_links += total_links
                start_counter += 1
            utilization_percentage.append(total_used / all_total_links)
        return utilization_percentage, required_times

    def average_utilization(self, util_percentage):
        total = sum(util_percentage)
        count = len(util_percentage)
        return total / count

    def compute_link_utilization_ar(self, ax, schemes, names, used_names, data, folder_path, folder_names, collective, colors, x_label, y_label):
        total_nodes = 36
        time_diff = 10000

        for s, name in enumerate(names):
            pkl_filename = "%s/%s/utilization/bw_%d_%s_%d_%s_AR.pkl" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])
            utilization_percentage, required_times = self.get_utilized_link_info(pkl_filename, time_diff)
            print("Average Link Utilization of " + name + " : " + str(self.average_utilization(utilization_percentage)))
            ax.plot(required_times, utilization_percentage, color=colors[s], label=schemes[s], linewidth=3)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.yaxis.grid(True, linestyle='--', color='black')

    def compute_link_utilization_agrs(self, ax, schemes, names, used_names, data, folder_path, folder_names, collective, colors, x_label, y_label):
        total_nodes = 36
        time_diff = 10000

        for s, name in enumerate(names):
            if collective == 'RS':
                pkl_filename = "%s/%s/utilization/bw_%d_%s_%d_%s_RS.pkl" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])
            else:
                pkl_filename = "%s/%s/utilization/bw_%d_%s_%d_%s_AG.pkl" % (folder_path, folder_names[s], data, used_names[s], total_nodes, folder_names[s])

            # print("Before utilization percentage")
            utilization_percentage, required_times = self.get_utilized_link_info(pkl_filename, time_diff)
            print("Average Link Utilization of " + name + " : " + str(self.average_utilization(utilization_percentage)))
            ax.plot(required_times, utilization_percentage, color=colors[s], label=schemes[s], linewidth=3)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_ylim(0, 1)
        ax.yaxis.grid(True, linestyle='--', color='black')


def main():
    tree = DrawLinkUtilization()
    plt.rcParams["figure.figsize"] = [15.00, 5.0]
    plt.rcParams["figure.autolayout"] = True
    # plt.rcParams['font.family'] = ['serif']
    plt.rcParams['font.size'] = 24
    figure, ax1 = plt.subplots(1, 3, sharex=True, sharey=True)
    dataSize = 134217728
    folder_path = '{}/micro_2025/link_utl'.format(os.environ['SIMHOME'])

    schemes = ['MultiTree', 'TTO', '$SM_{Alter}$', '$SM_{Bi}$']
    names = ['multitree', 'pipeline', 'sm_alter', 'sm_bi']
    used_names = ['multitree', 'pipeline', 'pipeline', 'pipeline']
    folder_names = ['mesh', 'mesh', 'SM_Alter', 'SM_Bi']
    collective = 'ar'
    tree.compute_link_utilization_ar(ax1[0], schemes, names, used_names, dataSize, folder_path, folder_names, collective, ['#70ad47', '#EC255A', '#ed7d31', '#4472c4', '#31AA75'], "AllReduce", "Link Utilization")
    print("Allreduce done")

    schemes = ['MultiTree', '$SM_{Alter}$', '$SM_{Bi}$']
    names = ['multitree', 'sm_alter', 'sm_bi']
    used_names = ['multitree', 'pipeline', 'pipeline']
    folder_names = ['mesh', 'SM_Alter', 'SM_Bi']
    collective = 'rs'
    tree.compute_link_utilization_agrs(ax1[1], schemes, names, used_names, dataSize, folder_path, folder_names, collective, ['#70ad47', '#ed7d31', '#4472c4', '#31AA75'], "ReduceScatter", "")
    print("Reduce scatter done")
    collective = 'ag'
    tree.compute_link_utilization_agrs(ax1[2], schemes, names, used_names, dataSize, folder_path, folder_names, collective, ['#70ad47', '#ed7d31', '#4472c4', '#31AA75'], "AllGather", "")
    print("AllGather Done")
    lines_labels = [ax1[0].get_legend_handles_labels()]
    # lines_labels_2 = [ax1[1].get_legend_handles_labels()]
    # lines_labels_3 = [ax1[2].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    # lines2, labels2 = [sum(lol, []) for lol in zip(*lines_labels_2)]
    # lines3, labels3 = [sum(lol, []) for lol in zip(*lines_labels_3)]
    # lines.append(lines2[1])
    # lines.append(lines2[2])
    # labels.append(labels2[1])
    # labels.append(labels2[2])
    figure.legend(lines, labels, loc='upper center', ncol=5, bbox_to_anchor=(0.5, 1.1))

    figure.savefig('fig_18_link_utl_' + str(dataSize) + '_updated_new.pdf', bbox_inches='tight')


if __name__ == '__main__':
    main()
