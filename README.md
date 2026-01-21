# Pathion-EMS (Energy Management System)

A robust, multi-process industrial control system prototype designed for high-availability energy monitoring and safety actuation.

## 🏗️ Architecture Overview

This project uses a **Decoupled Service Architecture** to ensure fault tolerance and high performance. Instead of a single monolithic script, the system is split into three distinct layers:

1.  **Hardware Emulation:** Simulates a solar inverter and battery storage using the Modbus TCP protocol.
2.  **Data Producer:** Acts as the "Sense" layer. It polls the hardware and writes data into high-speed **POSIX Shared Memory** using a binary ring-buffer pattern.
3.  **Logic Agent:** Acts as the "Think/Act" layer. It reads from Shared Memory (Read-Only), validates data health via sliding-window quality scoring, and executes safety commands.



---

## 🚀 Key Features

* **High-Speed IPC:** Utilizes `mmap` and `posix_ipc` for near-zero latency communication between services.
* **Watchdog Heartbeat:** The Producer generates a 1Hz pulse, allowing the Agent to detect service failures or "stale" data.
* **Quality Scoring:** Implements a sliding window algorithm to monitor the reliability of the data stream.
* **Closed-Loop Control:** Automatically throttles solar production via Modbus Write commands when the battery reaches 100% capacity.
* **Hardware Agnostic:** Uses industrial standard Modbus TCP, making it compatible with real-world inverters (Tesla, SMA, etc.) with minimal config changes.

---

## 🛠️ Tech Stack

* **Language:** Python 3.10.12
* **Protocol:** Modbus TCP (`pymodbus`)
* **Memory Management:** POSIX Shared Memory, `struct` (Binary Packing)
* **DevOps:** Modular Python structure, Virtual Environments

---

## 🚦 Getting Started

1. **Clone the repo:**
   ```bash
   git clone [https://github.com/trinadhatmuri/Pathion-EMS.git](https://github.com/trinadhatmuri/Pathion-EMS.git)
   cd Pathion-EMS/services