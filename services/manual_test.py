from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient("127.0.0.1", port=502)
client.connect()
client.write_register(0, 100) # Set Battery to 100
client.write_register(1, 450) # Set Solar to 450
client.close()