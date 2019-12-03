"""Draw a map from the grid."""
from typing import Any, List, Tuple

import cv2
import numpy as np

# from sc2pathlib import PathFind


def plot(full_map: Any, path: List[Tuple[int, int]], image_name: str = "map") -> None:
    """Draw the map."""
    image = full_map
    for point in path:
        image[point] = 255
    image = np.rot90(image, 1)
    cv2.imshow(image_name, image)
    cv2.waitKey(1)


MAP_NAME = "Triton LE"
map_array = np.load(f"map_grids/{MAP_NAME}_grid.npy").astype(int)
plot(full_map=map_array, path=[(100, 100), (100, 101)])
