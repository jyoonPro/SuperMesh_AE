1. Check SavedTrees folder
2. Add TACCL, TECCL code
3. Finalize create_cfg_files.py
4. Bring LLMCompass
5. Write that some of the scripts has hundreds of concurrent execution.

1. Automated way to change the paths of all booksim files.

For cleaning up the repository
1. allreduce/network/cmesh -> Remove distance
2. allreduce/network/dbutterfly -> Remove distance
3. allreduce/network/folded_torus -> Remove distance
4. allreduce/network/kite_medium -> Remove distance
5. allreduce/network/kite_small -> Remove distance
6. allreduce/network/kncube -> Remove distance, sm_uni
7. Clean up allreduce.py
8. Remove src/allreduce/Alternative_2D_ring_allreduce.py
9. Remove src/allreduce/chunk_info.py
10. Remove src/allreduce/FatMesh_allreduce_trees.py
11. Proper dot file generation src/allreduce/multitree_allreduce.py
12. Clean up supermesh_pipeline_trees.py
13. Clean up taccl_allreduce.py and handle proper dot file generation
14. Clean up tacos_allreduce.py and handle proper dot file generation
15. Clean up teccl_allreduce.py and handle proper dot file generation
16. Clean up tto_pipeline_trees.py and handle proper dot file generation
17. Clean up anynet files inside booksim
18. Clean up generate_anynet_files/ folder
19. Clean up tacos folder
20. Check generate_global_routing_table.py
21. Clean hmc.py
22. 