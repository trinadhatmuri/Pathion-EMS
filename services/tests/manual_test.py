from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient("127.0.0.1", port=502)
client.connect()
# Write 100% to both index 0 and 1 to be safe
client.write_registers(0, [100, 100]) 
# Write 20kW to Solar (Index 2)
client.write_register(2, 20)
client.close()
print("Injection Successful: Battery 100%, Solar 20kW")