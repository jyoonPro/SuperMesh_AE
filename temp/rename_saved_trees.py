import os

# Define the directory to search for files
directory = '/home/sabuj/Sabuj/Research/SuperMesh_2/src/SavedTrees_2/SM_Uni'

# Loop through each file in the directory
for filename in os.listdir(directory):
    if filename.startswith("fatmesh_unidirectional"):
        # Construct the old file path
        old_file = os.path.join(directory, filename)

        # Construct the new file name by replacing the old ending with the new ending
        new_file = os.path.join(directory, filename.replace("fatmesh_unidirectional", "SM_Uni"))

        # Rename the file
        os.rename(old_file, new_file)
        print(f"Renamed '{old_file}' to '{new_file}'")
