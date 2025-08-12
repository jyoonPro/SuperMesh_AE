mesh_wire = [2.097152e-05, 3.276800e-05, 4.718592e-05, 6.422528e-05, 8.388608e-05, 1.061683e-04, 1.310720e-04]
mesh_active = [2.327825e-05, 3.637226e-05, 5.237606e-05, 7.128963e-05, 9.311299e-05, 1.178461e-04, 1.454890e-04]
mesh_total = [a + b for a, b in zip(mesh_wire, mesh_active)]

sm_uni_wire = [2.490368e-05, 3.801088e-05, 5.373952e-05, 7.208960e-05, 9.306112e-05, 1.166541e-04, 1.428685e-04]
sm_uni_active = [2.328776e-05, 3.638495e-05, 5.239192e-05, 7.130866e-05, 9.313519e-05, 1.178715e-04, 1.455176e-04]
sm_uni_total = [a + b for a, b in zip(sm_uni_wire, sm_uni_active)]

sm_alter_wire = [2.621440e-05, 3.801088e-05, 5.505024e-05, 7.208960e-05, 9.437184e-05, 1.166541e-04, 1.441792e-04]
sm_alter_active = [2.329093e-05, 3.638495e-05, 5.239509e-05, 7.130866e-05, 9.313836e-05, 1.178715e-04, 1.455208e-04]
sm_alter_total = [a + b for a, b in zip(sm_alter_wire, sm_alter_active)]

sm_bi_wire = [2.883584e-05, 4.325376e-05, 6.029312e-05, 7.995392e-05, 1.022362e-04, 1.271398e-04, 1.546650e-04]
sm_bi_active =[3.281370e-05, 5.126705e-05, 7.381972e-05, 1.004717e-04, 1.312231e-04, 1.660738e-04, 2.050238e-04]
six_five_router_ratio = [a / b for a, b in zip(sm_bi_active, mesh_active)]
sm_bi_router = []
for i in range(4, 11):
    six_port = 4 * (i - 2)
    five_port = i * i - six_port
    five_port_per_router = mesh_active[i-4] / (i*i)
    sm_bi_router.append(five_port * five_port_per_router + six_port * five_port_per_router * six_five_router_ratio[i-4])
sm_bi_total = [a + b for a, b in zip(sm_bi_wire, sm_bi_router)]

print("SM_Uni Area Overhead")
print([a / b for a, b in zip(sm_uni_total, mesh_total)])
print("SM_Alter Area Overhead")
print([a / b for a, b in zip(sm_alter_total, mesh_total)])
print("SM_Bi Area Overhead")
print([a / b for a, b in zip(sm_bi_total, mesh_total)])

mesh_64_per_wire = mesh_wire[4] / 224
folded_torus_total_wire = mesh_64_per_wire * 256
mesh_16_per_wire = mesh_wire[0] / 48
kite_total_wire = mesh_16_per_wire * 2.8 * 60
kite_medium_total_wire = mesh_16_per_wire * 4 * 60
cmesh_total_wire = mesh_16_per_wire * 2 * 48
dbutterfly_wire = mesh_16_per_wire * 4.45 * 48


router_total_normal = mesh_active[4] # For 64 case
per_port_concen = (sm_bi_active[4]/(64*6)) * 8
router_total_concen = per_port_concen * 16 # For 16 case TODO: Currently it has six port router. Update with eight port router.
folded_torus_total = folded_torus_total_wire + router_total_normal
kite_total = kite_total_wire + router_total_concen
kite_medium_total = kite_medium_total_wire + router_total_concen
cmesh_total = cmesh_total_wire + router_total_concen
dbutterfly_total = dbutterfly_wire + router_total_concen
mesh_total_area = mesh_total[4]
sm_bi_total_area = sm_bi_total[4]
sm_alter_total_area = sm_alter_total[4]

print("SM Bi vs folded torus: " + str(sm_bi_total_area / folded_torus_total))
print("SM Bi vs kite: " + str(sm_bi_total_area / kite_total))
print("SM Bi vs kite medium: " + str(sm_bi_total_area / kite_medium_total))
print("SM Bi vs cmesh: " + str(sm_bi_total_area / cmesh_total))
print("SM Bi vs dbutterfly: " + str(sm_bi_total_area / dbutterfly_total))

print("SM Alter vs folded torus: " + str(sm_alter_total_area / folded_torus_total))
print("SM Alter vs kite: " + str(sm_alter_total_area / kite_total))
print("SM Alter vs kite medium: " + str(sm_alter_total_area / kite_medium_total))
print("SM Alter vs cmesh: " + str(sm_alter_total_area / cmesh_total))
print("SM Alter vs dbutterfly: " + str(sm_alter_total_area / dbutterfly_total))

print("Mesh vs folded torus: " + str(mesh_total_area / folded_torus_total))
print("Mesh vs kite: " + str(mesh_total_area / kite_total))
print("Mesh vs kite medium: " + str(mesh_total_area / kite_medium_total))
print("Mesh vs cmesh: " + str(mesh_total_area / cmesh_total))
print("Mesh vs dbutterfly: " + str(mesh_total_area / dbutterfly_total))