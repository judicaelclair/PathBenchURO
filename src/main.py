import sys
import os

# Compatibility for running with codecov, add 'PathBench/src' to system path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from algorithms.configuration.configuration import Configuration  # noqa: E402
from algorithms.algorithm_manager import AlgorithmManager  # noqa: E402
from maps.map_manager import MapManager  # noqa: E402
from algorithms.lstm.trainer import Trainer  # noqa: E402
from analyzer.analyzer import Analyzer  # noqa: E402
from generator.generator import Generator  # noqa: E402
from simulator.services.debug import DebugLevel  # noqa: E402
from simulator.services.services import Services  # noqa: E402
from simulator.simulator import Simulator  # noqa: E402
from utility.misc import flatten  # noqa: E402
from utility.argparse import add_configuration_flags  # noqa: E402

import argparse  # noqa: E402
from typing import List, Callable  # noqa: E402

class MainRunner:
    main_services: Services

    def __init__(self, configuration: Configuration) -> None:
        self.main_services: Services = Services(configuration)
        self.run = self.main_services.debug.debug_func(DebugLevel.BASIC)(self.run)

    def run(self) -> None:
        if self.main_services.settings.generator:
            Generator.main(self)
        if self.main_services.settings.trainer:
            Trainer.main(self)
        if self.main_services.settings.analyzer:
            Analyzer.main(self)
        if self.main_services.settings.load_simulator:
            simulator: Simulator = Simulator(self.main_services)
            simulator.start()

        if self.main_services.settings.clear_cache:
            self.main_services.resources.cache_dir.clear()

def arg_valid(attr: str, args: argparse.Namespace) -> bool:
    if not getattr(args, attr):
        print("Invalid argument, {} is not enabled".format(attr), file=sys.stderr)
        return False
    return True

def configure_generator(config: Configuration, args: argparse.Namespace) -> bool:
    if args.generator:
        config.generator = True

    if args.room_size:
        if not arg_valid("generator", args):
            return False
        config.generator_min_room_size = args.room_size[0]
        config.generator_max_room_size = args.room_size[1]

    if args.fill_rate:
        if not arg_valid("generator", args):
            return False
        config.generator_obstacle_fill_min = args.fill_rate[0]
        config.generator_obstacle_fill_max = args.fill_rate[1]

    if args.generator_type:
        if not arg_valid("generator", args):
            return False
        config.generator_gen_type = args.generator_gen_type

    if args.num_maps:
        if not arg_valid("generator", args):
            return False
        config.generator_nr_of_examples = args.num_maps

    return True

def configure_analyzer(config: Configuration, args: argparse.Namespace) -> bool:
    if args.analyzer:
        config.analyzer = True

    return True

def configure_trainer(config: Configuration, args: argparse.Namespace) -> bool:
    if args.trainer:
        config.trainer = True

    return True

def configure_visualiser(config: Configuration, args: argparse.Namespace) -> bool:
    if args.visualiser:
        config.load_simulator = True
        config.simulator_graphics = True

    if args.visualiser_flags is not None and not arg_valid("visualiser", args):
        return False

    return True

def configure_common(config: Configuration, args: argparse.Namespace) -> bool:
    # for generator & analyzer
    config.num_dim = args.dims

    if args.include_builtin_algorithms:
        config.algorithms.update(AlgorithmManager.builtins)

    if args.list_maps:
        print("Available maps:")
        for key in MapManager.builtins.keys():
            print(f"  {key}")
        print("Can also specify a custom map,")
        print("  (1) cached map stored in Maps")
        print("  (2) external file that contains a global variable with type that inherits from Map")
        sys.exit(0)

    if args.maps:
        maps = MapManager.load_all(args.maps)
        if not all(maps):
            invalid_maps = [args.maps[i] for i in range(len(maps)) if not maps[i]]
            invalid_str = ",".join('"' + a + '"' for a in invalid_maps)
            valid_str = ",".join('"' + a + '"' for a in MapManager.builtins.keys())
            print(f"Invalid map(s) specified: {invalid_str}", file=sys.stderr)
            print(f"Available maps: {valid_str}", file=sys.stderr)
            print("Can also specify a custom map,", file=sys.stderr)
            print("  (1) cached map stored in Maps", file=sys.stderr)
            print("  (2) external file that contains a global variable with type that inherits from Map", file=sys.stderr)
            return False

        maps = list(flatten(maps, depth=1))

        # name uniqueness
        names = [a[0] for a in maps]
        if len(set(names)) != len(names):
            print("Name conflict detected in custom map list:", names, file=sys.stderr)
            return False

        maps = dict(maps)
        if args.include_default_builtin_maps or args.include_all_builtin_maps:
            maps.update(MapManager.builtins)
        if args.include_all_builtin_maps:
            maps.update(MapManager.cached_builtins)

        config.maps = maps
    elif args.include_all_builtin_maps:
        config.maps.update(MapManager.cached_builtins)

    return True

def configure_and_run(args: argparse.Namespace, configurers: List[Callable[[Configuration, argparse.Namespace], bool]]):
    config = Configuration()

    for c in configurers:
        if not c(config, args):
            return False

    if not configure_common(config, args) or \
       not configure_generator(config, args) or \
       not configure_analyzer(config, args) or \
       not configure_trainer(config, args) or \
       not configure_visualiser(config, args):
        return False

    mr = MainRunner(config)
    mr.run()
    return True

def main() -> bool:
    parser = argparse.ArgumentParser(prog="main.py",
                                     description="PathBench runner",
                                     formatter_class=argparse.RawTextHelpFormatter)

    configurers: List[Callable[[Configuration, argparse.Namespace], bool]] = []

    # Run arguments
    parser.add_argument("-v", "--visualiser", action='store_true', help="run visualiser (simulator with graphics)")
    parser.add_argument("-g", "--generator", action='store_true', help="run generator")
    parser.add_argument("-t", "--trainer", action='store_true', help="run trainer")
    parser.add_argument("-a", "--analyzer", action='store_true', help="run analyzer")

    # Visualiser arguments
    configurers.append(add_configuration_flags(parser, visualiser_flags=True, help_prefix="[visualiser] "))

    # Generator arguments
    parser.add_argument("--room-size", nargs=2, type=int, help="[generator] min/max room size, in format \"min max\"")
    parser.add_argument("--fill-rate", nargs=2, type=float, help="[generator] min/max fill rate in random fill rooms")
    parser.add_argument("--generator-type", choices=list(Generator.AVAILABLE_GENERATION_METHODS), help="[generator] generator type")
    parser.add_argument("--num-maps", type=int, help="[generator] number of maps to generate")

    # Miscellaneous
    parser.add_argument("--dims", type=int, help="[generator|analyzer] number of dimensions", default=3)

    configurers.append(add_configuration_flags(parser, algorithms_flags=True, multiple_algorithms_specifiable=True, help_prefix="[visualiser|analyzer] "))
    parser.add_argument("--include-builtin-algorithms", action='store_true',
                        help="[visualiser|analyzer] include all builtin algorithms even when a custom list is provided via '--algorithms'")

    parser.add_argument("--maps", help="[visualiser|analyzer|trainer] maps to load (either built-in map name or module file path)", nargs="+")
    parser.add_argument("--include-all-builtin-maps", action='store_true',
                        help="[visualiser|analyzer|trainer] include all builtin maps (includes all cached maps) even when a custom list is provided via '--maps'")
    parser.add_argument("--include-default-builtin-maps", action='store_true',
                        help="[visualiser|analyzer|trainer] include default builtin maps (does not include all cached maps) even when a custom list is provided via '--maps'")
    parser.add_argument("--list-maps", action="store_true", help="[visualiser|analyzer|trainer] output list of available built-in maps")

    configurers.append(add_configuration_flags(parser, deterministic_flags=True, debug_flag=True))

    args = parser.parse_args()
    print("args:{}".format(args))
    return configure_and_run(args, configurers)


if __name__ == "__main__":
    ret = main()
    exit_code = 0 if ret else 1
    sys.exit(exit_code)
