"""Spread creep."""
from math import floor
from typing import Any, Set

import numpy as np  # noqa F401
from sc2.bot_ai import BotAI
from sc2.game_data import GameData
from sc2.game_info import GameInfo  # , Ramp
from sc2.game_state import GameState
from sc2.position import Point2
from sc2.unit import Unit

from path_manager import PathManager
from sc2pathlib import PathFind


class Creeper:
    """Spread creep."""

    def __init__(
        self, raw_game_data: Any, raw_game_info: Any, raw_observation: Any
    ) -> None:
        """
        Set up variables for use within Creeper.

        Args:
            raw_game_data (Any): self.game_data from main instance
            raw_game_info (Any): self.game_info from main instance
            raw_observation (Any): self.game_state from main instance

        Returns:
            None
        """
        self.bot = BotAI()
        game_data = GameData(raw_game_data.data)
        game_info = GameInfo(raw_game_info.game_info)
        game_state = GameState(raw_observation)
        self.bot._initialize_variables()
        self.bot._prepare_start(
            client=None, player_id=1, game_info=game_info, game_data=game_data
        )
        self.bot._prepare_step(state=game_state, proto_game_info=raw_game_info)
        self.pathing = PathManager(raw_game_data, raw_game_info, raw_observation)
        self.pf = PathFind(self.pathing.map_grid)

    def check_tumor_position(
        self, possible_position: Point2, combined_grid: Any
    ) -> int:
        """
        Calculate the number of tiles the tumor position would cover.

        Arg:
            possible_position (Point2): the point being checked.
            combined_grid (Any): ndarray that's the pathfinding lib's path map and the
                                 creep map added together

        Returns:
            int: the number of tiles that would be covered.
        """
        x, y = floor(possible_position[0]), floor(possible_position[1])
        future_tiles = 0
        for i in range(-10, 11):
            for j in range(-10, 11):
                if 8 <= abs(j) <= 10:
                    if abs(i) <= 6 - 2 * (abs(j) - 8):
                        future_tiles += combined_grid[Point2((x + i, y + j))] % 2
                elif abs(j) == 7:
                    if abs(i) <= 7:
                        future_tiles += combined_grid[Point2((x + i, y + j))] % 2
                elif 3 <= abs(j) <= 6:
                    if abs(i) <= 9 - floor(abs(j) / 5):
                        future_tiles += combined_grid[Point2((x + i, y + j))] % 2
                else:
                    if combined_grid[Point2((x + i, y + j))] == 1:
                        future_tiles += 1
        return future_tiles

    async def find_position(
        self,
        tumor: Unit,
        tumor_positions: Set[Point2],
        creep_grid: Any,
        pathable_map: Any,
    ) -> Point2:
        """
        Find the location to spread the tumor to.

        Args:
            tumor (Unit): the creep tumor ready to be spread
            tumor_positions (Set[Point2]): list of existing tumor locations
            creep_grid (ndarray): the creep grid from the main bot
            pathable_map (ndarray): the pathfinding lib's pathable map

        Returns:
            Point2: where to spread the tumor.
        """
        path_creep_map = creep_grid + pathable_map
        tposx, tposy = tumor.position.x, tumor.position.y
        max_tiles = 0
        location = None
        for i in range(-10, 11):
            for j in range(-10, 11):
                if 81 <= i ** 2 + j ** 2 <= 105:
                    pos = Point2((tposx + i, tposy + j))
                    if pos not in tumor_positions:
                        if path_creep_map[floor(pos[0])][floor(pos[1])] != 2:
                            continue
                        tiles = self.check_tumor_position((pos), path_creep_map)
                        if tiles > max_tiles:
                            max_tiles = tiles
                            location = pos
        if max_tiles < 75:
            floored_unit_pos = Point2((floor(tposx), floor(tposy)))
            floored_e_base = Point2(
                (
                    floor(self.bot.enemy_start_locations[0].position.x),
                    floor(self.bot.enemy_start_locations[0].position.y),
                )
            )
            path_to_e_base = self.pf.find_path(floored_unit_pos, floored_e_base)[0]
            if path_to_e_base:
                for k in range(9, 5, -1):
                    pos = path_to_e_base[k]
                    if path_creep_map[pos[0]][pos[1]] == 2:
                        location = Point2(pos)
                        break
        if location:
            return location
        else:
            return tumor.position
