import time
import pyautogui
import os
import sys

if __name__ == "__main__":
    from common import init, launch_visualiser
else:
    from .common import init, launch_visualiser

init()
launch_visualiser()

from constants import TEST_DATA_PATH  # noqa: E402


# Pick 3d cube with RRT
x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'map.png'), confidence=0.5)
pyautogui.click(x + 160, y + 5)
x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, '3d_cube.png'), confidence=0.9)
pyautogui.click(x, y)
x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'algorithm.png'), confidence=0.5)
pyautogui.click(x + 150, y)
x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'rrt2.png'), confidence=0.9)
pyautogui.click(x, y)
x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'update.png'), confidence=0.5)
pyautogui.click(x, y)
time.sleep(5)

# rotate map to pick a pos
pyautogui.press('a', presses=5500)
time.sleep(0.5)
pyautogui.rightClick(997, 532)

# make traversables transparent for the RRT
x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'traversables.png'), confidence=0.5)
pyautogui.click(x - 120, y)

# #run algo
pyautogui.press('t')
time.sleep(1)

# take ss
pyautogui.press('o')
time.sleep(1)

# hide gui
pyautogui.press('c')
time.sleep(0.5)
pyautogui.press('v')
time.sleep(1)

# take scene ss
pyautogui.press('p')
time.sleep(1)

# restore changes
pyautogui.press('v')
time.sleep(0.5)
pyautogui.press('c')
time.sleep(0.5)
x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'traversables.png'), confidence=0.5)
pyautogui.click(x - 120, y)