from VEXLib.Algorithms.DijkstraPathfinding import DijkstraPathfinding
import time
import pygame
import os


resources_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")

print(f"Loading resources from: {resources_directory}")

TARGET_FPS = 60
DISPLAY_SCALING_FACTOR = 16
FIELD_SIZE = (122, 122)

pygame.init()

pygame.display.set_caption("Dijkstra Pathfinding Simulation")

background_image = pygame.image.load(os.path.join(resources_directory, "Pathfinding_Obstacles_3_to_1.png"))

background_image = pygame.transform.scale(
    background_image,
    (
        background_image.get_width() * DISPLAY_SCALING_FACTOR,
        background_image.get_height() * DISPLAY_SCALING_FACTOR,
    ),
)

background_rect = background_image.get_rect()

screen = pygame.display.set_mode((background_rect.width, background_rect.height))

clock = pygame.time.Clock()


def scale_point(point, scale):
    return point[0] * scale, point[1] * scale


def convert_point_type(point, window_size):
    return point[0], window_size[1] - point[1]


def get_path(start_position, target_position):

    valid_moves = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    # valid_moves = [(-1, 0), (0, 1), (1, 0), (0, -1)]

    dijkstra = DijkstraPathfinding(start_position, target_position, open(os.path.join(os.pardir, "deploy", "obstacles.bin"), "r"), valid_moves)

    start_time = time.perf_counter()

    try:
        path, visited_tiles = dijkstra.find_path()
    except AssertionError as e:
        print("Assertion Error:", e)
        path, visited_tiles = [], []

    print(
        f"[{__file__}]: Search took: {round((time.perf_counter() - start_time) * 1000)}ms"
    )

    return path, visited_tiles


def render_path(path, visited_tiles):
    global background_image, background_rect, screen

    new_path = []
    for point in path:
        new_path.append(
            convert_point_type(
                scale_point(point, DISPLAY_SCALING_FACTOR),
                (
                    FIELD_SIZE[0] * DISPLAY_SCALING_FACTOR,
                    FIELD_SIZE[1] * DISPLAY_SCALING_FACTOR,
                ),
            )
        )
        new_path[-1] = (
            new_path[-1][0] - DISPLAY_SCALING_FACTOR / 2,
            new_path[-1][1] - DISPLAY_SCALING_FACTOR / 2,
        )

    new_visited = []
    for point in visited_tiles:
        new_visited.append(
            convert_point_type(
                scale_point(point, DISPLAY_SCALING_FACTOR),
                (
                    FIELD_SIZE[0] * DISPLAY_SCALING_FACTOR,
                    FIELD_SIZE[1] * DISPLAY_SCALING_FACTOR,
                ),
            )
        )
        new_visited[-1] = (
            new_visited[-1][0] - DISPLAY_SCALING_FACTOR / 2,
            new_visited[-1][1] - DISPLAY_SCALING_FACTOR / 2,
        )
    # fill the screen with a color to wipe away anything from the last frame
    screen.fill("white")

    screen.blit(background_image, background_rect)

    for i, point in enumerate(new_visited):
        if point == new_path[0]:  # Draw the first point in the path red
            pygame.draw.rect(
                screen,
                (0, 255, 0),
                (*new_path[0], DISPLAY_SCALING_FACTOR, DISPLAY_SCALING_FACTOR),
            )
        elif point == new_path[-1]:  # Draw the last point in the path green
            pygame.draw.rect(
                screen,
                (255, 0, 0),
                (*new_path[-1], DISPLAY_SCALING_FACTOR, DISPLAY_SCALING_FACTOR),
            )
        elif point in new_path:  # Draw the rest of the path solid black
            pygame.draw.rect(
                screen,
                (0, 0, 0),
                (point[0], point[1], DISPLAY_SCALING_FACTOR, DISPLAY_SCALING_FACTOR),
            )
        else:  # Draw explored (but not accepted) solutions as black outlined boxes
            pygame.draw.rect(
                screen,
                (0, 0, 0),
                (point[0], point[1], DISPLAY_SCALING_FACTOR, DISPLAY_SCALING_FACTOR),
                1,
            )
            # clock.tick(100)
            # pygame.display.flip()

        # if i % 5 == 0:
        #     pygame.display.flip()

    # Update the display
    pygame.display.flip()


def main():
    start_position = (37, 60)
    target_position = (110, 58)

    clock = pygame.time.Clock()
    running = True

    # Render an empty field
    render_path([], [])

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                click_position = convert_point_type(
                    scale_point(pygame.mouse.get_pos(), 1 / DISPLAY_SCALING_FACTOR),
                    (122, 122),
                )
                click_position = round(click_position[0]), round(click_position[1])

                if event.button == 1:  # Left click
                    print("Left click at position:", click_position)
                    start_position = click_position
                elif event.button == 3:  # Right click
                    print("Right click at position:", click_position)
                    target_position = click_position
                path, visited_tiles = get_path(start_position, target_position)
                render_path(path, visited_tiles)

        clock.tick(TARGET_FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
