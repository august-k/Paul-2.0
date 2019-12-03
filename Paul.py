"""
Paul 2.0.

Last release date: Unreleased

Most "Any" type hints are placeholders, the actual type is an inline comment.
"""
import pickle  # nosec
from math import floor
from typing import Any, Dict, List, Set, Union

import numpy as np
import sc2
from mypy_extensions import TypedDict
from s2clientprotocol import sc2api_pb2 as sc_pb
from sc2 import Difficulty
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from creep_manager import Creeper
from path_manager import PathManager

# used for self.pathing_dict
PathDict = TypedDict("PathDict", {"path": list, "step": int})


class Paul(sc2.BotAI):
    """The code that is Paul."""

    def __init__(self) -> None:
        """Set up variables and data for the game."""
        super().__init__()
        self.unit_dict: Dict[int, UnitTypeId] = {}
        self.inject_queens: Set[int] = set()
        self.creep_queens: Set[int] = set()
        self.tag_sets: List[Set[int]] = [self.inject_queens, self.creep_queens]
        self.tag_dicts: List[Units] = [self.unit_dict]
        self.target: Point2 = None
        self.build_order: List[Dict] = []
        self.pathing: Any = None  # class
        self.i: int = 0  # build order index
        self.mode: str = "econ"  # econ or army
        self.rush_start = False

    async def on_start(self) -> None:
        """
        Set up data that require information from the game.

        Note: This function is called automatically at iteration = 0.

        Args:
            None

        Returns:
            None
        """
        raw_game_data = await self._client._execute(
            data=sc_pb.RequestData(
                ability_id=True,
                unit_type_id=True,
                upgrade_id=True,
                buff_id=True,
                effect_id=True,
            )
        )
        raw_game_info = await self._client._execute(game_info=sc_pb.RequestGameInfo())
        raw_observation = self.state.response_observation
        self.pathing = PathManager(raw_game_data, raw_game_info, raw_observation)
        self.creeper = Creeper(raw_game_data, raw_game_info, raw_observation)
        # build_selector = BuildOrderManager(self.enemy_race)
        # self.build_order = build_selector.select_build_order()
        with open("builds/1312.pickle", "rb") as f:
            self.build_order = pickle.load(f)  # nosec
        # all possible arguments are handled by BuildOrderManager class
        self.tag_dicts.append(self.pathing.pathing_dict)
        self.target = self.enemy_start_locations[0].position
        await self.chat_send("gl hf")

    async def on_step(self, iteration: int = 0) -> None:
        """
        Call all relevant functions.

        Note: This function is called automatically.

        Args:
            None

        Returns:
            None
        """
        if len(self.units(UnitTypeId.ZERGLING)) >= 6:
            self.rush_start = True
        await self.inject(queen_tags=self.inject_queens)
        if self.rush_start:
            await self.micro()
        creep_grid = np.transpose(self.state.creep.data_numpy)
        if iteration == 0:
            with open("drawn_grids/creep_triton.txt", "w") as f:
                for i in range(creep_grid.shape[0]):
                    for j in range(creep_grid.shape[1]):
                        f.write(str(creep_grid[i][j]))
                    f.write("\n")
        for queen in self.units(UnitTypeId.QUEEN).filter(
            lambda unit: unit.tag in self.creep_queens
        ):
            q_abilities = await self.get_available_abilities(queen)
            if AbilityId.BUILD_CREEPTUMOR_QUEEN in q_abilities:
                enemy_target = self.enemy_start_locations[0].towards(
                    self._game_info.map_center, 5
                )
                to_e_base = self.pathing.pf.find_path(
                    (floor(queen.position.x), floor(queen.position.y)),
                    (floor(enemy_target.x), floor(enemy_target.y)),
                )[0]
                for i in range(len(to_e_base) - 1, -1, -1):
                    if creep_grid[to_e_base[i]]:
                        pos = Point2((to_e_base[i][0], to_e_base[i][1]))
                        self.do(queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, pos))
                        # CAN'T FIND PROPER POINT
        for tumor in self.structures(UnitTypeId.CREEPTUMORBURROWED):
            abilities = await self.get_available_abilities(tumor)
            if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                tumor_positions = {
                    unit.position
                    for unit in self.structures.filter(
                        lambda unit: unit.type_id
                        in {UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMOR}
                    )
                }
                location = await self.creeper.find_position(
                    tumor, tumor_positions, creep_grid, self.pathing.map_grid
                )
                self.do(tumor(AbilityId.BUILD_CREEPTUMOR_TUMOR, location))
        # TODO: place all necessary code above build order due to return statements
        if self.i >= len(self.build_order):
            # TODO: Select new build order instead of switching to army
            self.mode = "army"
        if self.mode == "econ":
            order = self.build_order[self.i]
            if self.supply_used != order["supply"]:
                self.train(UnitTypeId["DRONE"])
            elif self.supply_used == order["supply"]:
                for tech in order["requires"]:
                    if not self.structures(UnitTypeId[tech]).ready:
                        return
                if order["category"] == "struct":
                    if self.workers:
                        worker = self.workers.random
                        if order["name"] == "EXTRACTOR":
                            if self.can_afford(UnitTypeId["EXTRACTOR"]):
                                target = self.vespene_geyser.closest_to(worker)
                                if self.do(worker.build_gas(target)):
                                    self.i += 1
                        elif order["name"] == "SPAWNINGPOOL":
                            pos = self.townhalls[0].position.to2.towards(
                                self._game_info.map_center, 5
                            )
                            if self.can_afford(UnitTypeId["SPAWNINGPOOL"]):
                                if self.do(
                                    worker.build(UnitTypeId["SPAWNINGPOOL"], pos)
                                ):
                                    self.i += 1
                        elif order["name"] == "HATCHERY":
                            if self.minerals >= 300:
                                await self.expand_now()
                                self.i += 1
                elif order["category"] == "unit":
                    if len(self.units(UnitTypeId["LARVA"])) > 0:
                        if self.train(UnitTypeId[order["name"]]):
                            self.i += 1
                elif order["category"] == "upgrade":
                    if self.can_afford(UpgradeId[order["name"]]):
                        self.research(UpgradeId[order["name"]])
                        self.i += 1
        elif self.mode == "army":
            if (
                not self.already_pending(UnitTypeId["SPAWNINGPOOL"])
                and not self.structures(UnitTypeId["SPAWNINGPOOL"]).ready
            ):
                if self.can_afford(UnitTypeId["SPAWNINGPOOL"]):
                    pos = self.townhalls[0].position.to2.towards(
                        self._game_info.map_center, 5
                    )
                    if self.can_afford(UnitTypeId["SPAWNINGPOOL"]):
                        self.do(worker.build(UnitTypeId["SPAWNINGPOOL"], pos))
                else:
                    return
            if self.supply_left <= 2:
                if not self.already_pending(UnitTypeId["OVERLORD"]):
                    self.train(UnitTypeId["OVERLORD"])
            self.train(
                UnitTypeId["ZERGLING"], amount=len(self.units(UnitTypeId["LARVA"]))
            )
            self.train(UnitTypeId["QUEEN"])

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
            for extractor in self.gas_buildings.ready:
                if extractor.assigned_harvesters < 3:
                    self.do(unit.gather(extractor))
                    return
            for base in self.townhalls.ready:
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
                possible_targets = self.townhalls.filter(
                    lambda unit: BuffId.QUEENSPAWNLARVATIMER not in unit.buffs
                )
                if possible_targets:
                    inject_target = possible_targets.closest_to(queen)
                    self.do(queen(AbilityId.EFFECT_INJECTLARVA, inject_target))

    async def on_enemy_unit_entered_vision(self, unit: Unit) -> None:
        """
        Decide what to do based on where the unit is.

        Args:
            unit (Unit): the enemy that entered vision

        Returns:
            None
        """
        if unit.type_id not in {UnitTypeId.DRONE, UnitTypeId.PROBE, UnitTypeId.SCV}:
            if self._distance_pos_to_pos(unit, self.townhalls.closest_to(unit)) <= 20:
                self.mode = "army"

    async def micro(self, unit_tags: List[int] = []) -> None:
        """
        Issue unit commands for microing.

        Args:
            unit_tags (List[int]): Set of units to micro. If empty, micro all units

        Returns:
            None
        """
        if not unit_tags:
            attackers = self.units.filter(
                lambda unit: unit.tag not in self.inject_queens | self.creep_queens
                and unit.type_id
                not in {UnitTypeId.OVERLORD, UnitTypeId.DRONE, UnitTypeId.LARVA}
            )
        else:
            attackers = self.units.filter(lambda unit: unit.tag in unit_tags)
        for unit in attackers:
            self.do(
                unit.attack(
                    self.pathing.follow_path(
                        unit=unit, default=self.enemy_start_locations[0].position
                    )
                )
            )
        pass


def main() -> None:
    """Run the game."""
    sc2.run_game(
        sc2.maps.get("TritonLE"),
        [Bot(Race.Zerg, Paul()), Computer(Race.Protoss, Difficulty.Hard)],
        realtime=False,
        # save_replay_as="PaulTesting.SC2Replay",
    )


if __name__ == "__main__":
    main()
