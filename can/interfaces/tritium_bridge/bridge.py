import socket
import struct
import select
import uuid

from can import BusABC, Message, CanError
from typing import Dict, List, Optional, Sequence, Tuple, Type, Union


class TritiumBridgeBus(BusABC):
    """
    The bridge supports bi-directional CAN-Ethernet bridging using both UDP and
    TCPprotocols.

    See TRI82.007 for interface documentation.
    """

    UDP_PACKET_STRUCTURE = ">1x7s1x7s1L1B1B8s"
    MULTICAST_PORT = 4876
    MULTICAST_IP = "239.255.60.60"


    # bit masks for flags bitfield
    flag_mask = {
        "heartbeat":    0b10000000,
        "settings":     0b01000000,
        "rtr":          0b00000010,
        "extended_id":  0b00000001,
    }

    def __init__(
        self,
        bus_number=13,
    ):
        self.BUS_NUMBER = bus_number

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
        self._socket.setblocking(False)

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
            self._flags_encode(extended_id=msg.is_extended_id, rtr=msg.is_remote_frame),
            msg.dlc,
            msg.data,
        )

        self._socket.sendto(data, (self.MULTICAST_IP, self.MULTICAST_PORT))

    def recv(self, timeout: Optional[float] = None):
        """
        Receive a message from the bridge
        """

        while (True):
            ready = select.select([self._socket], [], [], timeout)

            if ready[0]: # data ready to read
                try:
                    packet_data = self._socket.recvfrom(30, self.MULTICAST_PORT)
                except socket.error as exception:
                    raise can.CanError(f"Failed to read from IP/UDP socket: {exception}")
                
                (
                    bus_identifier,
                    client_identifier,
                    identifier,
                    flags,
                    data_length,
                    data
                ) = struct.unpack(self.UDP_PACKET_STRUCTURE, packet_data[0])

                if bus_identifier[-1] - 0x60 != self.BUS_NUMBER:
                    continue # wrong bus number

                return Message(
                    arbitration_id=identifier,
                    is_extended_id=self._flag_extended_id_set(flags),
                    dlc=data_length,
                    data=data
                )
            else:
                return None # timed out

    def shutdown(self):
        """Close all sockets and free up any resources.

        Never throws errors and only logs them.
        """
        try:
            self._socket.close()
        except OSError as exception:
            log.error("could not close IP socket: %s", exception)

    def _bus_identifier(self):
        if not (0 <= self.BUS_NUMBER <= 15):
            raise ValueError("Invalid bus number: {}, must be between 0 and 15".format(self.BUS_NUMBER))
    
        return bytearray([
                ord("T"),
                ord("r"),
                ord("i"),
                ord("t"),
                ord("i"),
                ord("u"),
                0x60 + self.BUS_NUMBER,
        ])

    def _flags_encode(
        self, heartbeat=False, settings=False, rtr=False, extended_id=False
    ):
        flags = 0

        if extended_id:
            flags += self.flag_mask['extended_id']

        if rtr:
            flags += self.flag_mask['rtr']

        if settings:
            flags += self.flag_mask['settings']

        if heartbeat:
            flags += self.flag_mask['heartbeat']

        return flags

    def _flags_decode(self, flags: int):
        decoded = {}

        for key, value in self.flag_mask.items():
            decoded[key] = bool(flags & value)
        
        return decoded
