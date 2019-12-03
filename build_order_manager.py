"""Determine units to train based on starting build order and game state."""
import json

# import os
from typing import Any

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId


class BuildOrderManager:
    """Select a build order, then add orders as needed."""

    def __init__(self, enemy_race: Race) -> None:
        """
        Pick build order informed by relevant game information.

        Args:
            enemy_race (Race): the enemy race

        Returns:
            None
        """
        self.enemy_race = enemy_race
        # units
        self.unittype = {
            UnitTypeId.DRONE,
            UnitTypeId.QUEEN,
            UnitTypeId.ZERGLING,
            UnitTypeId.BANELING,
            UnitTypeId.ROACH,
            UnitTypeId.RAVAGER,
            UnitTypeId.HYDRALISK,
            UnitTypeId.LURKER,
            UnitTypeId.INFESTOR,
            UnitTypeId.SWARMHOSTMP,
            UnitTypeId.ULTRALISK,
            UnitTypeId.OVERLORD,
            UnitTypeId.OVERSEER,
            UnitTypeId.MUTALISK,
            UnitTypeId.CORRUPTOR,
            UnitTypeId.BROODLORD,
            UnitTypeId.VIPER,
        }
        # buildings
        self.building_categories = {
            UnitTypeId.HATCHERY: "economy",
            UnitTypeId.EXTRACTOR: "economy",
            UnitTypeId.SPAWNINGPOOL: "tech",
            UnitTypeId.EVOLUTIONCHAMBER: "tech",
            UnitTypeId.SPINECRAWLER: "defense",
            UnitTypeId.SPORECRAWLER: "defense",
            UnitTypeId.ROACHWARREN: "tech",
            UnitTypeId.BANELINGNEST: "tech",
            UnitTypeId.LAIR: "tech",
            UnitTypeId.HYDRALISKDEN: "tech",
            UnitTypeId.LURKERDEN: "tech",
            UnitTypeId.INFESTATIONPIT: "tech",
            UnitTypeId.SPIRE: "tech",
            UnitTypeId.NYDUSNETWORK: "tech",
            UnitTypeId.NYDUSCANAL: "transport",  # Nydus Worm
            UnitTypeId.HIVE: "tech",
            UnitTypeId.ULTRALISKCAVERN: "tech",
            UnitTypeId.GREATERSPIRE: "tech",
            UnitTypeId.CREEPTUMOR: "scouting",
        }
        self.structype = set(self.building_categories)
        self.i: int = 0
        self.build_order = self.select_build_order()
        self.build_order_done: bool = False

    def select_build_order(self) -> Any:
        """
        Based on critera, select build order.

        Currently, selections are only made based on race.

        Returns:
            List[Union[UnitTypeId, str]]: build order as a list.
        """
        with open("builds/1312.json", "r", encoding="utf8") as f:
            build_order = json.load(f)
        return build_order

    def select_id_to_build(self) -> UnitTypeId:
        """
        Identify the id of what needs to be built.

        Args:
            None

        Returns:
            UnitTypeId: id of the unit/structure/upgrade to be built.
        """
