import os
import socket
import sys
import termios
import threading
import time
import traceback
from _socket import SOL_SOCKET, SO_REUSEADDR
import serial.tools.list_ports  # Library for listing available serial ports
import atexit  # Module to register cleanup functions
import sdnotify  # Library for notifying systemd about the status of this service (Linux systems only)

# Constants for VEX Brain programmer port configuration
VEX_BRAIN_PROGRAMMER_PORT_VID = 10376
VEX_BRAIN_PROGRAMMER_PORT_PID = 1281
VEX_BRAIN_PROGRAMMER_PORT_DESCRIPTION = "VEX Robotics User Port"
VEX_BRAIN_PROGRAMMER_PORT_BAUD_RATE = 9600
VEX_BRAIN_PROGRAMMER_PORT_TIMEOUT = 1
VEX_BRAIN_PROGRAMMER_PORT_RETRY_DELAY = 0.5
VEX_BRAIN_PROGRAMMER_PORT_BUFFER_SIZE = 1024

# Systemd notifier for service management
systemd_notifier = sdnotify.SystemdNotifier()


def log(message):
    """
    Logs a message and sends a notification to systemd.

    Args:
        message (str): The message to be logged and notified.
    """
    print(message)
    systemd_notifier.notify(f"STATUS={message}")


class DeviceNotFound(serial.SerialException):
    """
    Exception raised when the VEX Brain device is not found.
    """
    pass


class ConnectionSynchronizer:
    def __init__(self):
        self.serial_is_connected = True
        self.network_socket_is_connected = True
        self.rpi_restart_requested = False
        self.bridge_restart_requested = False

    def set_both_connected(self):
        self.serial_is_connected = True
        self.network_socket_is_connected = True

    def set_both_disconnected(self):
        self.serial_is_connected = False
        self.network_socket_is_connected = False

    def get_both_connected(self):
        return self.serial_is_connected and self.network_socket_is_connected

    def get_both_disconnected(self):
        return not self.serial_is_connected and not self.network_socket_is_connected

    def get_any_disconnected(self):
        return not self.get_both_connected()

    def get_any_restart_requested(self):
        return self.rpi_restart_requested or self.bridge_restart_requested


class SerialConnection:
    def __init__(self, baud_rate=115200, timeout=1):
        """
        Initializes a SerialConnection object with default or specified baud rate and timeout.

        Args:
            baud_rate (int, optional): The baud rate for serial communication. Defaults to 115200.
            timeout (int, optional): The timeout duration in seconds, defaults to 1.
        """
        self.device = None
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_connection = None

    def find_vex_brain(self):
        """
        Searches for the VEX Brain among available serial ports.

        Returns:
            bool: True if the VEX device is found, False otherwise.
        """
        for device in serial.tools.list_ports.comports():
            log(f"[SerialConnection.find_vex_brain]: Found device: {device.interface}")
            if (device.interface == VEX_BRAIN_PROGRAMMER_PORT_DESCRIPTION and
                    device.vid == VEX_BRAIN_PROGRAMMER_PORT_VID and
                    device.pid == VEX_BRAIN_PROGRAMMER_PORT_PID):
                self.device = device.device
                return True
        log("[SerialConnection.find_vex_brain]: No device found")
        return False

    def establish_connection(self):
        """
        Establishes a serial connection to the VEX Brain device.

        Raises:
            RuntimeError: If connection is attempted without initializing a device.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        if not self.device:
            raise RuntimeError(
                "Can't establish a connection without initializing a device first, please call SerialConnection.find_vex_brain first and ensure it returns True")
        try:
            self.serial_connection = serial.Serial(self.device, self.baud_rate, timeout=self.timeout)
            return True
        except serial.SerialException:
            return False

    def send_message(self, data, end="\n"):
        """
        Sends a message over the serial connection.

        Args:
            data (str): The message to be sent.
            end (str): The end to be appended to the message
        """
        self.serial_connection.write((data + end).encode())

    def get_message(self):
        """
        Receives a message from the serial connection.

        Returns:
            str: The received message.
        """
        return self.serial_connection.readline().strip().decode()

    def discard_serial_buffers(self):
        if self.serial_connection:
            try:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()
                log("[SerialConnection.discard_serial_buffers]: Discarded serial buffers")
            except termios.error:
                log("[SerialConnection.discard_serial_buffers]: termios.error while discarding serial buffers, the device may not be connected")
        else:
            log("[SerialConnection.discard_serial_buffers]: No serial connection, nothing to discard")

    def close(self):
        """
        Closes the serial connection.
        """
        if self.serial_connection:
            self.serial_connection.close()


# Class for managing network socket communication
class NetworkSocket:
    def __init__(self, host="0.0.0.0", port=10002, buffer_size=1024, timeout=1):
        """
        Initializes a NetworkSocket object with default or specified host, port, and buffer size.

        Args:
            host (str, optional): The host address to bind the socket to. Defaults to "0.0.0.0".
            port (int, optional): The port number to bind the socket to. Defaults to 10002.
            buffer_size (int, optional): The size of the receive buffer. Defaults to 1024.
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.socket = None
        self.connection = None
        self.client_address = None

    def start_listener(self):
        """
        Starts listening for incoming connections on the specified host and port.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        log(f"[NetworkSocket.start_listener] Listening for client at {self.host}:{self.port}")

    def establish_connection(self):
        """
        Accepts an incoming connection and establishes communication with the client.
        """
        log(f"[NetworkSocket.start_listener] Waiting for client to connect")
        self.connection, self.client_address = self.socket.accept()
        self.connection.settimeout(self.timeout)
        log(f"[NetworkSocket.start_listener] Connected to client at {self.client_address[0]}:{self.client_address[1]}")
        atexit.register(self.close)

    def send_message(self, message, end="\n"):
        """
        Sends a message over the network connection.

        Args:
            message (str): The message to be sent.
            end (str, optional): The end character for the message. Defaults to "\n".
        """
        self.connection.sendall((message + end).encode())

    def receive_message(self):
        """
        Receives a message from the network connection.

        Returns:
            message (str): The received message.
        """
        received = self.connection.recv(self.buffer_size).decode()
        if received == "":
            return None
        return received.strip("\n")

    def close(self):
        """
        Closes the network socket.
        """
        if self.socket:
            self.socket.close()


# Function to relay data from network socket to serial connection
def socket_to_serial(network_socket: NetworkSocket, serial_connection: SerialConnection, connection_synchronizer: ConnectionSynchronizer):
    """
    Relays data from network socket to serial connection.

    Args:
        network_socket (NetworkSocket): The network socket object.
        serial_connection (SerialConnection): The serial connection object.
        connection_synchronizer (ConnectionSynchronizer): The connection synchronizer object.

    """
    while True:
        if connection_synchronizer.get_both_connected() and not connection_synchronizer.get_any_restart_requested():
            try:
                received = network_socket.receive_message()
                if received is None:
                    log("[socket_to_serial]: Got empty packet, socket is disconnected")
                    connection_synchronizer.network_socket_is_connected = False
                    log(f"[socket_to_serial]: Informed connection_synchronizer that the network socket was disconnected")
                    break
                elif received == "RPI:RESTART_BRIDGE":
                    log("[socket_to_serial]: Got RPI:RESTART_BRIDGE")
                    connection_synchronizer.bridge_restart_requested = True
                elif received == "RPI:RESTART":
                    log("[socket_to_serial]: Got RPI:RESTART")
                    connection_synchronizer.rpi_restart_requested = True
            except (TimeoutError, socket.timeout):
                log("[socket_to_serial]: timeout while getting data from network socket")
                continue
            except ConnectionResetError:
                log(f"[socket_to_serial]: Connection reset in network_socket.receive_message: {traceback.format_exc()}")
                connection_synchronizer.network_socket_is_connected = False
                log(f"[socket_to_serial]: Informed connection_synchronizer that the network socket was disconnected")
                break
            except Exception:
                log(f"[socket_to_serial]: Critical error in network_socket.receive_message: {traceback.format_exc()}")
                connection_synchronizer.network_socket_is_connected = False
                log(f"[socket_to_serial]: Informed connection_synchronizer that the network socket was disconnected")
                break
            try:
                serial_connection.send_message(received)
            except Exception:
                log(f"[socket_to_serial]: Critical error in serial_connection.send_message: {traceback.format_exc()}")
                connection_synchronizer.serial_is_connected = False
                log(f"[socket_to_serial]: Informed connection_synchronizer that the serial connection was disconnected")
                break
        else:
            log("[socket_to_serial]: connection_synchronizer says to terminate")
            break
    log("[socket_to_serial]: Terminating")


# Function to relay data from serial connection to network socket
def serial_to_socket(network_socket: NetworkSocket, serial_connection: SerialConnection, connection_synchronizer: ConnectionSynchronizer):
    """
    Relays data from serial connection to network socket.

    Args:
        network_socket (NetworkSocket): The network socket object.
        serial_connection (SerialConnection): The serial connection object.
        connection_synchronizer (ConnectionSynchronizer): The connection synchronizer object.
    """
    while True:
        if connection_synchronizer.get_both_connected() and not connection_synchronizer.get_any_restart_requested():
            try:
                received = serial_connection.get_message()
                if not received:
                    log("[serial_to_socket]: timeout while getting data from serial connection")
                    continue
            except Exception:
                log(f"[serial_to_socket]: Critical error in serial_connection.get_message: {traceback.format_exc()}")
                connection_synchronizer.serial_is_connected = False
                log(f"[serial_to_socket]: Informed connection_synchronizer that the serial connection was disconnected")
                break
            try:
                network_socket.send_message(received)
            except BrokenPipeError:
                log(f"[serial_to_socket]: Broken pipe in network_socket.send_message")
                connection_synchronizer.network_socket_is_connected = False
                log(f"[serial_to_socket]: Informed connection_synchronizer that the network socket was disconnected")
                break
            except Exception:
                log(f"[serial_to_socket]: Critical error in network_socket.send_message: {traceback.format_exc()}")
                connection_synchronizer.network_socket_is_connected = False
                log(f"[serial_to_socket]: Informed connection_synchronizer that the network socket was disconnected")
                break
        else:
            log("[serial_to_socket]: connection_synchronizer says to terminate")
            break
    log("[serial_to_socket]: Terminating")


# Main function
def main():
    # Initialize network socket and start listening for clients
    communications_socket = NetworkSocket()
    communications_socket.start_listener()
    serial_connection = SerialConnection()
    connection_synchronizer = ConnectionSynchronizer()

    # Start under the assumption that we have no connections
    connection_synchronizer.set_both_disconnected()

    systemd_notifier.notify("READY=1")

    while True:
        if not connection_synchronizer.network_socket_is_connected:
            log("[main]: connection_synchronizer says we lost connection to the socket, attempting to reconnect")
            # Establish connection with a client
            communications_socket.establish_connection()
        else:
            log("[main]: connection_synchronizer says we did not lose connection to the socket, skipping reconnect")

        if not connection_synchronizer.serial_is_connected:
            log("[main]: connection_synchronizer says we lost connection to the robot, attempting to reconnect")
            # Initialize serial connection and attempt to connect to VEX Brain
            serial_connection = SerialConnection()
            log("[main]: Looking for vex brain...")
            while not serial_connection.find_vex_brain():
                log(f"[main]: Unable to find vex brain, rescanning in {VEX_BRAIN_PROGRAMMER_PORT_RETRY_DELAY} seconds")
                time.sleep(VEX_BRAIN_PROGRAMMER_PORT_RETRY_DELAY)
            log("[main]: Found vex brain")
            log("[main]: Establishing connection to vex brain...")
            while not serial_connection.establish_connection():
                log(f"[main]: Unable to connect to vex brain, retrying in {VEX_BRAIN_PROGRAMMER_PORT_RETRY_DELAY} seconds")
                time.sleep(VEX_BRAIN_PROGRAMMER_PORT_RETRY_DELAY)
            log("[main]: Established connection to vex brain")
        else:
            log("[main]: connection_synchronizer says we did not lose connection to the robot, skipping reconnect")

        connection_synchronizer.set_both_connected()

        # Create and start threads for bidirectional communication
        socket_to_serial_thread = threading.Thread(target=socket_to_serial,
                                                   args=(communications_socket, serial_connection, connection_synchronizer))
        serial_to_socket_thread = threading.Thread(target=serial_to_socket,
                                                   args=(communications_socket, serial_connection, connection_synchronizer))

        communications_socket.connection.setblocking(False)
        communications_socket.connection.settimeout(0)

        try:
            log("[main]: Discarding incoming socket data before initializing connection")
            while communications_socket.receive_message():
                pass
        except (socket.timeout, BlockingIOError):
            log("[main]: Got timeout from socket, done discarding data")
            pass

        communications_socket.connection.setblocking(True)

        log("[main]: Discarding serial buffers to prevent packet flooding")
        serial_connection.discard_serial_buffers()

        log("[main]: Starting bidirectional communication")
        socket_to_serial_thread.start()
        serial_to_socket_thread.start()

        # Wait for threads to finish
        while connection_synchronizer.get_both_connected() and not connection_synchronizer.get_any_restart_requested():
            log("[main]: Both threads alive")
            time.sleep(3)

        if connection_synchronizer.get_any_restart_requested():
            if connection_synchronizer.rpi_restart_requested:
                log("[main]: RPI restart requested")
                os.system("sudo reboot")
            elif connection_synchronizer.bridge_restart_requested:
                log("[main]: Bridge restart requested")
                sys.exit(0)

        if not connection_synchronizer.network_socket_is_connected and not connection_synchronizer.serial_is_connected:
            log("[main]: Socket and serial disconnected, reconnecting socket")
        elif not connection_synchronizer.serial_is_connected:
            log("[main]: Serial disconnected but socket connected, keeping socket connection and reconnecting to serial")
        elif not connection_synchronizer.network_socket_is_connected:
            log("[main]: Socket disconnected, reconnecting socket")

        log("[main]: Waiting for all threads to terminate...")
        socket_to_serial_thread.join()
        serial_to_socket_thread.join()
        log("[main]: All threads terminated")


# Entry point of the script
if __name__ == "__main__":
    main()
