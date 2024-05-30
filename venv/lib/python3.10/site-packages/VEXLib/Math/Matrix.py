import random
import time


class Shape:
    def __init__(self, x_size, y_size):
        if not isinstance(x_size, int) or not isinstance(y_size, int) or x_size <= 0 or y_size <= 0:
            raise ValueError("x_size and y_size must both be positive integers")
        self._x_size = x_size
        self._y_size = y_size

    @property
    def x_size(self):
        return self._x_size

    @x_size.setter
    def x_size(self, x_size):
        if not isinstance(x_size, int) or x_size <= 0:
            raise ValueError("x_size must be a positive integer")
        self._x_size = x_size

    @property
    def y_size(self):
        return self._y_size

    @y_size.setter
    def y_size(self, y_size):
        if not isinstance(y_size, int) or y_size <= 0:
            raise ValueError("y_size must be a positive integer")
        self._y_size = y_size

    def __repr__(self):
        return "<Shape x_size=" + str(self._x_size) + ", y_size=" + str(self._y_size) + ">"

    def __copy__(self):
        return Shape(self.x_size, self.y_size)


class Matrix:
    def __init__(self, shape, data=None):
        if shape.x_size <= 0 or shape.y_size <= 0:
            raise ValueError("Minimum matrix size is 1x1")
        self.shape = shape
        if data is None:
            self.data = []
            self.clear()
        else:
            self.data = data

    @classmethod
    def identity(cls, size):
        if size < 1:
            raise ValueError("Size must be at least 1")
        data = [[(1 if i == j else 0) for i in range(size)] for j in range(size)]

        return cls(shape=Shape(size, size), data=data)

    def clear(self):
        self.fill_with(0)

    def fill_with_random(self):
        self.data = [[(random.random() * 2) - 1 for _ in range(self.shape.x_size)] for _ in range(self.shape.y_size)]

    def fill_with(self, value):
        self.data = [[value] * self.shape.x_size for _ in range(self.shape.y_size)]

    def remove_row(self, row):
        del self.data[row]
        self.shape.y_size -= 1

    def remove_column(self, column):
        for row in self.data:
            del row[column]
        self.shape.x_size -= 1

    def is_square(self):
        return self.shape.x_size == self.shape.y_size

    def is_same_shape_as(self, other):
        return self.shape.x_size == other.shape.x_size and self.shape.y_size == other.shape.y_size

    def set_at(self, position, value):
        row_number, column_number = position
        self.data[column_number][row_number] = value

    def get_at(self, position):
        row_number, column_number = position
        return self.data[column_number][row_number]

    def __str__(self):
        return ",\n".join([str(row) for row in self.data])

    def __add__(self, other):
        if not self.is_same_shape_as(other):
            raise ValueError("Cannot add matrices with shapes " + str(self.shape) + " and " + str(other.shape))

        added_matrix_data = [[0 for _ in range(other.shape.x_size)] for _ in range(other.shape.y_size)]

        added_matrix_data = [[x1 + x2 for x1, x2 in zip(row, other_row)] for row, other_row in
                             zip(self.data, other.data)]

        return Matrix(shape=self.shape, data=added_matrix_data)

    def __sub__(self, other):
        if not self.is_same_shape_as(other):
            raise ValueError("Cannot subtract matrices with shapes " + str(self.shape) + " and " + str(other.shape))

        subtracted_matrix_data = [[x1 - x2 for x1, x2 in zip(row, other_row)] for row, other_row in
                                  zip(self.data, other.data)]

        return Matrix(shape=self.shape, data=subtracted_matrix_data)

    def __mul__(self, other):
        if isinstance(other, Matrix):
            assert self.shape.x_size == other.shape.y_size, "Size comparison failure"

            dot_product_matrix = Matrix(shape=Shape(other.shape.x_size, self.shape.y_size))

            for i in range(self.shape.x_size):
                for j in range(other.shape.y_size):
                    for k in range(self.shape.y_size):
                        dot_product_matrix.set_at((i, j), self.get_at((i, j)) * other.get_at((i, j)))

            return dot_product_matrix
        elif isinstance(other, (int, float)):
            dot_product_data = [[a * other for a in row] for row in self.data]
            return Matrix(shape=self.shape, data=dot_product_data)
        else:
            raise ValueError("Cannot multiply matrix by a value that is neither another matrix nor a scalar")

    def __truediv__(self, other):
        if isinstance(other, Matrix):
            if not self.is_same_shape_as(other):
                raise ValueError("Cannot divide matrix with shape " + str(self.shape) + " by matrix with shape " + str(other.shape))

            if any([j == 0 for sub in other.data for j in sub]):
                raise RuntimeError("Can't perform element-wise division by a matrix with an element that is zero")

            divided_matrix_data = [[x1 / x2 for x1, x2 in zip(row, other_row)] for row, other_row in
                                   zip(self.data, other.data)]

            return Matrix(shape=self.shape, data=divided_matrix_data)
        elif isinstance(other, (int, float)):
            divided_matrix_data = [[a / other for a in row] for row in self.data]
            return Matrix(shape=self.shape, data=divided_matrix_data)

    def __abs__(self):
        abs_matrix_data = [[abs(x) for x in row] for row in self.data]
        return Matrix(shape=self.shape, data=abs_matrix_data)

    def __eq__(self, other):
        return self.is_same_shape_as(other) and self.data == other.data

    def sum_of_all_elements(self):
        return sum(sum(row) for row in self.data)

    def maximum_of_all_elements(self):
        return max(max(row) for row in self.data)

    def minimum_of_all_elements(self):
        return min(min(row) for row in self.data)

    def average_of_all_elements(self):
        return self.sum_of_all_elements() / (self.shape.x_size * self.shape.y_size)

    def transpose(self):
        return Matrix(Shape(self.shape.y_size, self.shape.x_size), data=list(list(row) for row in zip(*self.data)))

    def copy(self):
        return Matrix(self.shape, [row[:] for row in self.data])

    def get_determinant_in_n_factorial_time(self):
        if not self.is_square():
            raise ValueError("Determinant can only be calculated for a square matrix")
        return self.slow_and_bad_determinant(self.data)

    def slow_and_bad_determinant(self, m):
        # Base case of recursive function: 1x1 matrix
        if len(m) == 1:
            return m[0][0]

        total = 0
        for column, element in enumerate(m[0]):
            # Exclude first row and current column.
            k = [x[:column] + x[column + 1:] for x in m[1:]]
            s = 1 if column % 2 == 0 else -1
            total += s * element * self.slow_and_bad_determinant(k)
        return total

    def inverse(self):
        identity = Matrix.identity(self.shape.x_size)


if __name__ == "__main__":
    # matrix = Matrix(shape=Shape(1, 1), data=[[5]])
    # print(matrix.slow_and_bad_determinant(matrix.data))

    i = 1
    while True:
        matrix = Matrix(shape=Shape(i, i))
        matrix.fill_with_random()
        start_time = time.perf_counter()
        print("Matrix data is:\n" + str(matrix))
        print("Determinant for above matrix is: " + str(matrix.get_determinant_in_n_factorial_time()))
        print("Found determinant of " + str(i) + "x" + str(i) + " matrix in " + str(round((time.perf_counter() - start_time) * 1000, 4)) + " MS\n\n")
        i += 1
