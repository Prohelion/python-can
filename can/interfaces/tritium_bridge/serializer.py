import struct
import uuid

from can import Message

from can.interfaces.tritium_bridge.constants import TritiumConstants
from can.interfaces.tritium_bridge.utils import *

class TritiumUdpSerializer():

    def __init__(self, bridge_bus_number, version = 1):
        self._bridge_bus_number = bridge_bus_number
        self._version = version

    def serialize(self, msg: Message):

        # binary data structure
        data = struct.pack(
            TritiumConstants.UDP_DEFAULT_MESSAGE_STRUCTURE,
            get_bus_identifier(self._bridge_bus_number, self._version),
            get_client_identifier(),
            msg.arbitration_id,
            encode_flags(extended_id=msg.is_extended_id, rtr=msg.is_remote_frame),
            msg.dlc,
            msg.data,
        )

        return data

    def deserialize(self, data):
        (
            bus_identifier,
            client_identifier,
            identifier,
            flags,
            data_length,
            data
        ) = struct.unpack(TritiumConstants.UDP_DEFAULT_MESSAGE_STRUCTURE, data)


        if get_bridge_bus_number(bus_identifier, self._version) != self._bridge_bus_number:
            return None

        return Message(
            arbitration_id=identifier,
            is_extended_id=False,
            dlc=data_length,
            data=data
        )

class TritiumTcpSerializer():

    def __init__(self, bridge_bus_number):
        self._bridge_bus_number = bridge_bus_number

    def serialize(self, msg: Message):
        data = []

        return data

    def deserialize(self, data: list[str]):
        msg = Message()

        return msg
