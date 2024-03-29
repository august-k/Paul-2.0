"""Turns array into image for visual checking."""
from math import floor
from typing import List, Tuple, Union

import cv2
import numpy as np

import _sc2pathlib
from sc2pathlib import PathFind


def to_float2(original: Tuple[int, int]) -> Tuple[float, float]:
    """Convert tuple to float2."""
    return (original[0] + 0.5, original[1] + 0.5)


class PathFinder:
    """Create class for usage later."""

    def __init__(self, maze: Union[List[List[int]], np.array]):
        """
        Convert pathing values to integers to improve performance.

        Initialization should be done with array consisting values of 0 and 1.
        """
        self._path_find = PathFind(maze)
        self.heuristic_accuracy = 1  # Octile distance

    def normalize_influence(self, value: int) -> None:
        """
        Normalizes influence to integral value.

        Influence does not need to be calculated each frame, but this quickly resets
        influence values to specified value without changing available paths.
        """
        self._path_find.normalize_influence(value)

    @property
    def width(self) -> int:
        """
        :return: Width of the defined map
        """
        return self._path_find.width

    @property
    def height(self) -> int:
        """
        :return: Height of the defined map
        """
        return self._path_find.height

    @property
    def map(self) -> List[List[int]]:
        """
        :return: map as list of lists [x][y] in python readable format
        """
        return self._path_find.map

    def set_map(self, data: List[List[int]]):
        self._path_find.map = data

    def create_block(
        self,
        center: Union[Tuple[float, float], List[Tuple[float, float]]],
        size: Tuple[int, int],
    ):
        if isinstance(center, list):
            self._path_find.create_blocks(center, size)
        else:
            self._path_find.create_block(center, size)

    def remove_block(
        self,
        center: Union[Tuple[float, float], List[Tuple[float, float]]],
        size: Tuple[int, int],
    ):
        if isinstance(center, list):
            self._path_find.remove_blocks(center, size)
        else:
            self._path_find.remove_block(center, size)

    def find_path(
        self, start: (float, float), end: (float, float), large: bool = False
    ) -> Tuple[List[Tuple[int, int]], float]:
        """
        Finds a path ignoring influence.

        :param start: Start position in float tuple
        :param end: Start position in float tuple
        :param large: Unit is large and requires path to have width of 2 to pass
        :return: Tuple of points and total distance.
        """
        start_int = (floor(start[0]), floor(start[1]))
        end_int = (floor(end[0]), floor(end[1]))
        if large:
            return self._path_find.find_path_large(
                start_int, end_int, self.heuristic_accuracy
            )
        return self._path_find.find_path(start_int, end_int, self.heuristic_accuracy)

    def find_path_influence(
        self, start: (float, float), end: (float, float), large: bool = False
    ) -> (List[Tuple[int, int]], float):
        """
        Finds a path that takes influence into account

        :param start: Start position in float tuple
        :param end: Start position in float tuple
        :param large: Unit is large and requires path to have width of 2 to pass
        :return: Tuple of points and total distance including influence.
        """
        start_int = (floor(start[0]), floor(start[1]))
        end_int = (floor(end[0]), floor(end[1]))
        if large:
            return self._path_find.find_path_influence_large(
                start_int, end_int, self.heuristic_accuracy
            )
        return self._path_find.find_path_influence(
            start_int, end_int, self.heuristic_accuracy
        )

    def safest_spot(
        self, destination_center: (float, float), walk_distance: float
    ) -> (Tuple[int, int], float):
        destination_int = (floor(destination_center[0]), floor(destination_center[1]))
        return self._path_find.lowest_influence_walk(destination_int, walk_distance)

    def lowest_influence_in_grid(
        self, destination_center: (float, float), radius: int
    ) -> (Tuple[int, int], float):
        destination_int = (floor(destination_center[0]), floor(destination_center[1]))
        return self._path_find.lowest_influence(destination_int, radius)

    def add_influence(
        self,
        points: List[Tuple[float, float]],
        value: float,
        distance: float,
        flat: bool = False,
    ):
        list = []
        for point in points:
            list.append((floor(point[0]), floor(point[1])))

        if flat:
            self._path_find.add_influence_flat(list, value, distance)
        else:
            self._path_find.add_influence(list, value, distance)

    def add_influence_walk(
        self,
        points: List[Tuple[float, float]],
        value: float,
        distance: float,
        flat: bool = False,
    ):
        list = []
        for point in points:
            list.append((floor(point[0]), floor(point[1])))

        if flat:
            self._path_find.add_walk_influence_flat(list, value, distance)
        else:
            self._path_find.add_walk_influence(list, value, distance)

    def find_low_inside_walk(
        self, start: (float, float), target: (float, float), distance: Union[int, float]
    ) -> (Tuple[float, float], float):
        """
        Finds a compromise where low influence matches with close position to the start position.

        This is intended for finding optimal position for unit with more range to find optimal position to fight from
        :param start: This is the starting position of the unit with more range
        :param target: Target that the optimal position should be optimized for
        :param distance: This should represent the firing distance of the unit with more range
        :return: Tuple for position and influence distance to reach the destination
        """
        # start_int = (floor(start[0]), floor(start[1]))
        # target_int = (floor(target[0]), floor(target[1]))
        return self._path_find.find_low_inside_walk(start, target, distance)

    def plot(
        self, path: List[Tuple[int, int]], image_name: str = "map", resize: int = 4
    ):
        """
        Uses cv2 to draw current pathing grid.

        requires opencv-python

        :param path: list of points to colorize
        :param image_name: name of the window to show the image in. Unique names update only when used multiple times.
        :param resize: multiplier for resizing the image
        :return: None
        """
        image = np.array(self._path_find.map, dtype=np.uint8)
        for point in path:
            image[point] = 255
        image = np.rot90(image, 1)
        resized = cv2.resize(image, dsize=None, fx=resize, fy=resize)
        cv2.imshow(image_name, resized)
        cv2.waitKey(1)
