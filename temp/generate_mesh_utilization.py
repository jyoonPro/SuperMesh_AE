import copy
import math
import pickle

def get_lrtb(node, nodes_per_dim):
    col_idx = node % nodes_per_dim
    row_idx = math.floor(node / nodes_per_dim)
    if col_idx == 0:
        left = None
        right = node + 1
    elif col_idx == nodes_per_dim - 1:
        left = node - 1
        right = None
    else:
        left = node - 1
        right = node + 1

    if row_idx == 0:
        top = None
        bottom = node + nodes_per_dim
    elif row_idx == nodes_per_dim - 1:
        top = node - nodes_per_dim
        bottom = None
    else:
        top = node - nodes_per_dim
        bottom = node + nodes_per_dim
    return left, right, top, bottom

def generate_a2a_schedule_visualization(saved_file_path, output_path):
    save_object = pickle.load(open(saved_file_path, 'rb'))
    max_tree_height_for_pipeline = save_object['max_tree_height_for_pipeline']
    trees_rs = save_object['trees_rs']
    trees_ag = save_object['trees_ag']
    timesteps_rs = save_object['timesteps_rs']
    timesteps_ag = save_object['timesteps_ag']
    tree_roots = save_object['tree_roots']

    print("Loaded tree information")
    total_nodes = 64
    node_per_dim = int(math.sqrt(total_nodes))
    node_to_node_tracker = {}
    for node in range(total_nodes):
        left, right, top, bottom = get_lrtb(node, node_per_dim)
        temp_tracker = {}
        if left is not None:
            temp_tracker[left] = 0
        if right is not None:
            temp_tracker[right] = 0
        if top is not None:
            temp_tracker[top] = 0
        if bottom is not None:
            temp_tracker[bottom] = 0
        node_to_node_tracker[node] = temp_tracker

    for tree_id in trees_ag.keys():
        tree = trees_ag[tree_id]
        for edge in tree:
            source = edge[1]
            dest = edge[0]
            node_to_node_tracker[source][dest] += 1

    unique_utilizations = set()
    utilization_dict = {}
    for node in range(total_nodes):
        for dest in node_to_node_tracker[node].keys():
            percentage = int(node_to_node_tracker[node][dest] * 100 / timesteps_ag)
            node_to_node_tracker[node][dest] = percentage
            unique_utilizations.add(node_to_node_tracker[node][dest])
            if percentage not in utilization_dict.keys():
                utilization_dict[percentage] = []
            utilization_dict[percentage].append((node, dest))
    print(unique_utilizations)
    for percentage in sorted(unique_utilizations):
        print(str(percentage) + " - R:" + str(int(percentage*255/100)) + ", G:" + str(int((100-percentage)*255/100)))
        for (src, dest) in utilization_dict[percentage]:
            print(str(src) + " -> " + str(dest))

    color_dict = {}
    color_dict[16] = '#28D600'
    color_dict[22] = '#38C600'
    color_dict[27] = '#44BA00'
    color_dict[33] = '#54AA00'
    color_dict[38] = '#609E00'
    color_dict[44] = '#708E00'
    color_dict[50] = '#7F7F00'
    color_dict[55] = '#8C7200'
    color_dict[61] = '#9B6300'
    color_dict[66] = '#A85600'
    color_dict[72] = '#B74700'
    color_dict[77] = '#C43A00'
    color_dict[83] = '#D32B00'
    color_dict[88] = '#E01E00'
    color_dict[94] = '#EF0F00'
    color_dict[100] = '#FF0000'

    header = 'digraph tree {\n'
    header += '  rankdir = BT;\n'
    header += '  color = black;\n'
    per_dim_nodes = int(math.sqrt(total_nodes))

    header += '\n'
    for node in range(per_dim_nodes):
        header += '  {rank = same;'
        for target_node in range(per_dim_nodes-1, -1, -1):
            header += ' "{}";'.format(node * per_dim_nodes + target_node)
        header += '}\n'
    temp_node_to_node_tracker = copy.deepcopy(node_to_node_tracker)
    for node in range(total_nodes):
        for key, value in temp_node_to_node_tracker[node].items():
            header += '  "{}" -> "{}" [ minlen=1, color="{}", penwidth=2];\n'.format(node, key, color_dict[node_to_node_tracker[node][key]])
    header += '}\n'

    f = open(output_path, 'w')
    f.write(header)
    f.close()

output_path = '/home/sabuj/Sabuj/Research/SuperMesh_2/src/8x8_mesh_proposed.dot'
saved_file_path = '/src/SavedTrees_2/mesh/mesh_multitree_64'
generate_a2a_schedule_visualization(saved_file_path, output_path)