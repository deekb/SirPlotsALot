import math
import unittest
from VEXLib.Math import Shape


def create_shape_with_invalid_size():
    shape = Shape(0, 0)


def change_shape_with_invalid_size(shape, x_size, y_size):
    shape.x_size = x_size
    shape.y_size = y_size


class TestShape(unittest.TestCase):
    def setUp(self):
        self.x_size = 3
        self.y_size = 3
        self.shape = Shape(self.x_size, self.y_size)

    def test_shape_creation(self):
        self.assertEqual(self.shape.x_size, self.x_size)
        self.assertEqual(self.shape.y_size, self.y_size)

    def test_shape_creation_invalid_size(self):
        self.assertRaises(ValueError, create_shape_with_invalid_size)

    def test_change_size(self):
        shape = Shape(5, 5)
        self.assertEqual(shape.x_size, 5)
        self.assertEqual(shape.y_size, 5)
        shape.x_size = 1
        shape.y_size = 100

    def test_change_size_invalid_size(self):
        shape = Shape(5, 5)
        self.assertRaises(ValueError, change_shape_with_invalid_size, shape, 0, 0)
        self.assertRaises(ValueError, change_shape_with_invalid_size, shape, 0.5, 1)
        self.assertRaises(ValueError, change_shape_with_invalid_size, shape, 1, 0.75)
        self.assertRaises(ValueError, change_shape_with_invalid_size, shape, -1, 1)
        self.assertRaises(ValueError, change_shape_with_invalid_size, shape, 1, -1)
        self.assertRaises(ValueError, change_shape_with_invalid_size, shape, -1, -1)
        self.assertRaises(ValueError, change_shape_with_invalid_size, shape, math.inf, math.inf)


if __name__ == '__main__':
    unittest.main()
