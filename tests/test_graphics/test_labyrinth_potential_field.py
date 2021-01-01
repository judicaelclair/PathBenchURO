import time
import os
import glob
import cv2 as cv
import unittest

if __name__ == "__main__":
    from common import init, destroy, mse, wait_for, screenshot_saved
else:
    from .common import init, destroy, mse, wait_for, screenshot_saved


def graphics_test() -> None:
    from utility.constants import DATA_PATH, TEST_DATA_PATH
    import pyautogui

    # Select map Labyrinth, Potential Field algorithm
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'map.png'), confidence=0.5)
    pyautogui.click(x + 160, y + 5)
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'labyrinth_new.png'), confidence=0.5)
    pyautogui.click(x, y)
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'algorithm_new.png'), confidence=0.5)
    pyautogui.click(x + 150, y)
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'potential_field.png'), confidence=0.9)
    pyautogui.click(x, y)

    # start and end goals coordinate input
    pyautogui.click(342, 545)
    pyautogui.write('17')
    pyautogui.doubleClick(422, 545)
    pyautogui.write('15')
    pyautogui.doubleClick(342, 617)
    pyautogui.write('17')
    pyautogui.doubleClick(422, 617)
    pyautogui.write('4')

    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'update.png'), confidence=0.5)
    pyautogui.click(x, y)
    wait_for('initialised.png')

    # pick colours and do other modifications on the map
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'traversables_new.png'), confidence=0.5)
    pyautogui.click(x - 85, y)
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'lime.png'), confidence=0.9)
    pyautogui.click(x, y)

    pyautogui.press('t')
    wait_for('done.png')

    # take texture ss
    file_num = len(glob.glob(os.path.join(DATA_PATH, 'screenshots/*.png')))
    pyautogui.press('o')
    screenshot_saved(file_num)

    # get latest screenshot
    list_of_ss = glob.glob(os.path.join(DATA_PATH, 'screenshots/*.png'))
    transparent_1 = max(list_of_ss, key=os.path.getctime)

    time.sleep(2)

    # compare the new screenshot with the expected one
    expected_transparent_1 = cv.imread(os.path.join(TEST_DATA_PATH, "potential_field_2d.png"))
    transparent_1 = cv.imread(transparent_1)

    THRESHOLD = 30
    mse_1 = mse(expected_transparent_1, transparent_1)
    assert mse_1 < THRESHOLD, mse_1


class GraphicsTestCase(unittest.TestCase):
    def test(self):
        try:
            init()
            graphics_test()
        finally:
            destroy()


if __name__ == "__main__":
    GraphicsTestCase().test()
