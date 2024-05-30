import unittest
import random
from VEXLib.Math import Shape, Matrix


MATRIX_SHAPE_3X3 = Shape(3, 3)

MATRIX_1_THROUGH_9_3X3_DATA = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

MATRIX_9_THOUGH_1_3X3_DATA = [
    [9, 8, 7],
    [6, 5, 4],
    [3, 2, 1]
]


class TestMatrix(unittest.TestCase):
    def setUp(self):
        self.shape = MATRIX_SHAPE_3X3
        self.matrix_data = MATRIX_1_THROUGH_9_3X3_DATA
        self.matrix = Matrix(self.shape, self.matrix_data)

    def test_matrix_creation(self):
        self.assertEqual(self.matrix.shape, self.shape)
        self.assertEqual(self.matrix.data, self.matrix_data)

    def test_matrix_addition(self):
        other_matrix_data = MATRIX_9_THOUGH_1_3X3_DATA
        other_matrix = Matrix(self.shape, other_matrix_data)

        result = self.matrix + other_matrix
        expected_data = [
            [10, 10, 10],
            [10, 10, 10],
            [10, 10, 10]
        ]
        self.assertEqual(result.data, expected_data)

    def test_matrix_subtraction(self):
        other_matrix = Matrix(self.shape, MATRIX_1_THROUGH_9_3X3_DATA)

        result = self.matrix - other_matrix
        expected_data = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]
        self.assertEqual(result.data, expected_data)

    def test_matrix_multiplication(self):
        scalar = 2
        result = self.matrix * scalar
        expected_data = [
            [2, 4, 6],
            [8, 10, 12],
            [14, 16, 18]
        ]
        self.assertEqual(result.data, expected_data)

        # Test matrix-matrix multiplication
        other_matrix_data = [
            [2, 0, 1],
            [1, 0, 2],
            [0, 1, 1]
        ]
        other_matrix = Matrix(self.shape, other_matrix_data)
        result = self.matrix * other_matrix
        expected_data = [
            [2, 0, 3],
            [4, 0, 12],
            [0, 8, 9]
        ]
        self.assertEqual(result.data, expected_data)

    def test_matrix_division(self):
        scalar = 2
        result = self.matrix / scalar
        expected_data = [
            [0.5, 1.0, 1.5],
            [2.0, 2.5, 3.0],
            [3.5, 4.0, 4.5]
        ]
        self.assertEqual(result.data, expected_data)

        # Test matrix-matrix division
        other_matrix_data = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ]
        other_matrix = Matrix(self.shape, other_matrix_data)
        result = self.matrix / other_matrix
        expected_data = [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ]
        self.assertEqual(result.data, expected_data)

    def test_matrix_transpose(self):
        transposed_matrix = self.matrix.transpose()
        expected_data = [
            [1, 4, 7],
            [2, 5, 8],
            [3, 6, 9]
        ]
        self.assertEqual(transposed_matrix.data, expected_data)

    def test_matrix_copy(self):
        copied_matrix = self.matrix.copy()
        self.assertEqual(copied_matrix.data, self.matrix_data)
        self.assertEqual(copied_matrix.shape, self.shape)

    def test_matrix_determinant(self):
        determinant = self.matrix.get_determinant_in_n_factorial_time()
        self.assertEqual(determinant, 0)  # Determinant of the provided matrix is 0

        # Additional test cases for determinant
        # Case: Identity matrix
        identity_matrix = Matrix(self.shape, data=[[1, 0, 0],
                                                   [0, 1, 0],
                                                   [0, 0, 1]])

        self.assertEqual(identity_matrix.get_determinant_in_n_factorial_time(), 1)

        # Case: Diagonal matrix
        diagonal_matrix_data = [
            [2, 0, 0],
            [0, 3, 0],
            [0, 0, 4]
        ]
        diagonal_matrix = Matrix(self.shape, diagonal_matrix_data)
        self.assertEqual(diagonal_matrix.get_determinant_in_n_factorial_time(), 24)

        # Case: arbitrary matrix
        arbitrary_matrix_data = [[1, 2, 3],
                                 [3, 2, 1],
                                 [2, 1, 3]]

        arbitrary_matrix = Matrix(self.shape, arbitrary_matrix_data).transpose()
        self.assertEqual(arbitrary_matrix.get_determinant_in_n_factorial_time(), -12)

        # Case: Random matrix
        random.seed(42)
        random_matrix = Matrix(self.shape)
        random_matrix.fill_with_random()
        determinant_random_matrix = random_matrix.get_determinant_in_n_factorial_time()

    def test_matrix_fill_with_random(self):
        self.matrix.fill_with_random()
        self.assertTrue(all(-1 <= value <= 1 for row in self.matrix.data for value in row))

    def test_matrix_is_square(self):
        self.assertTrue(self.matrix.is_square())
        non_square_shape = Shape(2, 3)
        non_square_matrix = Matrix(non_square_shape)
        self.assertFalse(non_square_matrix.is_square())


if __name__ == '__main__':
    unittest.main()
