"""
Paul 2.0.

Last release date: Unreleased

Most "Any" type hints are placeholders, the actual type is an inline comment.
"""
import os
from math import floor
from typing import Any, Dict, Set, Union

import numpy as np
import sc2
from mypy_extensions import TypedDict
from sc2 import Difficulty
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit

from sc2pathlib import PathFind

# used for self.pathing_dict
PathDict = TypedDict("PathDict", {"path": list, "step": int})


class Paul(sc2.BotAI):
    """The code that is Paul."""

    def __init__(self) -> None:
        """Set up variables and data for the game."""
        super().__init__()
        self.unit_dict: Dict[int, UnitTypeId] = {}
        self.pathing_dict: Dict[int, PathDict] = {}
        self.inject_queens: Set[int] = set()
        self.creep_queens: Set[int] = set()
        self.tag_sets = [self.inject_queens, self.creep_queens]
        self.tag_dicts = [self.unit_dict, self.pathing_dict]
        self.map_grid: Any = None  # ndarray
        self.pf: Any = None  # sc2pathlib object
        self.target: Point2 = Point2((0, 0))

    async def on_start(self) -> None:
        """
        Set up data that requires information from the game.

        Note: This function is called automatically at iteration = 0.

        Args:
            None

        Returns:
            None
        """
        # get map grid for pathing
        map_name = self.game_info.map_name
        if os.path.exists(f"map_grids/{map_name}_grid.npy"):
            self.map_grid = np.load(f"map_grids/{map_name}_grid.npy")
        else:
            map_width = self.game_info.map_size.width
            map_height = self.game_info.map_size.height
            raw_grid = np.zeros((map_width, map_height))
            for x in range(map_width):
                for y in range(map_height):
                    pos = Point2((x, y))
                    raw_grid[x][y] = self.game_info.pathing_grid[pos]
            self.map_grid = np.rot90(raw_grid.astype(int))
            np.save(f"map_grids/{map_name}_grid", self.map_grid)
        # create search space for A* path finding
        self.pf = PathFind(self.map_grid)
        self.target = self.enemy_start_locations[0].to2.towards(
            self.game_info.map_center, 4
        )

    async def on_step(self, iteration: int = 0) -> None:
        """
        Call all relevant functions.

        Note: This function is called automatically.

        Args:
            None

        Returns:
            None
        """
        # await self.inject(queen_tags=self.inject_queens)
        # if self.supply_used == 12 and not self.already_pending(UnitTypeId.EXTRACTOR):
        #     worker = self.workers.random
        #     self.do(
        #         worker.build(
        #             UnitTypeId.EXTRACTOR,
        #             self.vespene_geyser.closest_to(worker.position),
        #         )
        #     )
        #     return
        # if self.supply_left == 1 and not self.already_pending(UnitTypeId.OVERLORD):
        #     self.train(UnitTypeId.OVERLORD)
        # if self.supply == 15:
        #     if self.can_afford(UnitTypeId.HATCHERY):
        #         self.expand_now()
        #         return
        #     else:
        #         return
        # self.train(UnitTypeId.DRONE)
        for drone in self.workers:
            self.follow_path(drone)

    async def on_unit_created(self, unit: Unit) -> None:
        """
        Add unit to dictionaries and determine what should happen to each spawned unit.

        Note: This function is called automatically.

        Args:
            unit (Unit): the unit created

        Returns:
            None
        """
        self.unit_dict[unit.tag] = unit.type_id

        # drone protocol (prioritize gas -> minerals)
        if unit.type_id in {UnitTypeId.DRONE}:
            for extractor in self.gas_buildings:
                if extractor.assigned_harvesters < 3:
                    self.do(unit.gather(extractor))
                    return
            for base in self.townhalls:
                if base.assigned_harvesters < 16:
                    self.do(unit.gather(self.mineral_field.closest_to(base.position)))
                    return

        # queen protocol (inject > creep > unassigned)
        if unit.type_id in {UnitTypeId.QUEEN}:
            if len(self.inject_queens) < min(len(self.townhalls), 3):
                self.inject_queens.add(unit.tag)
                return
            elif len(self.creep_queens) < 4:
                self.creep_queens.add(unit.tag)
                return

    async def on_unit_destroyed(self, unit_tag: int) -> None:
        """
        Remove dead units from stored data points, replace structures/drones.

        Note: This function is called automatically.

        Args:
            unit_tag (int): tag of the deceased unit

        Returns:
            None
        """
        # clean up lists and sets
        for tag_set in self.tag_sets:  # type: Union[list, set]
            if unit_tag in tag_set:
                tag_set.remove(unit_tag)

        # clean up dictionaries
        for tag_dict in self.tag_dicts:  # type: Dict
            if unit_tag in tag_dict:
                del tag_dict[unit_tag]

    async def on_building_construction_complete(self, unit: Unit) -> None:
        """
        Determine if anything needs to be done when a building finishes.

        Note: This function is called automatically.

        Args:
            unit (Unit): the building completed

        Returns:
            None
        """
        # immediately assign workers to geyser
        if unit.type_id in {UnitTypeId.EXTRACTOR, UnitTypeId.EXTRACTORRICH}:
            gas_drones = self.workers.closest_n_units(unit, 3)
            for drone in gas_drones:
                self.do(drone.gather(unit))
            return

    async def inject(self, queen_tags: Set[int]) -> None:
        """
        Inject townhalls.

        Args:
            queen_tags (Set[int]): tags of queens assigned to inject

        Returns:
            None
        """
        queens = self.units.tags_in(queen_tags)
        for queen in queens:
            abilities = await self.get_available_abilities(queen)
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                inject_target = self.townhalls.closest_to(queen)
                self.do(queen(AbilityId.EFFECT_INJECTLARVA, inject_target))

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
        floored_dest = Point2((floor(destination.x), floor(destination.y)))
        self.pathing_dict[unit.tag]["path"] = self.pf.find_path(
            floored_unit_pos, floored_dest
        )[0]

    def follow_path(self, unit: Unit) -> None:
        """
        Follow the path set or set a new one if none exists.

        Args:
            unit (Unit): the unit moving

        Returns:
            None
        """
        if unit.tag not in self.pathing_dict:
            self.add_to_path_dict(unit, self.target)
        else:
            advance_factor = int(unit.movement_speed) + 2
            self.pathing_dict[unit.tag]["step"] += advance_factor
        curr_step = self.pathing_dict[unit.tag]["step"]
        if curr_step >= len(self.pathing_dict[unit.tag]["path"]):
            curr_step = len(self.pathing_dict[unit.tag]["path"]) - 1
        self.do(unit.attack(Point2(self.pathing_dict[unit.tag]["path"][curr_step])))
        if curr_step == len(self.pathing_dict[unit.tag]["path"]) - 1:
            del self.pathing_dict[unit.tag]


def main() -> None:
    """Run the game."""
    sc2.run_game(
        sc2.maps.get("TritonLE"),
        [Bot(Race.Zerg, Paul()), Computer(Race.Terran, Difficulty.VeryEasy)],
        realtime=False,
        # save_replay_as="PaulTesting.SC2Replay",
    )


if __name__ == "__main__":
    main()
