"""Turns array into text file for visual checking."""
import numpy as np

MAP_NAME = "Triton LE"
map_array = np.load(f"map_grids/{MAP_NAME}_grid.npy")
with open(f"{MAP_NAME}.txt", "w") as f:
    for x in range(map_array.shape[0]):
        for y in range(map_array.shape[1]):
            f.write(str(int(map_array[x][y])))
        f.write("\n")
