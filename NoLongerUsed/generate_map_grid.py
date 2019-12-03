"""Generate map grids for Paul."""
import os
from typing import Any

import numpy as np
import sc2
from sc2 import Difficulty
from sc2.data import Race
from sc2.player import Bot, Computer
from sc2.position import Point2


class Dummy(sc2.BotAI):
    """Just for generating grids."""

    def __init__(self) -> None:
        """Determine: here so I don't get yelled at."""
        super().__init__()
        self.map_grid: Any = None  # it's actually an ndarray

    async def on_start(self) -> None:
        """Determine: here so I don't get yelled at."""
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

    async def on_step(self, iteration: int = 0) -> None:
        """Determine not getting yelled at."""
        pass


def main() -> None:
    """Run the game."""
    sc2.run_game(
        sc2.maps.get("TritonLE"),
        [Bot(Race.Zerg, Dummy()), Computer(Race.Terran, Difficulty.VeryEasy)],
        realtime=False,
        # save_replay_as="PaulTesting.SC2Replay",
    )


if __name__ == "__main__":
    main()
