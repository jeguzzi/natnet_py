import struct
from typing import Any

from .buffer import (DoubleValue, FloatValue, MatrixRow, MatrixS, Quaternion,
                     QuaternionS, Vector3, Vector3S)


class WriteBuffer:

    def __init__(self):
        self.data = bytearray()

    def __repr__(self) -> str:
        return f"<WriteBuffer: {len(self.data)} bytes>"

    def write_bool(self, value: bool) -> None:
        self.data.append(1 if value else 0)

    def set_short(self, index: int, value: int) -> None:
        self.set(index, '<h', value)

    def write_short(self, value: int) -> None:
        self.write('<h', value)

    def write_int(self, value: int) -> None:
        self.write("<i", value)

    def write_long(self, value: int) -> None:
        self.write("<q", value)

    def write_ulong(self, value: int) -> None:
        self.write("<Q", value)

    def write_bytes(self, value: bytes, size: int = 0) -> None:
        self.data.extend(value)
        if len(value) < size:
            self.data.extend(b"\0" * (size - len(value)))

    def write_string(self, value: str, size: int = 0) -> None:
        self.data.extend(value.encode("utf-8"))
        self.data.append(0)
        if len(value) + 1 < size:
            self.data.extend(b"\0" * (size - len(value) - 1))

    def write_vector(self, value: Vector3) -> None:
        self.data.extend(Vector3S.pack(*value))

    def write_quaternion(self, value: Quaternion) -> None:
        self.data.extend(QuaternionS.pack(*value))

    def write_float(self, value: float) -> None:
        self.data.extend(FloatValue.pack(value))

    def write_double(self, value: float) -> None:
        self.data.extend(DoubleValue.pack(value))

    def write_matrix_row(self, value: MatrixRow) -> None:
        self.data.extend(MatrixS.pack(*value))

    def write(self, fmt: str, *value: Any) -> None:
        self.data.extend(struct.pack(fmt, *value))

    def set(self, index: int, fmt: str, *value: Any) -> None:
        vs = struct.pack(fmt, *value)
        self.data[index:index + len(vs)] = vs
