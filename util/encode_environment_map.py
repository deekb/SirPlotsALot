from PIL import Image
import configparser
import os

# Load constants from config
config = configparser.ConfigParser()

UTIL_DIR = os.path.dirname(__file__)

os.chdir(os.pardir)

config.read("deploy_config.ini")

DEPLOY_DIRECTORY = os.path.abspath(config.get("Paths", "DEPLOY_DIRECTORY"))
BYTES_FOR_SIZE = 8

img = Image.open(os.path.join(UTIL_DIR, "environment_map.png"))
x_size, y_size = img.size


bit_list = []

# Analyze the image to determine obstacle positions
for y in range(y_size):
    for x in range(x_size):
        pixel = img.getpixel((x, y))
        bit_list.append(pixel != (0, 0, 0, 0))

# Pad bits up to the nearest byte
bit_list_extra_size = len(bit_list) % 8
bit_list.extend([1] * bit_list_extra_size)

byte_list = []

byte_index = 0
bit_index = 0
for bit in bit_list:
    if bit_index == 0:
        byte_list.append(int(bit))
    else:
        byte_list[byte_index] <<= 1
        byte_list[byte_index] |= bit

    bit_index += 1
    if bit_index % 8 == 0:
        byte_index += 1
        bit_index = 0

length_list = []

max_length = 2 ** (8 * BYTES_FOR_SIZE)

if x_size > max_length:
    raise ValueError(f"X size: {x_size} overflows the {BYTES_FOR_SIZE} bytes reserved for size, maximum size for {BYTES_FOR_SIZE} bytes is {max_length}")


for i in range(BYTES_FOR_SIZE):
    length_list.append(x_size & 0b11111111)
    x_size >>= 8

length_list.extend(byte_list)
byte_list = length_list

array_str = "".join([chr(byte) for byte in byte_list])

with open(os.path.join(DEPLOY_DIRECTORY, "obstacles.bin"), "w") as f:
    f.write(array_str)
