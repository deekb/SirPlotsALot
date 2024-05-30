import os
import pygame
import threading
import time
import socket

# Socket parameters
HOST = "192.168.1.1"
PORT = 10002  # Port to connect to (non-privileged ports are >= 1024)
SOCKET_RECONNECT_INTERVAL_IN_SECONDS = 1

resources_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")

print(f"Loading resources from: {resources_directory}")

TARGET_FPS = 30
DISPLAY_SCALING_FACTOR = 400
PLOTTER_SIZE = (6, 5)

UP = 1
DOWN = 2

pygame.init()

pygame.display.set_caption("Plotter Interface")

screen = pygame.display.set_mode((PLOTTER_SIZE[0] * DISPLAY_SCALING_FACTOR, PLOTTER_SIZE[1] * DISPLAY_SCALING_FACTOR))
points = []

clock = pygame.time.Clock()


class NetworkHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.attempting_socket_connection = False

        self.shutdown_triggered = False

    def attempt_connection(self, retry_on_failure=True):
        if self.attempting_socket_connection:
            print("[attempt_connection]: Warning: Another thread is already attempting to reconnect the socket")
            return
        self.attempting_socket_connection = True
        first_try = True
        while (first_try or retry_on_failure) and not self.shutdown_triggered:
            try:
                print("attempt connect")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(1)
                self.socket.connect((self.host, self.port))
                break
            except (ConnectionRefusedError, ConnectionAbortedError, socket.gaierror, OSError):
                print(f"Reconnect attempt failed, retrying in {SOCKET_RECONNECT_INTERVAL_IN_SECONDS} seconds")
                time.sleep(SOCKET_RECONNECT_INTERVAL_IN_SECONDS)
            first_try = False
        if self.shutdown_triggered:
            print("Shutdown triggered while attempting reconnection to the socket")
        else:
            self.socket.settimeout(1)
            print("Successfully reconnected to the socket")
            self.attempting_socket_connection = False

    def start_network_loop(self):
        self.attempt_connection()
        while not self.shutdown_triggered:
            received = self.get_messages()
            if not received:
                continue

            for line in received:
                if not line:
                    continue
                print(line)

    def send_message(self, message, end="\n"):
        if self.attempting_socket_connection or self.socket is None:
            return  # No socket connected
        try:
            self.socket.sendall((str(message) + str(end)).encode())
        except (ConnectionResetError, BrokenPipeError):
            if not self.attempting_socket_connection:
                print("[send_message]: Robot socket disconnected, attempting reconnect...")
                self.attempt_connection()

    def get_messages(self):
        try:
            received = self.socket.recv(1024)
            if not received:
                if not self.attempting_socket_connection:
                    print("[get_messages]: Got no data, assuming robot socket disconnected, attempting reconnect...")
                    self.attempt_connection()
            return received.decode().split("\n")
        except socket.timeout:
            pass
        except (ConnectionResetError, BrokenPipeError, OSError,) as e:
            print(f"get_messages failed: {e}")
            if not self.attempting_socket_connection:
                print("[get_messages]: Robot socket disconnected, attempting reconnect...")
                self.attempt_connection()

    def communications_online(self):
        return not self.attempting_socket_connection

    def restart_rpi(self):
        self.send_message("RPI:RESTART")

    def restart_rpi_bridge(self):
        self.send_message("RPI:RESTART_BRIDGE")

    def shutdown(self):
        self.shutdown_triggered = True


def scale_point(point, scale):
    return point[0] * scale, point[1] * scale


def convert_point_type(point, window_size):
    return point[0], window_size[1] - point[1]


def render_path():
    global screen, points
    # fill the screen with a color to wipe away anything from the last frame
    screen.fill("white")
    prev_point = None

    for point in points:
        if isinstance(point, tuple):
            point = scale_point(convert_point_type(point, (5, 5)), DISPLAY_SCALING_FACTOR)

            pygame.draw.circle(screen, (0, 0, 0), point, 3)
            if isinstance(prev_point, tuple):
                print(prev_point)
                pygame.draw.line(screen, (0, 0, 0), prev_point, point)
            prev_point = point
        else:
            if point == UP:
                prev_point = point
            if point == DOWN:
                prev_point = point

    pygame.draw.rect(screen, (0, 255, 0), [scale_point(convert_point_type((5, 5), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR), scale_point(convert_point_type((6, 2.5), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR)])
    pygame.draw.rect(screen, (255, 0, 0), [scale_point(convert_point_type((5, 2.5), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR), scale_point(convert_point_type((6, 1), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR)])
    pygame.draw.rect(screen, (255, 255, 0), [scale_point(convert_point_type((5, 1), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR), scale_point(convert_point_type((6, 0), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR)])

    text = pygame.font.SysFont("Arial", int(0.3 * DISPLAY_SCALING_FACTOR))
    clear_text = text.render("Clear", True, (0, 0, 0))
    up_text = text.render("Up", True, (0, 0, 0))
    down_text = text.render("Down", True, (0, 0, 0))

    screen.blit(clear_text, scale_point(convert_point_type((5, 1), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR))
    screen.blit(up_text, scale_point(convert_point_type((5, 5), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR))
    screen.blit(down_text, scale_point(convert_point_type((5, 2.5), PLOTTER_SIZE), DISPLAY_SCALING_FACTOR))

    pygame.display.flip()


def main():
    global points
    network_handler = NetworkHandler(HOST, PORT)
    network_thread = threading.Thread(target=network_handler.start_network_loop)

    clock = pygame.time.Clock()
    running = True
    network_thread.start()

    # Render an empty field
    render_path()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if any(pygame.mouse.get_pressed()):
            click_position = convert_point_type(scale_point(pygame.mouse.get_pos(), 1 / DISPLAY_SCALING_FACTOR),
                                                PLOTTER_SIZE)

            if click_position[0] >= 5.0:
                print("Button press")
                if click_position[1] >= PLOTTER_SIZE[1] / 2:
                    print("UP")
                    network_handler.send_message("UP")
                    # points.append(UP)
                elif PLOTTER_SIZE[1] / 2 > click_position[1] > 1:
                    print("DOWN")
                    network_handler.send_message("DOWN")
                    # points.append(DOWN)
                elif click_position[1] <= 1:
                    print("CLEAR")
                    network_handler.send_message("CLEAR")
                    points.clear()
            else:
                if pygame.mouse.get_pressed()[0]:  # Left click
                    print("Left click at position:", click_position)
                    # if points and isinstance(points[-1], tuple) :
                    #     if abs(math.dist(points[-1], click_position)) >= 0:
                    network_handler.send_message("GOTO:" + str(click_position[0]) + "|" + str(click_position[1]))
                    points.append(click_position)
                    # else:
                    #     points.append(click_position)

                elif pygame.mouse.get_pressed()[2]:  # Right click
                    print("Right click at position:", click_position)

            render_path()

        clock.tick(TARGET_FPS)

    network_handler.shutdown()
    pygame.quit()


if __name__ == "__main__":
    main()
