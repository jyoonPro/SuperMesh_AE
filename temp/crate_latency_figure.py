import matplotlib.pyplot as plt
import numpy as np

# Creating data
labels = ['MultiTree(Mesh)', 'TACOS(Mesh)', 'Pipeline AG(SM_Bi)', 'Pipeline AG (SM_Alter)', 'Pipeline AG (SM_Uni)']
network_latency = [45565, 34753, 671, 671, 671]
packet_latency = [46727, 35334, 687, 687, 687]
waiting_cycles = [282391, 336422, 123720, 123690, 134962]

x = np.arange(len(labels))  # the label locations
width = 0.35  # the width of the bars

fig, ax = plt.subplots(figsize=(12, 8))
rects1 = ax.bar(x - width/2, network_latency, width, label='Average Network Latency')
rects2 = ax.bar(x - width/2, packet_latency, width, bottom=network_latency, label='Average Packet Latency')
rects3 = ax.bar(x - width/2, waiting_cycles, width, bottom=np.array(network_latency) + np.array(packet_latency), label='Average Waiting Cycles')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Values')
ax.set_title('Comparison of Network and Packet Latency, and Waiting Cycles')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45)
ax.legend()

fig.tight_layout()


