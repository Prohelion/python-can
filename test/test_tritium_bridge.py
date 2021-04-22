#!/usr/bin/env python
# coding: utf-8

import unittest
import can
import socket
import struct


class tritiumBridgeTestCase(unittest.TestCase):
    def setUp(self):
        # create instance on default bus number (13)
        self.bus = can.Bus(bustype="tritium_bridge")

        self.bus._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

    def tearDown(self):
        self.bus.shutdown()

    def test_alternate_bus_identifier(self):
        msg = can.Message(
            arbitration_id=0x100,
            is_extended_id=False,
            data=[0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF]
        )

        for n in range(0, 16):
            # create temporary bridge instance
            alternate_bus = can.Bus(n, bustype="tritium_bridge")
            # send test message
            alternate_bus.send(msg)
            # receive raw test message
            data = alternate_bus._socket.recv(30)
            data = struct.unpack(alternate_bus.UDP_PACKET_STRUCTURE, data)
            # calculate expected value
            expected_bus_identifier = bytearray(
                [
                    ord("T"),
                    ord("r"),
                    ord("i"),
                    ord("t"),
                    ord("i"),
                    ord("u"),
                    0x60 + n,
                ]
            )
            # bus identifier value is correct
            self.assertEqual(data[0], expected_bus_identifier)
            # close socket
            alternate_bus.shutdown()

    def test_send_standard(self):
        msg = can.Message(
            arbitration_id=0x400,
            is_extended_id=False,
            data=[0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF]
        )
        self.bus.send(msg)

        data = self.bus._socket.recv(30)
        data = struct.unpack(self.bus.UDP_PACKET_STRUCTURE, data)

        # ID is correct
        self.assertEqual(data[2], msg.arbitration_id)
        # extended id flag is cleared
        self.assertEqual(data[3], 0x00)
        # data length is correct
        self.assertEqual(data[4], msg.dlc)
        # data body is correct
        self.assertEqual(data[5], msg.data)
    
    def test_send_extended(self):
        msg = can.Message(
            arbitration_id=0x800,
            is_extended_id=True,
            data=[0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF],
        )
        self.bus.send(msg)

        data = self.bus._socket.recv(30)
        data = struct.unpack(self.bus.UDP_PACKET_STRUCTURE, data)

        # ID is correct
        self.assertEqual(data[2], msg.arbitration_id)
        # extended id flag is set
        self.assertEqual(data[3], 0x01)
        # data length is correct
        self.assertEqual(data[4], msg.dlc)
        # data body is correct
        self.assertEqual(data[5], msg.data)

    def test_send_rtr(self):
        msg = can.Message(
            arbitration_id=0x200,
            is_remote_frame=True,
            is_extended_id=False,
        )
        self.bus.send(msg)

        data = self.bus._socket.recv(30)
        data = struct.unpack(self.bus.UDP_PACKET_STRUCTURE, data)

        # bus identifier is correct
        self.assertEqual(data[0], b'Tritium')
        # ID is correct
        self.assertEqual(data[2], msg.arbitration_id)
        # rtr flag is set
        self.assertEqual(data[3], 0x02)
        # data length is correct
        self.assertEqual(data[4], msg.dlc)

    def test_flags(self):
        # all flags set
        self.assertEqual(self.bus._flags_byte(True, True, True, True), int('11000011', 2))
        # no flags set
        self.assertEqual(self.bus._flags_byte(False, False, False, False), int('00000000', 2))
        # default argument values result in no flags set
        self.assertEqual(self.bus._flags_byte(), int('00000000', 2))
        # extended id
        self.assertEqual(self.bus._flags_byte(extended_id = True), int('00000001', 2))



if __name__ == "__main__":
    unittest.main()
