import asyncio
from enum import Enum
from typing import List, Callable


class GCode:
    SD_PRINT_STATUS = "M27"
    BEEP_SOUND = "M300"


class Shui3dPrinterConnection:
    CONNECTION_TIMEOUT = 2
    READ_TIMEOUT = 4
    DELAY_AFTER_CMD_WRITE = 4

    _ip: str
    _port: int
    _reader: asyncio.StreamReader
    _writer: asyncio.StreamWriter

    class CanNotConnect:
        pass

    def __init__(self, ip: str, port: int):
        self._ip = ip
        self._port = port

    async def read_all(self, chunk_size: int = 10000):
        data = await self._reader.read(chunk_size)

        return data.decode()

    async def read_lines(self, count: int):
        lines: List[str] = []

        for _ in range(count):
            line: str = (await self._reader.readline()).decode()
            sublines = line.split("\n")

            for subline in sublines:
                if len(subline):
                    lines.append(subline)

        return lines

    async def exec(self, snippet: str) -> List[str] | CanNotConnect:
        try:
            (self._reader, self._writer) = await asyncio.wait_for(
                asyncio.open_connection(self._ip, self._port),
                Shui3dPrinterConnection.CONNECTION_TIMEOUT,
            )
        except Exception:
            return Shui3dPrinterConnection.CanNotConnect()

        lines: List[str] = []

        try:
            lines = await asyncio.wait_for(
                self.read_lines(4), Shui3dPrinterConnection.READ_TIMEOUT
            )
        except Exception as e:
            return lines + [type(e).__name__]

        try:
            self._writer.write((snippet + "\n\r").encode())
            await self._writer.drain()
        except Exception as e:
            return lines + [type(e).__name__]

        await asyncio.sleep(Shui3dPrinterConnection.DELAY_AFTER_CMD_WRITE)

        try:
            buffer = await asyncio.wait_for(
                self.read_all(), Shui3dPrinterConnection.READ_TIMEOUT
            )

            lines = lines + buffer.split("\n")
        except Exception as e:
            return lines + [type(e).__name__]

        await self._writer.drain()
        self._writer.close()
        await self._writer.wait_closed()
        return lines


class Shui3dPrinterConnectionStatus(Enum):
    Disconnected = 0
    Connected = 1


class Shui3dPrintStatus(Enum):
    Idle = 0
    Busy = 1
    Printing = 2


def StdLogger(message: str):
    print(message)


class Shui3dPrinter:
    FAILS_TO_DISCONNECT = 3

    _bed_temp: float = 0
    _target_bed_temp: float = 0

    _extruder_temp: float = 0
    _target_extruder_temp: float = 0

    _print_progress: float = 0
    _print_status: Shui3dPrintStatus = Shui3dPrintStatus.Idle

    _status: Shui3dPrinterConnectionStatus = Shui3dPrinterConnectionStatus.Disconnected

    _update: bool = False
    _update_connection: Shui3dPrinterConnection

    _logger: Callable[[str], None]

    _disconnected: int = 0

    def __init__(self, ip: str, port: int, logger: Callable[[str], None] = StdLogger):
        self._ip = ip
        self._port = port
        self._logger = logger
        self._update_connection = Shui3dPrinterConnection(ip, port)

    def log(self, message: str):
        self._logger(message)

    async def beep(self):
        await self.exec_with_state_update(GCode.BEEP_SOUND)

    async def update(self):
        success = await self._exec_with_state_update(GCode.SD_PRINT_STATUS)

        if not success:
            self._disconnected += 1
        else:
            self._disconnected = 0
            self._status = Shui3dPrinterConnectionStatus.Connected

        if self._disconnected >= Shui3dPrinter.FAILS_TO_DISCONNECT:
            self._status = Shui3dPrinterConnectionStatus.Disconnected

    async def ensure_update(self):
        if self._update:
            return await self.wait_for_update()

        self._update = True

        try:
            await self.update()
        except Exception:
            pass

        self._update = False

    async def wait_for_update(self):
        while self._update:
            await asyncio.sleep(0.016)

    async def _exec_with_state_update(self, gcode: str) -> bool:
        lines = await Shui3dPrinterConnection(self._ip, self._port).exec(gcode)

        if isinstance(lines, Shui3dPrinterConnection.CanNotConnect):
            return False

        self.update_values_from(lines)

        return True

    async def exec_with_state_update(self, gcode: str) -> bool:
        return await self._exec_with_state_update(gcode)

    def update_from(self, lines: List[str]):
        self.update_values_from(lines)

        try:
            self.update_statues_from(lines)
        except Exception as e:
            self.log(f"Progress update failed with: {type(e).__name__}")

    def update_values_from(self, lines: List[str]):
        for line in lines:
            # self.log("Line: " + line)
            try:
                self.parse_and_update_values(line)
            except Exception as e:
                self.log(f"Update failed with: {e}")

    def parse_and_update_values(self, line: str):
        parts: list[str] = line.split()

        for i in range(len(parts)):
            part: str = parts[i]
            if part.startswith("T0:"):
                self._extruder_temp = float(part.split(":")[1])
                self._target_extruder_temp = float(parts[i + 1].split("/")[-1])
            if part.startswith("B:"):
                self._bed_temp = float(part.split(":")[1])
                self._target_bed_temp = float(parts[i + 1].split("/")[-1])

    def update_statues_from(self, lines: List[str]):
        for line in lines:
            if "SD printing byte" in line:
                nm = line.split()[-1].split("/")
                self._print_progress = float(nm[0]) / float(nm[1]) * 100
                self._print_status = Shui3dPrintStatus.Printing
                break
            elif "busy" in line:
                self._print_status = Shui3dPrintStatus.Busy
                break
            else:
                self._print_status = Shui3dPrintStatus.Idle

    def status(self):
        return str(self._status).split(".")[1]

    def is_connected(self) -> bool:
        return self._status == Shui3dPrinterConnectionStatus.Connected

    def bed_temp(self):
        return (
            self._bed_temp
            if self._status == Shui3dPrinterConnectionStatus.Connected
            else None
        )

    def target_bed_temp(self):
        return (
            self._target_bed_temp
            if self._status == Shui3dPrinterConnectionStatus.Connected
            else None
        )

    async def set_target_bed_temp(self, temp: float):
        await self.exec_with_state_update(f"M140 S{temp}")

    async def set_target_extruder_temp(self, temp: float):
        await self.exec_with_state_update(f"M104 T0 S{temp}")

    def extruder_temp(self):
        return (
            self._extruder_temp
            if self._status == Shui3dPrinterConnectionStatus.Connected
            else None
        )

    def target_extruder_temp(self):
        return (
            self._target_extruder_temp
            if self._status == Shui3dPrinterConnectionStatus.Connected
            else None
        )

    def print_progress(self):
        if self._status != Shui3dPrinterConnectionStatus.Connected:
            return None

        if self._print_status != Shui3dPrintStatus.Printing:
            return None

        return self._print_progress

    def print_status(self):
        return (
            str(self._print_status).split(".")[1]
            if self._status == Shui3dPrinterConnectionStatus.Connected
            else None
        )
