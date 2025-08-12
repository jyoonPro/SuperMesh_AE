import os
import re
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = ['serif']
plt.rcParams['font.size'] = 19

def main(exp_type):
    base_path = '{}/micro_2025/random_communication/'.format(os.environ['SIMHOME'])
    if exp_type == 'tornado':
        results_dir = ["results_latency_mesh_tornado", "results_latency_sm_alter_tornado", "results_latency_sm_bi_tornado"]
    else:
        results_dir = ["results_latency_mesh", "results_latency_sm_alter", "results_latency_sm_bi"]
    topologies = ['mesh', 'sm_alter', 'sm_bi']
    topologies_names = ['Mesh', '$SM_{Alter}$', '$SM_{Bi}$']
    colors_dict = {'sm_alter': '#4472c4', 'mesh': '#7A316F', 'sm_bi': '#31AA75'}
    markers_dict = {'sm_alter': 'o', 'sm_bi': '^',
                        'mesh': '*'}
    rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
    # rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]


    pattern = re.compile(r"Packet latency average = ([\d.]+)")
    plt.figure(figsize=(8, 6))

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
        plt.plot(rates, latencies,
                 marker=markers_dict[topo],
                 color=colors_dict[topo],
                 label=topologies_names[idx],
                 linewidth=2,
                 markersize=8)

    # plt.title("Injection Rate vs. Throughput", fontsize=14)
    plt.ylim(15, 40)
    plt.xlabel("Injection Rate")
    plt.ylabel("Packet Latency Average")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    if exp_type == 'tornado':
        plt.savefig("fig_22_injection_vs_latency_tornado.pdf", dpi=300)
    else:
        plt.savefig("fig_22_injection_vs_latency_uniform.pdf", dpi=300)
    # plt.show()
    # figure.savefig('bandwidth_pipeline_allreduce.pdf', bbox_inches='tight')

if __name__== "__main__":
    main('uniform')
    main('tornado')