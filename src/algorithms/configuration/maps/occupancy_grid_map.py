import numpy as np

from typing import Dict, List, Any, Optional, Tuple
from numbers import Real
import copy

from simulator.services.services import Services

from typing import Dict, List, Any, Optional, Tuple
from numbers import Real
import copy

from simulator.services.services import Services
from simulator.services.event_manager.events.map_update_event import MapUpdateEvent
from algorithms.configuration.maps.map import Map
from algorithms.configuration.maps.dense_map import DenseMap
from algorithms.configuration.entities.agent import Agent
from algorithms.configuration.entities.goal import Goal
from algorithms.configuration.entities.obstacle import Obstacle
from utility.misc import flatten, array_shape
from utility.compatibility import Final
from structures import Point, Size

class OccupancyGridMap(DenseMap):
    weight_grid: np.array
    traversable_threshold: float
    DEFAULT_TRAVERSABLE_THRESHOLD: Final[float] = 0.95

    def __init__(self,
                 weight_grid: Optional[List[Any]] = None,
                 agent: Optional[Agent] = None,
                 goal: Optional[Goal] = None,
                 weight_bounds: Optional[Tuple[Real, Real]] = None,
                 traversable_threshold: Optional[Real] = None,
                 unmapped_value: Optional[Real] = None,
                 services: Services = None) -> None:
        super().__init__(services=services)
        self.agent = agent
        self.goal = goal
        self.weight_grid = None
        self.traversable_threshold = None
        if weight_grid is not None:
            self.set_grid(weight_grid, weight_bounds, traversable_threshold, unmapped_value)

    @property
    def weight_bounds(self):
        return (0, 1)

    @staticmethod
    def __normalise(weight_bounds, x):
        y = (weight_bounds[1] - weight_bounds[0])
        return max(weight_bounds[0], min(weight_bounds[1], ((x - weight_bounds[0]) / y) if y else weight_bounds[0]))

    def set_grid(self, weight_grid: List[Any], weight_bounds: Optional[Tuple[Real, Real]] = None, traversable_threshold: Optional[Real] = None, unmapped_value: Optional[Real] = None) -> None:
        if not isinstance(weight_grid, np.ndarray):
            self.set_grid(np.array(weight_grid), weight_bounds, traversable_threshold, unmapped_value)
            return

        (self.__new_grid if self.size is None else self.__update_grid)(weight_grid, weight_bounds, traversable_threshold, unmapped_value)


    def __update_grid(self, weight_grid: np.ndarray, weight_bounds: Optional[Tuple[Real, Real]] = None, traversable_threshold: Optional[Real] = None, unmapped_value: Optional[Real] = None) -> None:
        assert weight_grid.shape == self.weight_grid.shape, "Dimension mismatch in grid update."

        def remove_obstacle(p: Point):
            for i in range(len(self.obstacles)):
                if self.obstacles[i].position == p:
                    self.obstacles.pop(i)
                    break

        # bounds
        if weight_bounds is None:
            ignored = [] if unmapped_value is None else [unmapped_value]
            weight_bounds = (min(flatten(weight_grid, ignored)), max(flatten(weight_grid, ignored)))
        
        # threshold
        if traversable_threshold is None:
            traversable_threshold = min(weight_bounds[0] + (weight_bounds[1] - weight_bounds[0]) * self.DEFAULT_TRAVERSABLE_THRESHOLD, weight_bounds[1])
        self.traversable_threshold = OccupancyGridMap.__normalise(weight_bounds, traversable_threshold)

        updated_cells: List[Point] = []

        # todo: when obstacle modified, extended wall update required

        # unmapped value
        if unmapped_value is not None:
            for idx in np.ndindex(*self.size):
                if weight_grid[idx] == unmapped_value and self.grid[idx] != Map.UNMAPPED_ID:
                    p = Point(*idx)
                    if self.grid[idx] == Map.WALL_ID or self.grid[idx] == Map.EXTENDED_WALL_ID:
                        remove_obstacle(p)
                    self.grid[idx] = Map.UNMAPPED_ID
                    updated_cells.append(p)
        
        # mapped values
        for idx in np.ndindex(*self.size):
            v = weight_grid[idx]
            self.weight_grid[idx] = OccupancyGridMap.__normalise(weight_bounds, v)

            if self.grid[idx] == Map.UNMAPPED_ID and weight_grid[idx] != unmapped_value:
                p = Point(*idx)
                updated_cells.append(p)

                if v > traversable_threshold:
                    self.grid[idx] = self.WALL_ID
                    self.obstacles.append(Obstacle(p))
                else:
                    self.grid[idx] = self.CLEAR_ID
            elif self.grid[idx] != Map.UNMAPPED_ID:
                if v > traversable_threshold:
                    if self.grid[idx] != Map.WALL_ID:
                        p = Point(*idx)
                        self.grid[idx] = self.WALL_ID
                        self.obstacles.append(Obstacle(p))
                        updated_cells.append(p)
                elif self.grid[idx] == Map.WALL_ID:
                    p = Point(*idx)
                    self.grid[idx] = self.CLEAR_ID
                    remove_obstacle(p)
                    updated_cells.append(p)
        
        if updated_cells and self._services is not None:
            self._services.ev_manager.post(MapUpdateEvent(updated_cells))

        print(self.weight_grid)

    def __new_grid(self, weight_grid: np.ndarray, weight_bounds: Optional[Tuple[Real, Real]] = None, traversable_threshold: Optional[Real] = None, unmapped_value: Optional[Real] = None) -> None:
        self.size = Size(*weight_grid.shape)
        self.grid = np.full(self.size, self.CLEAR_ID, dtype=np.uint8)
        self.weight_grid = np.empty(self.size, dtype=np.float32)

        # bounds
        if weight_bounds is None:
            ignored = [] if unmapped_value is None else [unmapped_value]
            weight_bounds = (min(flatten(weight_grid, ignored)), max(flatten(weight_grid, ignored)))

        # threshold
        if traversable_threshold is None:
            traversable_threshold = min(weight_bounds[0] + (weight_bounds[1] - weight_bounds[0]) * self.DEFAULT_TRAVERSABLE_THRESHOLD, weight_bounds[1])
        self.traversable_threshold = OccupancyGridMap.__normalise(weight_bounds, traversable_threshold)

        # unmapped value
        if unmapped_value is not None:
            for idx in np.ndindex(*self.size):
                if weight_grid[idx] == unmapped_value:
                    self.grid[idx] = self.UNMAPPED_ID
        
        # obstacles
        self.obstacles.clear()
        for idx in np.ndindex(*self.size):
            v = weight_grid[idx]
            self.weight_grid[idx] = OccupancyGridMap.__normalise(weight_bounds, v)
            if v > traversable_threshold and self.grid[idx] != self.UNMAPPED_ID:
                self.grid[idx] = self.WALL_ID
                self.obstacles.append(Obstacle(Point(*idx)))

        # entities
        self.grid[self.agent.position.values] = self.AGENT_ID
        self.grid[self.goal.position.values] = self.GOAL_ID

        # todo: the following works but very slow.
        # Additionally, self.__update_grid() doesn't handle extended wall updates.
        # self.extend_walls()

    def at(self, p: Point) -> int:
        return self.grid[p.values]

    def __repr__(self) -> str:
        return "Occupancy Grid: " + super().__repr__()

    def convert_to_sparse_map(self) -> None:
        raise NotImplementedError()

    def __deepcopy__(self, memo: Dict) -> 'OccupancyGridMap':
        mp = self.__class__(copy.deepcopy(self.weight_grid),
                            copy.deepcopy(self.agent), copy.deepcopy(self.goal),
                            traversable_threshold=self.traversable_threshold,
                            services=self._services)
        mp.trace = copy.deepcopy(self.trace)
        mp.obstacles = copy.deepcopy(self.obstacles)
        mp.grid = copy.deepcopy(self.grid)
        return mp
