import unittest, copy

from structures import Point


class TestPoint(unittest.TestCase):
    def test_copy(self) -> None:
        point1: Point = Point(2, 3)
        point2: Point = copy.copy(point1)
        self.assertEqual(point1, point2)

    def test_deep_copy(self) -> None:
        point1: Point = Point(2, 3)
        point2: Point = copy.deepcopy(point1)
        self.assertEqual(point1, point2)

    def test_str(self) -> None:
        point = Point(2, 3)
        self.assertEqual("Point(x=2, y=3)", str(point))

    def test_str_3D(self) -> None:
        point = Point(2, 3, 4)
        self.assertEqual("Point(2, 3, 4)", str(point))

    def test_eq(self) -> None:
        point1: Point = Point(2, 3)
        point2: Point = Point(2, 3)
        self.assertEqual(point1, point2)

    def test_eq_3D(self) -> None:
        point1: Point = Point(2, 3, 4)
        point2: Point = Point(2, 3, 4)
        self.assertEqual(point1, point2)

    def test_ne_pos(self) -> None:
        point1: Point = Point(2, 3)
        point2: Point = Point(2, 5)
        self.assertNotEqual(point1, point2)

    def test_ne_dim(self) -> None:
        point1: Point = Point(2, 3)
        point2: Point = Point(2, 3, 0)
        self.assertNotEqual(point1, point2)

    def test_ne_instance(self) -> None:
        point1: int = 2
        point2: Point = Point(2, 3)
        self.assertNotEqual(point1, point2)


if __name__ == '__main__':
    TestEntity().run()
