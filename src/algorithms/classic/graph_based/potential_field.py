from typing import List, Tuple
import pygame
from typing import Set, List, Tuple, Optional, Dict
from memory_profiler import profile
import numpy as np

#from algorithms.configuration.configuration import Configuration
from algorithms.algorithm import Algorithm
from algorithms.basic_testing import BasicTesting
from algorithms.configuration.entities.agent import Agent
from algorithms.configuration.entities.goal import Goal
from algorithms.configuration.maps.map import Map
from algorithms.configuration.entities.obstacle import Obstacle
from simulator.services.services import Services
from simulator.views.map.display.gradient_map_display import GradientMapDisplay
from simulator.views.map.display.map_display import MapDisplay
from structures import Point, DynamicColour, Colour, BLUE
from structures.tracked_list import TrackedList
from structures.factory import gen_list


class PotentialField(Algorithm):
    """
    Supports both 2D & 3D maps, but extremely slow on 
    any realistic 3D map.
    """

    step_grid: List[Tuple[int, Point]]
    step_grid_min_colour: DynamicColour
    step_grid_max_colour: DynamicColour

    KP = 10.0  # attractive potential gain
    ETA = 50.0  # repulsive potential gain
    AREA_WIDTH = 30.0  # potential area width [m]
    grid_size = 1  # potential grid size [m]
    pmapheat = []
    pmapnew = []

    def __init__(self, services: Services, testing: BasicTesting = None):
        super().__init__(services, testing)

        grid: Map = self._get_grid()
        ls: List[Tuple[int, Point]] = []
        for idx in np.ndindex(*grid.size):
            ls.append((0, Point(*idx)))
        self.step_grid = gen_list(self._services, ls)

        self.step_grid_min_colour = self._services.state.add_colour("step min", BLUE.with_alpha(0))
        self.step_grid_max_colour = self._services.state.add_colour("step max", BLUE)

        self.__map_displays = [GradientMapDisplay(self._services, pts=self.step_grid, min_colour=self.step_grid_min_colour, max_colour=self.step_grid_max_colour)]

    def set_display_info(self) -> List[MapDisplay]:
        """
        Read super description
        """
        return self.__map_displays

    def calc_potential_field(self, grid: Map):
        # calc each potential
        pmap = np.zeros(grid.size, dtype=np.float32)

        for index in np.ndindex(*grid.size):
            ug = self.calc_attractive_potential(index, grid.goal.position)
            uo = self.calc_repulsive_potential(index, grid.obstacles, rr=(grid.agent.radius))

            uf = ug + uo
            pmap[index] = uf
            point = Point(*index)
            self.pmapheat.append((point, uf))

        return pmap

    def calc_attractive_potential(self, pos, goal):
        return 0.5 * self.KP * np.linalg.norm(np.array(pos) - np.array(goal))

    def calc_repulsive_potential(self, pos, obs, rr):
        # search nearest obstacle
        minid = -1

        dmin = float("inf")
        for i in range(len(obs)):
            d = np.linalg.norm(np.array(pos) - np.array(obs[i].position))

            # find closest obstacle
            if dmin >= d:
                dmin = d
                minid = i

        # distance from point to closest obstacle
        dq = np.linalg.norm(np.array(pos) - np.array(obs[minid].position))

        if dq <= 0.99 and dq != 0:
            if dq <= 0.1:
                return 0.5 * self.ETA * (1.0 / dq) ** 2
            else:

                return 0.5 * self.ETA * (1.0 / dq) ** 2
        else:
            return 0

    def __lin_idx(self, p: Point) -> int:
        return np.ravel_multi_index(p.values, self._get_grid().size)

    def potential_field_planning(self, grid):
        # calc potential field
        pmap = self.calc_potential_field(grid)
        for i in range(len(self.step_grid)):
            p = self.step_grid[i][1]
            self.step_grid[i] = (pmap[p.values], p)
        self.key_frame(ignore_key_frame_skip=True)

        nums = []
        for index in np.ndindex(*pmap.shape):
            if pmap[index] < 1000000:
                nums.append(pmap[index])
        self.pmapnew = set(nums)

        # search path
        d = np.linalg.norm(np.array(grid.agent.position) - np.array(grid.goal.position))
        iss = [round((grid.agent.position[i]) / self.grid_size) for i in range(grid.agent.position.n_dim)]  # index starting x position

        gi = [round((grid.goal.position[i]) / self.grid_size) for i in range(grid.agent.position.n_dim)]  # index goal x position

        ri = grid.agent.position

        motion = grid.ALL_POINTS_MOVE_VECTOR
        visited = []

        # we don't want to move to unmapped or obstacle regions.
        for idx in np.ndindex(*grid.size):
            if not grid.is_agent_valid_pos(Point(*idx)):
                visited.append(idx)
        
        while d >= self.grid_size:
            minp = float("inf")
            minIxs = [-1] * grid.agent.position.n_dim
            for point in motion:
                ins = [int(iss[n] + point.values[n]) for n in range(grid.agent.position.n_dim)]

                setInf = False

                for i in range(len(ins)):
                    if ins[i] < 0 or ins[i] >= len(pmap[tuple(([0] * i))]):
                        setInf = True
                        break
                if setInf:
                    p = float("inf")
                else:
                    p = pmap[tuple(ins)]

                point = tuple(ins)
                # find which neighbour has the largest potential value (so can move there)
                if minp > p and point not in visited:
                    minp = p
                    minIxs = ins
                    if tuple(ins) in visited:
                        print("stuck")
                        break
            visited.append(tuple(minIxs))

            iss = minIxs

            d = np.linalg.norm(np.array(grid.goal.position) - np.array(tuple(iss)))
            point1 = Point(*iss)

            if (tuple([-1] * grid.agent.position.n_dim)) in visited:
                print("stuck at start")
                break

            self.move_agent(point1)
            self.key_frame(ignore_key_frame_skip=True)

    # noinspection PyUnusedLocal
    # @profile

    def _find_path_internal(self) -> None:
        """
        Read super description
        The internal implementation of :ref:`find_path`
        """

        # ._get_grid() is in Algorithm class and gets the map
        grid: Map = self._get_grid()
        # agent and goal are represented by a point(x,y) and radius
        agent: Agent = grid.agent
        goal: Goal = grid.goal
        obstacles: Obstacle = grid.obstacles

        # path generation
        self.potential_field_planning(grid)
