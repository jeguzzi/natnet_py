import struct
import numpy as np
import numpy.typing as npt
from typing import Any, cast

Vector3S = struct.Struct('<fff')
QuaternionS = struct.Struct('<ffff')
FloatValue = struct.Struct('<f')
DoubleValue = struct.Struct('<d')
MatrixS = struct.Struct('<ffffffffffff')

Vector3 = npt.NDArray[np.float64]
Quaternion = npt.NDArray[np.float64]


class Buffer:
    data: bytes = b''
    index: int = 0

    def __init__(self, data: bytes):
        self.data = data
        self.index = 0

    def __repr__(self) -> str:
        return f"<Buffer {self.index} | {len(self.data)}: {self.data[self.index:self.index+8]!r}>"

    @property
    def remaining(self) -> int:
        return len(self.data) - self.index

    def read_string(self, size: int = 0) -> str:
        if size > 0:
            end = self.index + size
        else:
            end = -1
        index = self.data.find(b'\0', self.index, end)
        value = self.data[self.index:index].decode("utf-8")
        if size:
            self.index = end
        else:
            self.index = index + 1
        return value

    def read_int(self) -> int:
        value = int.from_bytes(self.data[self.index:self.index + 4],
                               byteorder='little')
        self.index += 4
        return value

    def read_bool(self) -> bool:
        value = self.data[self.index] != 0
        self.index += 1
        return value

    def read_bytes(self, size: int) -> bytes:
        value = self.data[self.index: self.index + size]
        self.index += size
        return value

    def read_long(self) -> int:
        value = int.from_bytes(self.data[self.index:self.index + 8],
                               byteorder='little')
        self.index += 8
        return value

    def read_ulong(self) -> int:
        value, = struct.unpack('<Q', self.data[self.index:self.index + 8])
        self.index += 8
        return cast(int, value)

    def read_short(self) -> int:
        value, = struct.unpack('<h', self.data[self.index:self.index + 2])
        self.index += 2
        return cast(int, value)

    def read_vector(self) -> Vector3:
        value = np.asarray(
            Vector3S.unpack(self.data[self.index:self.index + 12]))
        self.index += 12
        return value

    def read_quaternion(self) -> Quaternion:
        value = np.asarray(
            QuaternionS.unpack(self.data[self.index:self.index + 16]))
        self.index += 16
        return value

    def read_float(self) -> float:
        value = FloatValue.unpack(self.data[self.index:self.index + 4])
        self.index += 4
        return cast(float, value[0])

    def read_double(self) -> float:
        value = DoubleValue.unpack(self.data[self.index:self.index + 8])
        self.index += 8
        return cast(float, value[0])

    def read_matrix(self) -> npt.NDArray[np.float64]:
        value = MatrixS.unpack(self.data[self.index:self.index + 4 * 12])
        self.index += 4 * 12
        return np.asarray(value)

    def read(self, fmt: str, size: int) -> Any:
        value = struct.unpack(fmt, self.data[self.index:self.index + size])
        self.index += size
        return value
