"""Draw the grids stored to check accuracy."""
import numpy as np

NAME = "Triton LE"
map_grid = np.load(f"map_grids/{NAME}_grid.npy").astype(int)
with open(f"drawn_grids/{NAME}_drawn.txt", "w") as f:
    for i in range(map_grid.shape[0]):
        for j in range(map_grid.shape[1]):
            f.write(str(map_grid[i][j]))
        f.write("\n")
