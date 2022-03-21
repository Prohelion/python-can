import logging
import select
import socket
import struct
from typing import Optional

from can import BusABC, CanError, Message

from can.interfaces.tritium_bridge.constants import TritiumConstants
from can.interfaces.tritium_bridge.serializer import TritiumUdpSerializer
from can.interfaces.tritium_bridge.enums import TritiumBridgeConnectionType

log = logging.getLogger(__name__)

class TritiumBridgeBus(BusABC):
    """
    The bridge supports bi-directional CAN-Ethernet bridging using both UDP and
    TCP protocols.

    See TRI82.007 for interface documentation.
    """

    def __init__(
        self,
        interface_ip = None,
        bridge_ip = TritiumConstants.UDP_DEFAULT_MULTICAST_IP,
        bridge_port = TritiumConstants.UDP_DEFAULT_MULTICAST_PORT,
        bridge_connection_type = TritiumBridgeConnectionType.UDP,
        bridge_bus_number = 13,
        bridge_version = 2
    ):
        self.interface_ip = interface_ip
        self.bridge_ip = bridge_ip
        self.bridge_port = bridge_port
        self.bridge_bus_number = bridge_bus_number
        self.bridge_connection_type = bridge_connection_type
        self._bridge_version = bridge_version

        self._udp_socket = None
        self._udp_is_connected = False
        self._udp_serializer = TritiumUdpSerializer(self.bridge_bus_number, self._bridge_version)

        self._tcp_socket = None
        self._tcp_is_connected = False

        # Parent-class info
        self.channel = self.bridge_bus_number
        self.channel_info = f"Tritium CAN via {self.bridge_connection_type}: {self.interface_ip}->{self.bridge_ip}"

        if(self.bridge_connection_type == TritiumBridgeConnectionType.UDP):
            self._connect_via_udp()
        elif(self.bridge_connection_type == TritiumBridgeConnectionType.TCP):
            raise CanError("TCP Bridge Connection Type is not yet supported")
        else:
            raise CanError("Bridge Connection Type is invalid")

    def _connect_via_udp(self):
        if(self._udp_is_connected == True):
            log.warn("Already connected via UDP")
            return

        try:
            # TODO: Automatically find all network interfaces that support multicast
            self._udp_socket = self._create_udp_socket(
                self.interface_ip,
                TritiumConstants.UDP_DEFAULT_MULTICAST_IP,
                TritiumConstants.UDP_DEFAULT_MULTICAST_PORT)
            self._udp_is_connected = True
            log.info("Successfully connected via UDP")
        except OSError as exception:
            self._udp_socket = None
            self._udp_is_connected = False
            raise CanError("Failed to connect via UDP: %s", exception)

    def _create_udp_socket(self, interface_ip, multicast_ip, multicast_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow the reuse of this ip/port by other programs
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 128)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(interface_ip))

        # Add a membership for each network interface
        mreq = struct.pack("4s4s", socket.inet_aton(multicast_ip), socket.inet_aton(interface_ip))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        sock.bind((interface_ip, multicast_port))
        return sock
        
    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        """
        Send a message to the Tritium CAN Bridge
        """
        if(self.bridge_connection_type == TritiumBridgeConnectionType.UDP):
            self._send_via_udp(msg, timeout)
        elif(self.bridge_connection_type == TritiumBridgeConnectionType.TCP):
            raise CanError("TCP Bridge Connection Type is not yet supported")
        else:
            raise CanError("Bridge Connection Type is invalid")

    def _send_via_udp(self, msg: Message, timeout: Optional[float] = None) -> None:
        """
        Send a message to the Tritium CAN Bridge using UDP
        """
        data = self._udp_serializer.serialize(msg)
        self._udp_socket.sendto(data, (TritiumConstants.UDP_DEFAULT_MULTICAST_IP, TritiumConstants.UDP_DEFAULT_MULTICAST_PORT))

    def recv(self, timeout: Optional[float] = None):
        """
        Receive a message from the Tritium CAN Bridge
        """
        if(self.bridge_connection_type == TritiumBridgeConnectionType.UDP):
            return self._recv_via_udp(timeout)
        elif(self.bridge_connection_type == TritiumBridgeConnectionType.TCP):
            raise CanError("TCP Bridge Connection Type is not yet supported")
        else:
            raise CanError("Bridge Connection Type is invalid")

    def _recv_via_udp(self, timeout: Optional[float] = None):
        """
        Receive a message from the Tritium CAN Bridge via UDP
        """

        socket_list = [ self._udp_socket ]
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [], timeout)

        for sock in read_sockets:
            sock.settimeout(timeout)
            try:
                data = sock.recv(30)
                if data is not None:
                    msg = self._udp_serializer.deserialize(data)
                    return msg
            except socket.timeout as e:
                continue
            except Exception:
                log.error(f"Failed to read UDP socket")

        return None

        timer = 0
        while (True):
            try:
                packet_data = self._udp_socket.recv(1500)
                msg = self._udp_serializer.deserialize(packet_data)
                return msg
            except socket.error as exception:
                timer += 0.1
                if timer >= timeout:
                    return None
                else:
                    continue
            except Exception as e:
                raise CanError("Failed to read from socket via UDP: %s", exception)
                

    def shutdown(self):
        """
        Close all sockets and free up any resources.

        Never throws errors and only logs them.
        """

        if(self._udp_is_connected):
            try:
                self._udp_socket.close()
            except OSError as exception:
                log.error("Failed to close UDP socket: %s", exception)

        if(self._tcp_is_connected):
            try:
                self._udp_socket.close()
            except OSError as exception:
                log.error("Failed to close TCP socket: %s", exception)


    
