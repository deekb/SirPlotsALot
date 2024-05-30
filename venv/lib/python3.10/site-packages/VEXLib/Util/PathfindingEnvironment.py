BYTES_FOR_SIZE = 8


class PathfindingEnvironment:
    def __init__(self):
        self.obstacle_list = []
        self.width = None

    def load_from_file(self, file_object):
        with file_object as f:
            file_contents = f.read()
            length_list = [ord(char) for char in file_contents[:BYTES_FOR_SIZE]]
            length_byte = 0
            for byte in reversed(length_list):
                length_byte <<= 8
                length_byte |= byte

            self.width = length_byte
            print(f"Set width to {self.width}")
            self.obstacle_list = [ord(char) for char in file_contents[BYTES_FOR_SIZE:]]

    def load_from_list(self, obstacle_list, width):
        self.obstacle_list = obstacle_list
        self.width = width

    def get_at(self, x, y):
        bit_index = (y * self.width) + x

        byte_index = bit_index // 8

        bit_of_byte = bit_index % 8

        target_byte = self.obstacle_list[byte_index]

        target_bit = target_byte & (1 << (7 - bit_of_byte))

        return bool(target_bit)

    def set_at(self, x, y, value):
        value = bool(value)

        if self.get_at(y, x) is not value:
            # Check if the bit needs to be inverted
            bit_index = (x * self.width) + y

            byte_index = bit_index // 8

            bit_of_byte = bit_index % 8

            self.obstacle_list[byte_index] ^= (1 << (7 - bit_of_byte))  # Invert the bit

    def display_as_map(self, padding=2):
        for row in range(self.width):
            for col in range(self.width):
                value = self.get_at(row, col)
                if value:
                    print("■".ljust(padding), end="")
                else:
                    print("□".ljust(padding), end="")
            print()

    def is_available(self, position):
        return not self.get_at(*position)

    def is_collision(self, position):
        return self.get_at(*position)
