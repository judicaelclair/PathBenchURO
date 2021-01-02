from typing import Optional, List, Type, Dict, Any, Tuple, Union
import importlib.util
import inspect
import os
import sys
import copy
import traceback

# builtin base map type
from algorithms.configuration.maps.map import Map

# Builtin maps
from maps.maps import Maps

from simulator.services.services import Services
from utility.misc import static_class

@static_class
class MapManager():
    MetaData = Tuple[Union[Map, str], bool]

    cached_builtins: Dict[str, MetaData]
    builtins: Dict[str, MetaData]

    @classmethod
    def _static_init_(cls):
        cls.cached_builtins = {}

        for name in dir(Maps):
            if name.startswith("_"):
                continue
            
            v = getattr(Maps, name)
            if not isinstance(v, Map):
                continue
            
            display_name = v.name if v.name else name
            cls.cached_builtins[display_name] = (v, True)
        
        cls.builtins = {
            "Uniform Random Fill": ("uniform_random_fill_10/0", True),
            "Uniform Random Fill 3D": ("uniform_random_fill_10_3d/0_3d", True),
            "Block": ("block_map_10/6", True),
            "Block 3D": ("block_map_10_3d/6_3d", True),
            "House": ("house_10/6", True),
            "House 3D": ("house_10_3d/6_3d", True),
            Maps.grid_map_one_obstacle1.name: (Maps.grid_map_one_obstacle1, True),
            Maps.grid_map_labyrinth.name: (Maps.grid_map_labyrinth, True),
            Maps.grid_map_3d_example.name: (Maps.grid_map_3d_example, True),
            Maps.grid_map_small_one_obstacle2.name: (Maps.grid_map_small_one_obstacle2, True),
            Maps.grid_map_small_one_obstacle.name: (Maps.grid_map_small_one_obstacle, True),
            Maps.grid_map_small_one_obstacle3.name: (Maps.grid_map_small_one_obstacle3, True),
            Maps.grid_map_complex_obstacle.name: (Maps.grid_map_complex_obstacle, True),
            Maps.grid_map_complex_obstacle2.name: (Maps.grid_map_complex_obstacle2, True),
            Maps.grid_map_28x28vin.name: (Maps.grid_map_28x28vin, True),
            "Small Obstacle": (Maps.grid_map_one_obstacle.convert_to_dense_map(), True),
            Maps.ogm_2d.name: (Maps.ogm_2d, False),
            Maps.ogm_3d.name: (Maps.ogm_3d, False),
            "SLAM Map 1": ("map10", False),
            "SLAM Map 1 (compressed)": ("map11", True),
            "SLAM Map 2": ("map14", False),
            "SLAM Map 3": ("map12", False),
        }

    def load_all(ids: List[str]) -> List[List[Tuple[str, MetaData]]]:
        """
        Returns a list of map classes from a list of names or file paths.

        For each element in `ids`, if string is the display name
        of a built-in map, then we return that map. Otherwise,
        we return the result of MapManager.try_load_from_file().
        """
        return list(map(MapManager.load, ids))

    def load(mp: str) -> List[Tuple[str, MetaData]]:
        """
        Returns a list of map classes from one name or file path
        """

        if mp in MapManager.cached_builtins:
            return [(mp, copy.deepcopy(MapManager.cached_builtins[mp]))]
        elif mp in MapManager.builtins:
            data = MapManager.builtins[mp]
            return [(mp, copy.deepcopy(data))]
        else:
            return MapManager.try_load_from_file(mp)

    @staticmethod
    def try_load_from_file(path: str) -> List[Tuple[str, MetaData]]:
        if not os.path.exists(path):
            msg = "File '{}' does not exist".format(path)
            print(msg, file=sys.stderr)
            return []

        try:
            spec = importlib.util.spec_from_file_location("custom_loaded", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # return all objects that subclass "Map"
            maps = []
            for name in dir(module):
                if name.startswith("_"):
                    continue

                mp = getattr(module, name)
                if not isinstance(mp, Map):
                    continue

                display_name = mp.name if mp.name else os.path.basename(path) + " ({})".format(name)
                maps.append((display_name, (mp, True)))
            return maps
        except:
            msg = "Failed to load map from file '{}', reason:\n{}".format(path, traceback.format_exc())
            print(msg, file=sys.stderr)
            return []
