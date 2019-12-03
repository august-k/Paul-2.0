"""Manage pathing for Paul."""
import os
from math import floor
from typing import Any, Dict

import numpy as np
from mypy_extensions import TypedDict
from sc2.bot_ai import BotAI
from sc2.game_data import GameData
from sc2.game_info import GameInfo  # , Ramp
from sc2.game_state import GameState
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from sc2pathlib import PathFind

# used for self.pathing_dict
PathDict = TypedDict("PathDict", {"path": list, "step": int})


class PathManager:
    """Manage unit pathing."""

    def __init__(
        self, raw_game_data: Any, raw_game_info: Any, raw_observation: Any
    ) -> None:
        """
        Set up variables for use within PathMangager.

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
        map_name = game_info.map_name
        self.pathing_dict: Dict[int, PathDict] = {}
        map_width = game_info.map_size.width
        map_height = game_info.map_size.height
        raw_grid = np.zeros((map_width, map_height))
        for x in range(map_width):
            for y in range(map_height):
                pos = Point2((x, y))
                raw_grid[x][y] = game_info.pathing_grid[pos]
        self.map_grid = np.rot90(raw_grid.astype(int))
        np.save(f"map_grids/{map_name}_grid", self.map_grid)
        self.pf = PathFind(self.map_grid)

    def add_to_path_dict(self, unit: Unit, destination: Point2) -> None:
        """
        Add unit's path to the path storage dictionary.

        Args:
            unit (Unit): the unit for pathing
            destination (Point2): where the unit is going
        Returns:
            None
        """
        self.pathing_dict[unit.tag] = {"path": [], "step": 0}
        raw_unit_pos = unit.position
        floored_unit_pos = Point2((floor(raw_unit_pos.x), floor(raw_unit_pos.y)))
        floored_dest = Point2((floor(destination[0]), floor(destination[1])))
        self.pathing_dict[unit.tag]["path"] = self.pf.find_path(
            floored_unit_pos, floored_dest
        )[0]

    def follow_path(self, unit: Unit, default: Point2) -> Point2:
        """
        Follow the path set or set a new one if none exists.

        Args:
            unit (Unit): the unit moving

        Returns:
            Point2: the location to attack
        """
        if (
            len(
                self.bot.structures.filter(
                    lambda unit: unit.type_id
                    in {UnitTypeId.NYDUSNETWORK, UnitTypeId.NYDUSCANAL}
                )
            )
            < 2
        ):
            if unit.tag not in self.pathing_dict:
                self.add_to_path_dict(unit, tuple(default))
            advance_factor = int(unit.movement_speed) + 2
            self.pathing_dict[unit.tag]["step"] += advance_factor
            curr_step = self.pathing_dict[unit.tag]["step"]
            if curr_step >= len(self.pathing_dict[unit.tag]["path"]):
                curr_step = len(self.pathing_dict[unit.tag]["path"]) - 1
            if curr_step < 0:
                return default
            a_move_to = Point2(self.pathing_dict[unit.tag]["path"][curr_step])
            if curr_step == len(self.pathing_dict[unit.tag]["path"]) - 1:
                del self.pathing_dict[unit.tag]
            return a_move_to
