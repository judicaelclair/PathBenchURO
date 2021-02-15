import Xlib.display
import numpy as np
import cv2 as cv

import atexit
import subprocess
import sys
import os
import time
import argparse
import glob
from typing import List, Optional, Callable, Tuple

# add 'PathBench/tests' to system path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import make_src_modules_importable, handle_display_args, try_delete_file  # noqa: E402

# add src folder to system path
make_src_modules_importable()

from utility.process import launch_process, kill_processes  # noqa: E402
from utility.constants import SRC_PATH, DATA_PATH, TEST_DATA_PATH  # noqa: E402
from simulator.services.resources.directory import Directory  # noqa: E402

g_restore_resources: bool = False


def setup(args: argparse.Namespace, visualiser_args: List[str]) -> None:
    global g_restore_resources

    atexit.register(destroy)

    handle_display_args(args)

    g_restore_resources = not args.no_restore_resources_at_exit

    if not args.no_rm_config_file:
        try_delete_file("./.pathbench.json")

    # import pyautogui after setting up virtual display otherwise import
    # will fail on system with no display as $DISPLAY hasn't been set.
    import pyautogui

    # enforce correct display being used
    pyautogui._pyautogui_x11._display = Xlib.display.Display(os.environ['DISPLAY'])

    # Fall back to sys executable if no env variable to specify how to run with codecov
    executable_name = os.environ.get("CODECOV_EXEC", sys.executable)
    print(f"Using executable {executable_name}")

    if not args.no_launch_visualiser:
        launch_process([executable_name, os.path.join(SRC_PATH, 'main.py'), '-d', args.debug, '-v', '-Vwindowed-fullscreen',
                        '-Vaudio-library-name=null', '--deterministic'] + visualiser_args,
                        on_kill=lambda _: pyautogui.press('esc'))

        pyautogui.moveTo(1, 1)
        wait_for('update.png')


def init(no_restore_resources_at_exit: bool = False, no_launch_visualiser: bool = False,
         no_rm_config_file: bool = False, visualiser_args: List[str] = []) -> None:
    parser = argparse.ArgumentParser(prog="common.py",
                                     description="PathBench individual test initialiser",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--spawn-display", nargs='?', default=None, const=":99",
                        help="spawn a virtual display for testing graphics and sets $DISPLAY")
    parser.add_argument("--view-display", nargs='?', default=None, const="auto",
                        help="open an interactive view of a virtual display (defaults to view $DISPLAY)")
    parser.add_argument("--no-restore-resources-at-exit", action="store_true",
                        help="do not restore and clean resources folder when test exits")
    parser.add_argument("--no-launch-visualiser", action="store_true", help="do not launch PathBench visualiser")
    parser.add_argument("--no-rm-config-file", action="store_true", help="do not delete PathBench configuration file")
    parser.add_argument("-d", "--debug", choices=['NONE', 'BASIC', 'LOW', 'MEDIUM', 'HIGH'], default='NONE',
                        help="set the debug level when running, default is none")

    if no_restore_resources_at_exit:
        sys.argv.append("--no-restore-resources-at-exit")

    if no_launch_visualiser:
        sys.argv.append("--no-launch-visualiser")

    if no_rm_config_file:
        sys.argv.append("--no-rm-config-file")

    args, rem_args = parser.parse_known_args()
    print("args:{}".format(args))

    setup(args, visualiser_args + rem_args)


def destroy() -> None:
    global g_restore_resources

    kill_processes()

    if g_restore_resources:
        restore_resources()

    atexit.unregister(destroy)


def restore_resources() -> None:
    cmd = ["git", "restore", "--source=HEAD", "--staged", "--worktree", "--", DATA_PATH]
    subprocess.check_call(cmd)

    cmd = ["git", "clean", "-dxf", "--", DATA_PATH]
    subprocess.check_call(cmd)


def wait_for(rel_img: str, delay: float = 0.5, max_it: int = 30, confidence: float = 0.5) -> None:
    import pyautogui  # cannot be done globally due to $DISPLAY madness

    img = os.path.join(TEST_DATA_PATH, rel_img)
    for _ in range(max_it):
        time.sleep(delay)
        try:
            if pyautogui.locateCenterOnScreen(img, confidence=confidence) is not None:
                return
        except pyautogui.PyAutoGUIException:
            continue
    raise RuntimeError("Unable to locate '{}' on screen".format(img))


# Lower values better
def mse(img_a: np.ndarray, img_b: np.ndarray) -> float:
    err = np.sum((img_a.astype("float") - img_b.astype("float")) ** 2)
    err /= float(img_a.shape[0] * img_a.shape[1])
    return err

def compare_images(img_a_path: str, img_b_path: str, threshold: float = 300, delay: float = 0.8, max_it: int = 10) -> None:
    def read(path) -> np.ndarray:
        # saving 4K images can take a while, therefore it's
        # likely the read will fail due to partially images

        path = os.path.join(TEST_DATA_PATH, path)
        for _ in range(max_it):
            data = cv.imread(path)
            if data is not None:
                return data
            time.sleep(delay)
        assert data, "unable to load image"

    # load images
    img_a = read(img_a_path)
    img_b = read(img_b_path)

    # check difference
    diff = mse(img_a, img_b)
    assert diff < threshold, diff

def take_screenshot(ref_path: str = None, threshold: float = 300, delay: float = 0.8, max_it: int = 30, max_tries: int = 3) -> str:
    import pyautogui  # cannot be done globally due to $DISPLAY madness

    for t in range(max_tries):
        # get screenshot file path
        metadata: Dict[str, any] = Directory._unpickle("metadata", DATA_PATH + "/screenshots/")
        if metadata is None:
            metadata = {
                "next_index": 0,
            }
        file_path = os.path.join(os.path.join(DATA_PATH, "screenshots"), "screenshot_{}.png".format(metadata["next_index"]))

        for _ in range(max_it):
            # take screenshot, doesn't matter
            # if we take multiple ones
            pyautogui.press('o')

            time.sleep(delay)

            # check if screenshot was taken (& saved)
            if os.path.exists(file_path):
                break

        if ref_path is not None:
            try:
                compare_images(file_path, ref_path, threshold)
            except AssertionError:
                if t + 1 == max_tries:
                    raise
                else:
                    continue

        return file_path
