import os

topologies = ['mesh', 'SM_Bi', 'SM_Alter']
totalNodes = [9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256]

for topology in topologies:
    for nodes in totalNodes:
        template_file = os.path.join('booksim2/runfiles/mesh_bkp/anynet_mesh_9_200.cfg')
        if os.path.isfile(template_file):
            with open(template_file, 'r') as file:
                data = file.readlines()
        assert data is not None
        cwd = os.getcwd()

        f = os.path.join('booksim2/runfiles/mesh/anynet_' + topology + '_' + str(nodes) + '_200.cfg')
        data[1] = 'network_file = ' + cwd + '/booksim2/runfiles/mesh/anynet/' + topology + '_' + str(nodes) + '_200.txt;'
        data.append('\n')
        data.append('supermesh_topology = ' + str(topology) + ';')
        # data.append('supermesh_topology = mesh;')
        with open(f, 'w') as file:
            file.writelines(data)


topologies = ['SM_Bi', 'SM_Alter']
totalNodes = [9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256]

for topology in topologies:
    for nodes in totalNodes:
        template_file = os.path.join('booksim2/runfiles/mesh_bkp/anynet_mesh_9_200.cfg')
        if os.path.isfile(template_file):
            with open(template_file, 'r') as file:
                data = file.readlines()
        assert data is not None
        cwd = os.getcwd()

        f = os.path.join('booksim2/runfiles/mesh/anynet_' + topology + '_' + str(nodes) + '_200_v2.cfg')
        data[1] = 'network_file = ' + cwd + '/booksim2/runfiles/mesh/anynet/' + topology + '_' + str(nodes) + '_200_v2.txt;'
        data.append('\n')
        # data.append('supermesh_topology = ' + str(topology) + ';')
        data.append('supermesh_topology = mesh;')
        with open(f, 'w') as file:
            file.writelines(data)

topologies = ['Partial_SM_Bi', 'Partial_SM_Alter']
totalNodes = [16]

for topology in topologies:
    for nodes in totalNodes:
        template_file = os.path.join('booksim2/runfiles/mesh_bkp/anynet_mesh_9_200.cfg')
        if os.path.isfile(template_file):
            with open(template_file, 'r') as file:
                data = file.readlines()
        assert data is not None
        cwd = os.getcwd()

        f = os.path.join('booksim2/runfiles/mesh/anynet_' + topology + '_' + str(nodes) + '_200.cfg')
        data[1] = 'network_file = ' + cwd + '/booksim2/runfiles/mesh/anynet/' + topology + '_' + str(nodes) + '_200.txt;'
        data.append('\n')
        if topology == 'Partial_SM_Bi':
            data.append('supermesh_topology = SM_Bi;')
        else:
            data.append('supermesh_topology = SM_Alter;')
        # data.append('supermesh_topology = mesh;')
        with open(f, 'w') as file:
            file.writelines(data)

topologies = ['Partial_SM_Bi', 'Partial_SM_Alter']
totalNodes = [16]

for topology in topologies:
    for nodes in totalNodes:
        template_file = os.path.join('booksim2/runfiles/mesh_bkp/anynet_mesh_9_200.cfg')
        if os.path.isfile(template_file):
            with open(template_file, 'r') as file:
                data = file.readlines()
        assert data is not None
        cwd = os.getcwd()

        f = os.path.join('booksim2/runfiles/mesh/anynet_' + topology + '_' + str(nodes) + '_200_v2.cfg')
        data[1] = 'network_file = ' + cwd + '/booksim2/runfiles/mesh/anynet/' + topology + '_' + str(nodes) + '_200_v2.txt;'
        data.append('\n')
        # data.append('supermesh_topology = ' + str(topology) + ';')
        data.append('supermesh_topology = mesh;')
        with open(f, 'w') as file:
            file.writelines(data)

topologies = ['cmesh', 'dbutterfly', 'kite', 'kite_medium']
totalNodes = [16]

for topology in topologies:
    for nodes in totalNodes:
        template_file = os.path.join('booksim2/runfiles/mesh_bkp/anynet_mesh_9_200.cfg')
        if os.path.isfile(template_file):
            with open(template_file, 'r') as file:
                data = file.readlines()
        assert data is not None
        cwd = os.getcwd()

        f = os.path.join('booksim2/runfiles/mesh/anynet_' + topology + '_' + str(nodes) + '_200.cfg')
        data[1] = 'network_file = ' + cwd + '/booksim2/runfiles/mesh/anynet/' + topology + '_' + str(nodes) + '_200.txt;'
        data.append('\n')
        data.append('supermesh_topology = mesh;')
        with open(f, 'w') as file:
            file.writelines(data)

topologies = ['folded_torus']
totalNodes = [64]

for topology in topologies:
    for nodes in totalNodes:
        template_file = os.path.join('booksim2/runfiles/mesh_bkp/anynet_mesh_9_200.cfg')
        if os.path.isfile(template_file):
            with open(template_file, 'r') as file:
                data = file.readlines()
        assert data is not None
        cwd = os.getcwd()

        f = os.path.join('booksim2/runfiles/mesh/anynet_' + topology + '_' + str(nodes) + '_200.cfg')
        data[1] = 'network_file = ' + cwd + '/booksim2/runfiles/mesh/anynet/' + topology + '_' + str(nodes) + '_200.txt;'
        data.append('\n')
        data.append('supermesh_topology = mesh;')
        with open(f, 'w') as file:
            file.writelines(data)