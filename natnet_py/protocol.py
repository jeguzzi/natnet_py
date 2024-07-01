import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple
import socket

import numpy as np
import numpy.typing as npt
import struct

from .buffer import Buffer as Buffer
from .buffer import Quaternion as Quaternion
from .buffer import Vector3 as Vector3


Version = Tuple[int, int, int, int]


@dataclass
class FramePrefixData:
    frame_number: int

    @classmethod
    def unpack(cls, data: Buffer) -> 'FramePrefixData':
        frame_number = data.read_int()
        return cls(frame_number)


@dataclass
class MarkerSet:
    model_name: str = ""
    marker_positions: List[Vector3] = field(default_factory=list)


@dataclass
class MarkerSetData:
    marker_sets: List[MarkerSet] = field(default_factory=list)
    unlabeled_markers: MarkerSet = field(default_factory=MarkerSet)

    @classmethod
    def unpack(cls, data: Buffer) -> 'MarkerSetData':
        marker_set_data = cls()
        marker_set_count = data.read_int()
        for i in range(marker_set_count):
            marker_data = MarkerSet()
            marker_data.model_name = data.read_string()
            marker_count = data.read_int()
            for j in range(marker_count):
                marker_data.marker_positions.append(data.read_vector())
            marker_set_data.marker_sets.append(marker_data)

        unlabeled_markers_count = data.read_int()
        ps = marker_set_data.unlabeled_markers.marker_positions
        for i in range(unlabeled_markers_count):
            ps.append(data.read_vector())
        return marker_set_data


@dataclass
class RigidBodyMarker:
    position: Vector3 = field(default_factory=lambda: np.zeros(3))
    id_num: int = 0
    size: float = 0.0
    error: float = 0.0


@dataclass
class RigidBody:
    id_num: int
    position: Vector3
    orientation: Quaternion
    rb_marker_list: List[RigidBodyMarker] = field(default_factory=list)
    tracking_valid: bool = False
    error: float = 0.0

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> 'RigidBody':
        new_id = data.read_int()
        pos = data.read_vector()
        rot = data.read_quaternion()
        rigid_body = cls(new_id, pos, rot)
        # RB Marker Data ( Before version 3.0.
        # After Version 3.0 Marker data is in description )
        if major < 3 and major != 0:
            marker_count = data.read_int()
            rb_marker_list = rigid_body.rb_marker_list
            for i in range(marker_count):
                rb_marker_list.append(
                    RigidBodyMarker(position=data.read_vector()))
            if major >= 2:
                for i in range(marker_count):
                    rb_marker_list[i].id_num = data.read_int()
                for i in range(marker_count):
                    rb_marker_list[i].size = data.read_float()
        if major >= 2:
            rigid_body.error = data.read_float()
        # Version 2.6 and later
        if (major == 2 and minor >= 6) or major > 2:
            param = data.read_short()
            rigid_body.tracking_valid = (param & 0x01) != 0
        return rigid_body


def unpack_rigid_bodies(data: Buffer, major: int, minor: int) -> List[RigidBody]:
    rigid_bodies: List[RigidBody] = []
    rigid_body_count = data.read_int()
    for i in range(rigid_body_count):
        rigid_body = RigidBody.unpack(data, major, minor)
        rigid_bodies.append(rigid_body)
    return rigid_bodies


@dataclass
class Skeleton:
    id_num: int = 0
    rigid_bodies: List[RigidBody] = field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> 'Skeleton':
        skeleton = Skeleton(data.read_int())
        rigid_body_count = data.read_int()
        for rb_num in range(rigid_body_count):
            rigid_body = RigidBody.unpack(data, major, minor)
            skeleton.rigid_bodies.append(rigid_body)
        return skeleton


def unpack_skeletons(data: Buffer, major: int, minor: int) -> List[Skeleton]:
    skeletons: List[Skeleton] = []
    if (major == 2 and minor > 0) or major > 2:
        skeleton_count = data.read_int()
        for _ in range(skeleton_count):
            skeleton = Skeleton.unpack(data, major, minor)
            skeletons.append(skeleton)
    return skeletons


@dataclass
class LabeledMarker:
    id_num: int
    position: Vector3
    size: float = 0.0
    param: int = 0
    residual: float = 0.0

    @property
    def decoded_marker_id(self) -> Tuple[int, int]:
        model_id = self.id_num >> 16
        marker_id = self.id_num & 0x0000ffff
        return model_id, marker_id

    @property
    def decoded_param(self) -> Tuple[bool, bool, bool]:
        occluded = (self.param & 0x01) != 0
        point_cloud_solved = (self.param & 0x02) != 0
        model_solved = (self.param & 0x04) != 0
        return occluded, point_cloud_solved, model_solved


def unpack_labeled_markers(data: Buffer, major: int, minor: int) -> List[LabeledMarker]:
    labeled_markers: List[LabeledMarker] = []
    # Labeled markers (Version 2.3 and later)
    labeled_marker_count = 0
    if (major == 2 and minor > 3) or major > 2:
        labeled_marker_count = data.read_int()
        for _ in range(labeled_marker_count):
            tmp_id = data.read_int()
            pos = data.read_vector()
            size = data.read_float()
            # Version 2.6 and later
            param = 0
            if (major == 2 and minor >= 6) or major > 2:
                param = data.read_short()
            # Version 3.0 and later
            residual = 0.0
            if major >= 3:
                residual = data.read_float()
            labeled_marker = LabeledMarker(tmp_id, pos, size, param,
                                           residual)
            labeled_markers.append(labeled_marker)
    return labeled_markers


@dataclass
class ForcePlateChannelData:
    frame_list: List[float] = field(default_factory=list)


@dataclass
class ForcePlate:
    id_num: int = 0
    channel_data: List[ForcePlateChannelData] = field(default_factory=list)


def unpack_force_plates(data: Buffer, major: int, minor: int) -> List[ForcePlate]:
    force_plates: List[ForcePlate] = []
    # Force Plate data (version 2.9 and later)
    force_plate_count = 0
    if (major == 2 and minor >= 9) or major > 2:
        force_plate_count = data.read_int()
        for i in range(force_plate_count):
            force_plate_id = data.read_int()
            force_plate = ForcePlate(force_plate_id)
            force_plate_channel_count = data.read_int()
            for j in range(force_plate_channel_count):
                fp_channel_data = ForcePlateChannelData()
                force_plate_channel_frame_count = data.read_int()
                for k in range(force_plate_channel_frame_count):
                    fp_channel_data.frame_list.append(data.read_float())
                force_plate.channel_data.append(fp_channel_data)
            force_plates.append(force_plate)
    return force_plates


@dataclass
class DeviceChannelData:
    frame_list: List[float] = field(default_factory=list)


@dataclass
class Device:
    id_num: int = 0
    channel_data: List[DeviceChannelData] = field(default_factory=list)


def unpack_devices(data: Buffer, major: int, minor: int) -> List[Device]:
    devices: List[Device] = []
    # Device data (version 2.11 and later)
    device_count = 0
    if (major == 2 and minor >= 11) or major > 2:
        device_count = data.read_int()
        for i in range(device_count):
            device = Device(data.read_int())
            device_channel_count = data.read_int()
            for j in range(device_channel_count):
                device_channel_data = DeviceChannelData()
                device_channel_frame_count = data.read_int()
                for k in range(device_channel_frame_count):
                    device_channel_val = data.read_float()
                    device_channel_data.frame_list.append(
                        device_channel_val)
                device.channel_data.append(device_channel_data)
            devices.append(device)
    return devices


@dataclass
class FrameSuffixData:
    timecode: int = -1
    timecode_sub: int = -1
    timestamp: float = -1
    stamp_camera_mid_exposure: int = -1
    stamp_data_received: int = -1
    stamp_transmit: int = -1
    param: int = 0
    is_recording: bool = False
    tracked_models_changed: bool = True

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> 'FrameSuffixData':
        frame_suffix_data = cls()
        frame_suffix_data.timecode = data.read_int()
        frame_suffix_data.timecode_sub = data.read_int()
        # Timestamp (increased to double precision in 2.7 and later)
        if (major == 2 and minor >= 7) or major > 2:
            frame_suffix_data.timestamp = data.read_double()
        else:
            frame_suffix_data.timestamp = data.read_float()
        if major >= 3:
            frame_suffix_data.stamp_camera_mid_exposure = data.read_long()
            frame_suffix_data.stamp_data_received = data.read_long()
            frame_suffix_data.stamp_transmit = data.read_long()
        # Frame parameters
        param = data.read_short()
        is_recording = (param & 0x01) != 0
        tracked_models_changed = (param & 0x02) != 0
        frame_suffix_data.param = param
        frame_suffix_data.is_recording = is_recording
        frame_suffix_data.tracked_models_changed = tracked_models_changed
        return frame_suffix_data


@dataclass
class MoCapData:
    frame_number: int = -1
    marker_sets: List[MarkerSet] = field(default_factory=list)
    unlabeled_markers: MarkerSet = field(default_factory=MarkerSet)
    rigid_bodies: List[RigidBody] = field(default_factory=list)
    skeletons: List[Skeleton] = field(default_factory=list)
    labeled_markers: List[LabeledMarker] = field(default_factory=list)
    force_plates: List[ForcePlate] = field(default_factory=list)
    devices: List[Device] = field(default_factory=list)
    suffix_data: Optional[FrameSuffixData] = None

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> 'MoCapData':
        mocap_data = cls()
        mocap_data.frame_number = FramePrefixData.unpack(data).frame_number
        msd = MarkerSetData.unpack(data)
        mocap_data.marker_sets = msd.marker_sets
        mocap_data.unlabeled_markers = msd.unlabeled_markers
        mocap_data.rigid_bodies = unpack_rigid_bodies(data, major, minor)
        mocap_data.skeletons = unpack_skeletons(data, major, minor)
        mocap_data.labeled_markers = unpack_labeled_markers(data, major, minor)
        mocap_data.force_plates = unpack_force_plates(data, major, minor)
        mocap_data.devices = unpack_devices(data, major, minor)
        mocap_data.suffix_data = FrameSuffixData.unpack(data, major, minor)
        _ = data.read_int()
        return mocap_data


@dataclass
class Response:
    data: bytes

    @classmethod
    def unpack(cls, data: Buffer, packet_size: int, major: int,
               minor: int) -> 'Response':
        # if packet_size == 4:
        #     return cls(str(data.read_int()))
        return cls(data.read_bytes(packet_size))


@dataclass
class EchoResponse:

    request_stamp: int
    received_stamp: int

    @classmethod
    def unpack(cls, data: Buffer, packet_size: int, major: int,
               minor: int) -> 'EchoResponse':
        return cls(data.read_ulong(), data.read_ulong())


@dataclass
class MarkerSetDescription:
    name: str = "Not Set"
    markers: List[str] = field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer) -> 'MarkerSetDescription':
        ms_desc = cls()
        ms_desc.name = data.read_string()
        marker_count = data.read_int()
        for i in range(marker_count):
            name = data.read_string()
            ms_desc.markers.append(name)
        return ms_desc


@dataclass
class RBMarker:
    name: str = ""
    active_label: int = 0
    position: Vector3 = field(default_factory=lambda: np.zeros(3))


@dataclass
class RigidBodyDescription:
    name: str = ""
    new_id: int = 0
    parent_id: int = 0
    position: Vector3 = field(default_factory=lambda: np.zeros(3))
    rb_markers: List[RBMarker] = field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer, major: int) -> 'RigidBodyDescription':
        rb_desc = cls()
        # Version 2.0 or higher
        if major >= 2 or major == 0:
            rb_desc.name = data.read_string()
        rb_desc.new_id = data.read_int()
        rb_desc.parent_id = data.read_int()
        rb_desc.position = data.read_vector()
        # Version 3.0 and higher, rigid body marker information
        # contained in description
        if major >= 3 or major == 0:
            marker_count = data.read_int()
            offsets = [data.read_vector() for _ in range(marker_count)]
            labels = [data.read_int() for _ in range(marker_count)]
            if major >= 4 or major == 0:
                names = [data.read_string() for _ in range(marker_count)]
            else:
                names = ["" for _ in range(marker_count)]
            for offset, label, name in zip(offsets, labels, names):
                rb_desc.rb_markers.append(RBMarker(name, label, offset))
        return rb_desc


@dataclass
class SkeletonDescription:
    name: str = ""
    new_id: int = 0
    rigid_bodies: List[RigidBodyDescription] = field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer, major: int) -> 'SkeletonDescription':
        skeleton_desc = cls()
        skeleton_desc.name = data.read_string()
        skeleton_desc.new_id = data.read_int()
        rigid_body_count = data.read_int()
        for i in range(rigid_body_count):
            rb_desc = RigidBodyDescription.unpack(data, major)
            skeleton_desc.rigid_bodies.append(rb_desc)
        return skeleton_desc


@dataclass
class ForcePlateDescription:
    id_num: int = 0
    serial_number: str = ""
    width: float = 0
    length: float = 0
    position: Vector3 = field(default_factory=lambda: np.zeros(3))
    cal_matrix: npt.NDArray[np.float64] = field(default_factory=lambda: np.zeros((12, 12)))
    corners: npt.NDArray[np.float64] = field(default_factory=lambda: np.zeros((3, 4)))
    plate_type: int = 0
    channel_data_type: int = 0
    channels: List[str] = field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer,
               major: int) -> Optional['ForcePlateDescription']:
        fp_desc = None
        if major >= 3:
            fp_desc = cls()
            fp_desc.id_num = data.read_int()
            fp_desc.serial_number = data.read_string()
            fp_desc.width = data.read_float()
            fp_desc.length = data.read_float()
            fp_desc.position = data.read_vector()
            # TODO(Jerome): check with original version
            # ... sizes, bytes read and so on
            for i in range(12):
                fp_desc.cal_matrix[i] = data.read_matrix()
            corners = data.read_matrix()
            o_2 = 0
            for i in range(4):
                fp_desc.corners[i][0] = corners[o_2]
                fp_desc.corners[i][1] = corners[o_2 + 1]
                fp_desc.corners[i][2] = corners[o_2 + 2]
                o_2 += 3
            # Plate Type int
            fp_desc.plate_type = data.read_int()
            fp_desc.channel_data_type = data.read_int()
            num_channels = data.read_int()
            for i in range(num_channels):
                fp_desc.channels.append(data.read_string())
        return fp_desc


@dataclass
class DeviceDescription:
    id_num: int
    name: str
    serial_number: str
    device_type: int
    channel_data_type: int
    channels: List[str] = field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer, major: int) -> Optional['DeviceDescription']:
        device_desc = None
        if major >= 3:
            new_id = data.read_int()
            name = data.read_string()
            serial_number = data.read_string()
            device_type = data.read_int()
            channel_data_type = data.read_int()
            device_desc = cls(new_id, name, serial_number, device_type,
                              channel_data_type)
            num_channels = data.read_int()
            for _ in range(num_channels):
                device_desc.channels.append(data.read_string())
        return device_desc


@dataclass
class CameraDescription:
    name: str
    position: Vector3
    orientation: Quaternion

    @classmethod
    def unpack(cls, data: Buffer) -> 'CameraDescription':
        name = data.read_string()
        position = data.read_vector()
        orientation = data.read_quaternion()
        camera_desc = cls(name, position, orientation)
        return camera_desc


@dataclass
class DataDescriptions():
    """Data Descriptions class"""
    marker_sets: List[MarkerSetDescription] = field(default_factory=list)
    rigid_bodies: List[RigidBodyDescription] = field(default_factory=list)
    skeletons: List[SkeletonDescription] = field(default_factory=list)
    force_plates: List[ForcePlateDescription] = field(default_factory=list)
    devices: List[DeviceDescription] = field(default_factory=list)
    cameras: List[CameraDescription] = field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer, major: int) -> 'DataDescriptions':
        data_desc = cls()
        count = data.read_int()
        for _ in range(count):
            data_type = data.read_int()
            if data_type == 0:
                data_desc.marker_sets.append(MarkerSetDescription.unpack(data))
            elif data_type == 1:
                data_desc.rigid_bodies.append(
                    RigidBodyDescription.unpack(data, major))
            elif data_type == 2:
                data_desc.skeletons.append(SkeletonDescription.unpack(data, major))
            elif data_type == 3:
                fp = ForcePlateDescription.unpack(data, major)
                if fp:
                    data_desc.force_plates.append(fp)
            elif data_type == 4:
                dd = DeviceDescription.unpack(data, major)
                if dd:
                    data_desc.devices.append(dd)
            elif data_type == 5:
                data_desc.cameras.append(CameraDescription.unpack(data))
            else:
                logging.error(f"Type {data_type} is UNKNOWN")
        return data_desc


@dataclass
class ConnectionInfo:
    data_port: int
    multicast: bool
    multicast_address: str

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> 'ConnectionInfo':
        data_port = data.read("H", 2)[0]
        multicast = data.read_bool()
        multicast_address = socket.inet_ntoa(data.read_bytes(4))
        return cls(data_port, multicast, multicast_address)


@dataclass
class ServerInfo:
    application_name: str
    server_version: Version
    nat_net_stream_version_server: Version
    high_resolution_clock_frequency: int = -1
    connection_info: Optional[ConnectionInfo] = None

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> 'ServerInfo':
        application_name = data.read_string(256)
        server_version = data.read('BBBB', 4)
        nat_net_stream_version_server = data.read('BBBB', 4)

        if major >= 3:
            high_resolution_clock_frequency = data.read("Q", 8)[0]
            connection_info: Optional[ConnectionInfo] = ConnectionInfo.unpack(data, major, minor)
        else:
            high_resolution_clock_frequency = -1
            connection_info = None

        return cls(application_name, server_version,
                   nat_net_stream_version_server,
                   high_resolution_clock_frequency,
                   connection_info)


# Client/server message ids
class NAT(Enum):
    CONNECT = 0
    SERVERINFO = 1
    REQUEST = 2
    RESPONSE = 3
    REQUEST_MODELDEF = 4
    MODELDEF = 5
    REQUEST_FRAMEOFDATA = 6
    FRAMEOFDATA = 7
    MESSAGESTRING = 8
    DISCONNECT = 9
    KEEPALIVE = 10
    DISCONNECT_BY_TIMEOUT = 11
    ECHO_REQUEST = 12
    ECHO_RESPONSE = 13
    DISCOVERY = 14
    UNRECOGNIZED_REQUEST = 100


def get_message_id(data: Buffer) -> Optional[NAT]:
    value = data.read_short()
    try:
        return NAT(value)
    except ValueError:
        logging.error(f"Unknown message id {value}")
        return None


def cmd_set_nat_net_version(major: int, minor: int) -> str:
    return f"Bitstream,{major:1.1d}.{minor:1.1d}"


def unpack(data: Buffer, major: int, minor: int) -> Any:
    message_id = get_message_id(data)
    if not message_id:
        return None
    packet_size = data.read_short()
    logging.debug(f"Unpack {message_id} ({packet_size} bytes)")
    msg: Any = None
    if message_id == NAT.FRAMEOFDATA:
        msg = MoCapData.unpack(data, major, minor)
    elif message_id == NAT.MODELDEF:
        msg = DataDescriptions.unpack(data, major)
    elif message_id == NAT.SERVERINFO:
        msg = ServerInfo.unpack(data, major, minor)
    elif message_id == NAT.RESPONSE:
        msg = Response.unpack(data, packet_size, major, minor)
    elif message_id == NAT.MESSAGESTRING:
        msg = data.read_string()
    elif message_id == NAT.ECHO_RESPONSE:
        msg = EchoResponse.unpack(data, packet_size, major, minor)
    if data.remaining:
        log = logging.warning
    else:
        log = logging.debug
    log(f"Unpacked {msg}, {data.remaining} bytes remaining: {data}")
    return msg


# def request(command: NAT, msg: bytes = b"") -> bytes:
#     packet_size = 0
#     if command == NAT.REQUEST:
#         packet_size = len(msg) + 1
#     elif command == NAT.CONNECT:
#         msg = b"Ping"
#         packet_size = len(msg) + 1
#     elif command == NAT.KEEPALIVE:
#         packet_size = 0
#         msg = b""
#     return b"".join((struct.pack("<HH", command.value, packet_size),
#                      msg, b"\0"))


def request(command: NAT, msg: bytes = b"") -> bytes:
    return b"".join((struct.pack("<HH", command.value, len(msg)),
                     msg))


def pack_version(version: Version) -> bytes:
    return struct.pack("4B", *version)


def connect_request(version: Version = (3, 0, 0, 0), version_1: Version = (3, 0, 0, 0)) -> bytes:
    return request(NAT.CONNECT, b"\0" * 256 + pack_version(version) + pack_version(version_1))


def discovery_request(version: Version = (3, 0, 0, 0), version_1: Version = (3, 0, 0, 0)) -> bytes:
    return request(NAT.DISCOVERY, b"\0" * 256 + pack_version(version) + pack_version(version_1))


def echo_request(timestamp: int) -> bytes:
    data = struct.pack("<Q", timestamp)
    return request(NAT.ECHO_REQUEST, data)
