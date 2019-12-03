"""Inject, spread creep, transfuse, and other queen actions."""
from typing import Set

import sc2
from sc2.units import Units


class QueenCommands:
    def injects(self, inject_queens: Set[int]) -> None:
        """
        Inject a townhall for each inject_queen that can.

        Args:
            inject_queens (Set[int]): the tags of queens assigned to inject

        Returns:
            None
        """
        for queen in self.units.tags_in(inject_queens):
            available_abilities = await self.get_available_abilities(queen)
