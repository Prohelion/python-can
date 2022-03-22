import uuid

# bit masks for flags bitfield
flag_mask = {
    "heartbeat":    0b10000000,
    "settings":     0b01000000,
    "rtr":          0b00000010,
    "extended_id":  0b00000001,
}

def get_client_identifier():
    return bytearray.fromhex(hex(uuid.getnode())[2:])

def get_bus_identifier(bridge_bus_number, version = 1):
    if not (0 <= bridge_bus_number <= 15):
        raise ValueError("Invalid bus number: {}, must be between 0 and 15".format(bridge_bus_number))

    if(version == 1):
        return bytearray([
                ord("T"),
                ord("r"),
                ord("i"),
                ord("t"),
                ord("i"),
                ord("u"),
                0x60 + bridge_bus_number,
        ])
    else:
        return bytearray([
                ord("T"),
                ord("r"),
                ord("i"),
                0xfd,
                0xd6,
                0x00,
                bridge_bus_number,
        ])

def get_bridge_bus_number(bus_identifier, version = 1):
    if(version == 1):
        return int(bus_identifier.hex()[-1], 16) - 0x60
    else:
        return int(bus_identifier.hex()[-1], 16)

def encode_flags(heartbeat=False, settings=False, rtr=False, extended_id=False):
    flags = 0

    if extended_id:
        flags += flag_mask['extended_id']

    if rtr:
        flags += flag_mask['rtr']

    if settings:
        flags += flag_mask['settings']

    if heartbeat:
        flags += flag_mask['heartbeat']

    return flags

def decode_flags(self, flags: int):
    return dict([(key, bool(flags & value)) for key, value in flag_mask.items()])