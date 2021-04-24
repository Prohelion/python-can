import socket
import struct
import uuid

from can import BusABC, Message, CanError
from typing import Dict, List, Optional, Sequence, Tuple, Type, Union


class TritiumBridgeBus(BusABC):
    """
    The bridge supports bi-directional CAN-Ethernet bridging using both UDP and
    TCPprotocols.

    See TRI82.007 for interface documentation.
    """

    def __init__(
        self,
        bus_number=13,
    ):
        self.BUS_NUMBER = bus_number

        self.UDP_PACKET_STRUCTURE = ">1x7s1x7s1L1B1B8s"
        self.MULTICAST_PORT = 4876
        self.MULTICAST_IP = "239.255.60.60"

        # create socket
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except OSError as exception:
            log.error("could not open socket: %s", exception)

        # setup multicast group membership
        req = struct.pack(
            "=4sl", socket.inet_aton(self.MULTICAST_IP), socket.htonl(socket.INADDR_ANY)
        )
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._socket.bind((self.MULTICAST_IP, self.MULTICAST_PORT))

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        """
        Send a message over the bridge
        """

        # use MAC address as the unique identifier
        client_identifier = bytearray.fromhex(hex(uuid.getnode())[2:])

        # binary data structure
        data = struct.pack(
            self.UDP_PACKET_STRUCTURE,
            self._bus_identifier(),
            client_identifier,
            msg.arbitration_id,
            self._flags_byte(extended_id=msg.is_extended_id, rtr=msg.is_remote_frame),
            msg.dlc,
            msg.data,
        )

        self._socket.sendto(data, (self.MULTICAST_IP, self.MULTICAST_PORT))

    def shutdown(self):
        """Close all sockets and free up any resources.

        Never throws errors and only logs them.
        """
        try:
            self._socket.close()
        except OSError as exception:
            log.error("could not close IP socket: %s", exception)

    def _bus_identifier(self):
        return bytearray(
            [
                ord("T"),
                ord("r"),
                ord("i"),
                ord("t"),
                ord("i"),
                ord("u"),
                0x60 + self.BUS_NUMBER,
            ]
        )

    def _flags_byte(
        self, heartbeat=False, settings=False, rtr=False, extended_id=False
    ):
        flags = 0

        if extended_id:
            flags += 0x01

        if rtr:
            flags += 0x02

        if settings:
            flags += 0x40

        if heartbeat:
            flags += 0x80

        return flags
