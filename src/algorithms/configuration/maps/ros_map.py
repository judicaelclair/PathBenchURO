import copy
from typing import List, Tuple, Callable, Dict, Any, Optional
from numbers import Real

from algorithms.configuration.entities.agent import Agent
from algorithms.configuration.entities.goal import Goal
from algorithms.configuration.entities.obstacle import Obstacle
from algorithms.configuration.maps.occupancy_grid_map import OccupancyGridMap
from simulator.services.debug import DebugLevel
from simulator.services.services import Services
from structures import Point, Size

import numpy as np


class RosMap(OccupancyGridMap):
    __update_requested: Optional[Callable[[], None]]
    __get_grid: Callable[[], Tuple[List[Any], Optional[Tuple[Real, Real]], Optional[Real]]]
    __wp_publish: Optional[Callable[[Point], None]]

    def __init__(self, size: Size, agent: Agent, goal: Goal,
                 get_grid: Callable[[], Tuple[List[Any], Optional[Tuple[Real, Real]], Optional[Real]]],
                 wp_publish: Optional[Callable[[Point], None]] = None,
                 update_requested: Optional[Callable[[], None]] = None,
                 services: Services = None) -> None:
        super().__init__(services=services)

        self.__get_grid = get_grid
        self.__wp_publish = wp_publish
        self.__update_requested = update_requested
        self.size = size
        self.agent = agent
        self.goal = goal

        if self._services:
            self.request_update = self._services.debug.debug_func(DebugLevel.LOW)(self.request_update)

    def request_update(self):
        self.set_grid(*self.__get_grid())

        if self.__update_requested:
            self.__update_requested()

    def publish_wp(self, to: Point):
        self.__wp_publish(to)

    def __copy__(self) -> 'RosMap':
        return copy.deepcopy(self)

    def __deepcopy__(self, memo: Dict) -> 'RosMap':
        mp = RosMap(copy.deepcopy(self.size), copy.deepcopy(self.agent), copy.deepcopy(self.goal),
                    self.__get_grid, self.__wp_publish, self.__update_requested,
                    services=self._services)
        mp.weight_grid = copy.deepcopy(self.weight_grid)
        mp.traversable_threshold = copy.deepcopy(self.traversable_threshold)
        mp.trace = copy.deepcopy(self.trace)
        mp.obstacles = copy.deepcopy(self.obstacles)
        mp.grid = copy.deepcopy(self.grid)
        return mp
