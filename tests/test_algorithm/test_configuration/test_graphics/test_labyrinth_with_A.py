import time
import pyautogui
import os
import sys

sys.path.append(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
    "src"))
from constants import DATA_PATH

pyautogui.click(1003, 218)

# Select map Labyrinth, A* algorithm, update
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'Map.png'), confidence=0.5)
pyautogui.click(x + 160, y + 5)
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'Labyrinth.png'), confidence=0.5)
pyautogui.click(x, y)
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'Algorithm.png'), confidence=0.5)
pyautogui.click(x + 150, y)
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'A.png'), confidence=0.5)
pyautogui.click(x, y)
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'update.png'), confidence=0.5)
pyautogui.click(x, y)
pyautogui.press('w', presses=5500)

# pick colours and other modifications of the map
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'traversables.png'), confidence=0.5)
pyautogui.click(x - 78, y)
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'lightblue.png'), confidence=0.9)
pyautogui.click(x, y)

# start and end goals
pyautogui.rightClick(900, 964)
time.sleep(0.5)
pyautogui.click(1511, 815)
time.sleep(1)

pyautogui.press('t')
time.sleep(0.5)

# take texture ss
pyautogui.press('o')

# make traversables transparent for the full scene ss
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'traversables.png'), confidence=0.5)
pyautogui.click(x - 120, y)

# hide gui
pyautogui.press('c')
time.sleep(1)
pyautogui.press('v')
time.sleep(1)

pyautogui.press('p')
time.sleep(0.5)

# revert changes
pyautogui.press('c')
time.sleep(0.5)
pyautogui.press('v')
time.sleep(0.5)
x, y = pyautogui.locateCenterOnScreen(os.path.join(DATA_PATH, 'traversables.png'), confidence=0.5)
pyautogui.click(x - 120, y)
