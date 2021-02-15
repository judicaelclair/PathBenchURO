import subprocess
import os
import sys
import time
from functools import partial
from typing import List, Tuple, Callable

def try_delete_file(fn) -> None:
    """
    Attempt to delete a file.

    :param fn: file to delete
    """

    try:
        os.remove(fn)
    except OSError as e:
        print(e, file=sys.stderr)

def handle_display_args(args) -> None:
    make_src_modules_importable()
    from utility.process import launch_process
    sys.path.pop(0) # remove src folder from path

    if 'DISPLAY' not in os.environ:
        args.spawn_display = ':99'

    if args.spawn_display:
        cmd = ["Xvfb", args.spawn_display, "-screen", "0", "2112x1376x24", "-fbdir", "/var/tmp"]
        if 'DISPLAY' in os.environ:
            def on_display_kill(display, *discard) -> None:
                os.environ['DISPLAY'] = display
            launch_process(cmd, partial(on_display_kill, os.environ['DISPLAY']))
        else:
            def on_display_kill(*discard) -> None:
                del os.environ['DISPLAY']
            launch_process(cmd, on_display_kill)
        
        os.environ['DISPLAY'] = args.spawn_display
        
        # wait for display to actually launch
        for _ in range(20):
            time.sleep(0.2)
            if os.path.exists("/var/tmp/Xvfb_screen0"):
                break

    if args.view_display:
        display = os.environ['DISPLAY'] if args.view_display == "auto" else args.view_display
        launch_process(["x11vnc", "-display", display, "-localhost"])
        launch_process(["vncviewer", "-display", ":0"])

def make_src_modules_importable() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
