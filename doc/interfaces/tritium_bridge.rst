Tritium CAN-Ethernet Bridge
===========================

This module implements support for the `Tritium CAN-Ethernet Bridge`_,
specifically it's custom UDP multicast protocol.

Example Default Bus Number
-------

This example sends a message using a bridge configured with the default
bus number of 13.

.. code-block:: python

        import can

        bus = can.Bus(bustype="tritium_bridge")

        message = can.Message(arbitration_id=0x123, data=[1, 2, 3])
        bus.send(message)

Example Default Bus Number
-------
        
        This example sends a message using a bridge configured with a user
        defined bus number. In this case, a bus number of 10
        
.. code-block:: python
        
        import can

        bus = can.Bus(bus_number=10, bustype="tritium_bridge")

        message = can.Message(arbitration_id=0x123, data=[1, 2, 3])
        bus.send(message)

Supported Platforms
-------------------

It should work on most Unix systems (including Linux with kernel 2.6.22+) but currently not on Windows.



