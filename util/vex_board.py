import os
import threading
import time
import socket
import pyglet
from pyglet import image
import math

from pyglet.gui import PushButton

# Socket parameters
HOST = "192.168.1.1"
PORT = 10002  # Port to connect to (non-privileged ports are >= 1024)
SOCKET_RECONNECT_INTERVAL_IN_SECONDS = 1

# Ping parameters
RPI_PING_FREQUENCY_IN_SECONDS = 1
ROBOT_PING_FREQUENCY_IN_SECONDS = 0.25
PING_ROBOT_MESSAGE = "PING"
PING_RPI_MESSAGE = "NONE"

# Heartbeat parameters
ONLINE_THRESHOLD_IN_SECONDS = 0.5

os.chdir(os.path.abspath(os.path.dirname(__name__)))
icon = image.load("Vex_Simulation_Logo.png")

pyglet.resource.path = ['icons']
pyglet.resource.reindex()

pyglet.font.add_file('Aller_Rg.ttf')
aller = pyglet.font.load('Aller', 16)


def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{str(int(hours)).zfill(2)}:{str(int(minutes)).zfill(2)}:{str(round(seconds)).zfill(2)}"


def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "ZB", "YB")
    i = int(math.floor((math.log(size_bytes, 1024))))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


class VexBoardWidget:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def update_value(self, new_value):
        self.value = new_value


class VexBoard:
    def __init__(self):
        self.widgets = {}

    def add_widget(self, name, initial_value):
        self.widgets[name] = VexBoardWidget(name, initial_value)

    def update_widget(self, name, new_value):
        if name in self.widgets:
            self.widgets[name].update_value(new_value)
        else:
            print(f"Widget \"{name}\" does not exist.")


class NetworkHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # self.vex_log = vex_log
        self.socket = None
        self.attempting_socket_connection = False

        self.shutdown_triggered = False

        self.last_ping_send_time_in_seconds = 0
        self.last_ping_response_time_in_milliseconds = 0
        self.last_heartbeat_time_in_seconds = 0

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
                for widget in vex_board.widgets:
                    if line.startswith(widget):
                        try:
                            if "memory" in widget.lower():
                                vex_board.update_widget(widget, format_size(int(line[len(widget) + 1:])) + " (" + str(
                                    round((int(line[len(widget) + 1:]) / 1024512) * 100)) + "%)")
                            elif "time" in widget.lower():
                                vex_board.update_widget(widget, format_time(float(line[len(widget) + 1:])))
                            else:
                                vex_board.update_widget(widget, line[len(widget) + 1:])
                        except Exception as e:
                            print(e)

                if "PING" in line:
                    self.last_ping_response_time_in_milliseconds = (
                                                                               time.monotonic() - self.last_ping_send_time_in_seconds) * 1000
                if "ROBOT_HEARTBEAT" in line:
                    self.last_heartbeat_time_in_seconds = time.monotonic()

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

    def ping_robot(self):
        if self.socket is not None:
            self.send_message(PING_ROBOT_MESSAGE)
            self.last_ping_send_time_in_seconds = time.monotonic()
            # print("PING -> Robot")

    def ping_rpi(self):
        if self.socket is not None:
            self.send_message(PING_RPI_MESSAGE)
            self.last_ping_send_time_in_seconds = time.monotonic()
            # print("PING -> RPI")
            self.get_messages()

    def ping_robot_loop(self):
        while not self.shutdown_triggered:
            self.ping_robot()
            time.sleep(ROBOT_PING_FREQUENCY_IN_SECONDS)

    def ping_rpi_loop(self):
        while not self.shutdown_triggered:
            self.ping_rpi()
            time.sleep(RPI_PING_FREQUENCY_IN_SECONDS)

    def communications_online(self):
        return not self.attempting_socket_connection

    def robot_is_online(self, online_threshold_in_seconds=ONLINE_THRESHOLD_IN_SECONDS):
        time_since_heartbeat = (time.monotonic() - self.last_heartbeat_time_in_seconds)
        return time_since_heartbeat < online_threshold_in_seconds

    def robot_ping_time(self):
        return self.last_ping_response_time_in_milliseconds

    def restart_rpi(self):
        self.send_message("RPI:RESTART")

    def restart_rpi_bridge(self):
        self.send_message("RPI:RESTART_BRIDGE")

    def shutdown(self):
        self.shutdown_triggered = True


class VexBoardWindow(pyglet.window.Window):
    def __init__(self, width, height, vex_board, network_handler: NetworkHandler):
        super().__init__(width, height, "VexBoard")
        self.vex_board = vex_board
        self.network_handler = network_handler
        self.labels = {}
        self.new_widget_position_y = self.height
        self.new_widget_position_x = 10

        self.rpi_online_image = pyglet.sprite.Sprite(pyglet.resource.image("access-point-1.png"), x=0, y=64)
        self.rpi_offline_image = pyglet.sprite.Sprite(pyglet.resource.image("access-point-off-1.png"), x=0, y=64)

        self.robot_online_image = pyglet.sprite.Sprite(pyglet.resource.image("robot-outline-1.png"), x=0, y=0)
        self.robot_offline_image = pyglet.sprite.Sprite(pyglet.resource.image("robot-off-outline-1.png"), x=0, y=0)

        self.rpi_status_label = pyglet.text.Label("Offline",
                                                  x=64,
                                                  y=64,
                                                  font_size=40,
                                                  anchor_x='left',
                                                  anchor_y='bottom',
                                                  color=(255, 0, 0, 255),
                                                  font_name="Aller",
                                                  )

        self.robot_status_label = pyglet.text.Label("Offline",
                                                    x=64,
                                                    y=0,
                                                    font_size=40,
                                                    anchor_x='left',
                                                    anchor_y='bottom',
                                                    color=(255, 0, 0, 255),
                                                    font_name="Aller",
                                                    )

        self.ping_time_label = pyglet.text.Label(f"Offline",
                                                 font_size=20,
                                                 x=self.width,
                                                 y=self.height,
                                                 anchor_x='right',
                                                 anchor_y='top',
                                                 color=(255, 0, 0, 255),
                                                 font_name="Aller",
                                                 )

    def on_mouse_press(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            self.network_handler.ping_robot()
        elif button == pyglet.window.mouse.RIGHT:
            self.network_handler.send_message(f"RMB:{x}|{y}")
        elif button == pyglet.window.mouse.MIDDLE:
            self.network_handler.send_message(f"MMB:{x}|{y}")

    def update_labels(self):
        for name, widget in self.vex_board.widgets.items():
            if name in self.labels:
                self.labels[name].text = f"{widget.name}: {widget.value}"
            else:
                self.labels[name] = (pyglet.text.Label(f"{widget.name}: {widget.value}",
                                                       font_size=16,
                                                       x=self.new_widget_position_x,
                                                       y=self.new_widget_position_y,
                                                       anchor_x='left',
                                                       anchor_y='top',
                                                       color=(255, 255, 255, 255),
                                                       font_name="Aller",
                                                       )
                                     )
                self.new_widget_position_y -= 30

    def draw_robot_status(self, online):
        if online:
            self.robot_status_label.text = "Online"
            self.robot_status_label.color = (0, 255, 0, 255)
            self.robot_online_image.draw()
        else:
            self.robot_status_label.text = "Offline"
            self.robot_status_label.color = (255, 0, 0, 255)
            self.robot_offline_image.draw()

    def draw_rpi_status(self, online):
        if online:
            self.rpi_status_label.text = "Online"
            self.rpi_status_label.color = (0, 255, 0, 255)
            self.rpi_online_image.draw()
        else:
            self.rpi_status_label.text = "Offline"
            self.rpi_status_label.color = (255, 0, 0, 255)
            self.rpi_offline_image.draw()

    def draw_ping_status(self, online):
        if online:
            self.ping_time_label.text = f"Ping: {round(self.network_handler.robot_ping_time())}ms"
            self.ping_time_label.color = (0, 255, 0, 255) if self.network_handler.robot_ping_time() <= 100 else (
            255, 0, 0, 255)
        else:
            self.ping_time_label.text = "Offline"
            self.ping_time_label.color = (255, 0, 0, 255)

    def draw_status(self):

        rpi_online = self.network_handler.communications_online()
        robot_online = self.network_handler.robot_is_online() and rpi_online  # Robot can't be online unless rpi is

        self.draw_ping_status(robot_online)
        self.draw_robot_status(robot_online)
        self.draw_rpi_status(rpi_online)

        self.ping_time_label.draw()
        self.robot_status_label.draw()
        self.rpi_status_label.draw()

    def on_draw(self):
        self.clear()
        pyglet.image.SolidColorImagePattern((30, 43, 54, 255)).create_image(self.width, self.height).blit(0, 0)
        self.update_labels()

        for label in self.labels.values():
            label.draw()
        self.draw_status()


class VexLogWindow(pyglet.window.Window):
    def __init__(self, width, height, network_handler: NetworkHandler):
        super().__init__(width, height, "VexLog")
        self.network_handler = network_handler
        self.text = ""
        self.log_label = pyglet.text.Label(self.text,
                                           font_size=16,
                                           anchor_x='left',
                                           anchor_y='top',
                                           color=(0, 255, 0, 255),
                                           multiline=True,
                                           width=width,
                                           font_name="Aller",
                                           )

        restart_image = pyglet.resource.image("restart-1.png")
        power_cycle_image = pyglet.resource.image("power-cycle-1.png")

        self.restart_bridge_button = PushButton(0, self.height - 64, restart_image, restart_image)
        self.restart_rpi_button = PushButton(0, self.height - 128, power_cycle_image, power_cycle_image)

        self.restart_bridge_label = pyglet.text.Label("Restart bridge",
                                                      x=64,
                                                      y=self.height,
                                                      font_size=40,
                                                      anchor_x='left',
                                                      anchor_y='top',
                                                      color=(255, 255, 255, 255),
                                                      font_name="Aller",
                                                      )

        self.restart_rpi_label = pyglet.text.Label("Restart RPI",
                                                   x=64,
                                                   y=self.height - 64,
                                                   font_size=40,
                                                   anchor_x='left',
                                                   anchor_y='top',
                                                   color=(255, 255, 255, 255),
                                                   font_name="Aller",
                                                   )

        self.push_handlers(self.restart_bridge_button)
        self.push_handlers(self.restart_rpi_button)

        self.restart_bridge_button.set_handler('on_press', self.network_handler.restart_rpi_bridge)
        self.restart_rpi_button.set_handler('on_press', self.network_handler.restart_rpi)
        # self.button.set_handler('on_release', my_on_release_handler)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.RIGHT:
            self.log(f"RMB:{x}|{y}")
        elif button == pyglet.window.mouse.MIDDLE:
            self.log(f"MMB:{x}|{y}")

    def on_draw(self):
        self.clear()
        pyglet.image.SolidColorImagePattern((30, 43, 54, 255)).create_image(self.width, self.height).blit(0, 0)
        last_20 = self.text.split("\n")[-20:]

        self.log_label = pyglet.text.Label("\n".join(last_20),
                                           x=0,
                                           y=self.height,
                                           font_size=16,
                                           anchor_x='left',
                                           anchor_y='top',
                                           color=(255, 255, 255, 255),
                                           multiline=True,
                                           width=500,
                                           font_name="Aller",
                                           )
        self.log_label.draw()
        self.restart_bridge_button._sprite.draw()
        self.restart_rpi_button._sprite.draw()
        self.restart_bridge_label.draw()
        self.restart_rpi_label.draw()

    def log(self, text, end="\n"):
        self.text += str(text) + str(end)


if __name__ == "__main__":
    network_handler = NetworkHandler(HOST, PORT)
    vex_log = VexLogWindow(500, 500, network_handler)
    network_thread = threading.Thread(target=network_handler.start_network_loop)
    ping_rpi_thread = threading.Thread(target=network_handler.ping_rpi_loop)
    ping_robot_thread = threading.Thread(target=network_handler.ping_robot_loop)

    vex_board = VexBoard()
    vex_board.add_widget("Voltage", 12)
    vex_board.add_widget("Current", 0.0)
    vex_board.add_widget("Charge", 100.0)
    vex_board.add_widget("Uptime", 0)
    vex_board.add_widget("Total Memory", 0)
    vex_board.add_widget("Free Memory", 0)
    vex_board.add_widget("Allocated Memory", 0)

    window = VexBoardWindow(500, 600, vex_board, network_handler)
    window.set_icon(icon)

    try:
        network_thread.start()
        ping_robot_thread.start()
        ping_rpi_thread.start()
        pyglet.app.run(1 / 30)
    except KeyboardInterrupt:
        pass
    print("Exiting")
    pyglet.app.exit()
    network_handler.shutdown()
