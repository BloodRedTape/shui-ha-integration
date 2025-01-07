import asyncio
from enum import Enum
from typing import List, Callable


class GCode:
    SD_PRINT_STATUS = "M27"
    BEEP_SOUND = "M300"


class Shui3dPrinterConnectionStatus(Enum):
    Disconnected = 0
    Connected = 1


class Shui3dPrintStatus(Enum):
    Not = 0
    Busy = 1
    Printing = 2


def StdLogger(message: str):
    print(message)


class Shui3dPrinter:
    CONNECTION_TIMEOUT = 2
    READ_TIMEOUT = 4
    DELAY_AFTER_CMD_WRITE = 4

    _ip: str
    _port: int
    _reader: asyncio.StreamReader
    _writer: asyncio.StreamWriter

    _bed_temp: float = 0
    _target_bed_temp: float = 0

    _extruder_temp: float = 0
    _target_extruder_temp: float = 0

    _print_progress: float = 0
    _print_status: Shui3dPrintStatus

    _status: Shui3dPrinterConnectionStatus = Shui3dPrinterConnectionStatus.Disconnected

    _update: bool = False

    _logger: Callable[[str], None]

    def __init__(self, ip: str, port: int, logger: Callable[[str], None] = StdLogger):
        self._ip = ip
        self._port = port
        self._logger = logger

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

    async def exec(self, snippet: str) -> List[str]:
        try:
            (self._reader, self._writer) = await asyncio.wait_for(
                asyncio.open_connection(self._ip, self._port),
                Shui3dPrinter.CONNECTION_TIMEOUT,
            )
        except Exception:
            return []

        lines: List[str] = []

        try:
            lines = await asyncio.wait_for(
                self.read_lines(4), Shui3dPrinter.READ_TIMEOUT
            )
        except Exception as e:
            self.log(f"Intro read failed with {e}")
            return [type(e).__name__]

        try:
            self._writer.write((snippet + "\n\r").encode())
            await self._writer.drain()
        except Exception as e:
            self.log(f"Write failed with: {type(e).__name__}")
            return [type(e).__name__]

        await asyncio.sleep(Shui3dPrinter.DELAY_AFTER_CMD_WRITE)

        try:
            buffer = await asyncio.wait_for(self.read_all(), Shui3dPrinter.READ_TIMEOUT)

            lines = lines + buffer.split("\n")
        except asyncio.TimeoutError:
            return ["asyncio.TimeoutError"]
        except Exception as e:
            self.log(f"Read failed with: {e}")
            return [type(e).__name__]

        await self._writer.drain()
        self._writer.close()
        await self._writer.wait_closed()
        return lines

    async def beep(self):
        await self.exec(GCode.BEEP_SOUND)

    async def update(self):
        lines = await self.exec(GCode.SD_PRINT_STATUS)

        for line in lines:
            # self.log("Line: " + line)
            try:
                self.update_values_based_on(line)
            except Exception as e:
                self.log(f"Update failed with: {e}")

        try:
            self.update_print_status(lines)
        except Exception as e:
            self.log(f"Progress update failed with: {type(e).__name__}")

        self._status = (
            Shui3dPrinterConnectionStatus.Connected
            if len(lines)
            else Shui3dPrinterConnectionStatus.Disconnected
        )

    async def ensure_update(self):
        if self._update:
            return

        self._update = True

        try:
            await self.update()
        except Exception:
            pass

        self._update = False

    def update_values_based_on(self, line: str):
        parts: list[str] = line.split()

        for i in range(len(parts)):
            part: str = parts[i]
            if part.startswith("T0:"):
                self._extruder_temp = float(part.split(":")[1])
                self._target_extruder_temp = float(parts[i + 1].split("/")[-1])
            if part.startswith("B:"):
                self._bed_temp = float(part.split(":")[1])
                self._target_bed_temp = float(parts[i + 1].split("/")[-1])

    def update_print_status(self, lines: List[str]):
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
                self._print_status = Shui3dPrintStatus.Not

    def log(self, message: str):
        self._logger(message)

    def status(self):
        return str(self._status).split(".")[1]

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
