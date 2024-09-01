import dataclasses as dc
import enum
import logging
import socket
from typing import Any, Callable, Protocol, Self, Type, TypeVar, cast

from .buffer import Buffer, MatrixRow, Quaternion, Vector3
from .write_buffer import WriteBuffer

major: int = 3
minor: int = 0

Matrix12x12 = tuple[MatrixRow, MatrixRow, MatrixRow, MatrixRow, MatrixRow,
                    MatrixRow, MatrixRow, MatrixRow, MatrixRow, MatrixRow,
                    MatrixRow, MatrixRow]
Matrix3x4 = tuple[Vector3, Vector3, Vector3, Vector3]


def set_version(major_version: int, minor_version: int) -> None:
    global major
    global minor
    major = major_version
    minor = minor_version


def get_version() -> tuple[int, int]:
    return major, minor


class Msg(Protocol):

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        ...

    def pack(self, data: WriteBuffer) -> None:
        ...


T = TypeVar("T", bound=Msg)
V = TypeVar("V")


def unpack_items(cls: Type[T], data: Buffer) -> list[T]:
    count = data.read_int()
    return [cls.unpack(data) for _ in range(count)]


def pack_items(items: list[T], data: WriteBuffer) -> None:
    data.write_int(len(items))
    for item in items:
        item.pack(data)


def read_items(data: Buffer, reader: Callable[[], V]) -> list[V]:
    count = data.read_int()
    return [reader() for _ in range(count)]


def write_items(items: list[V], data: WriteBuffer,
                writer: Callable[[V], None]) -> None:
    data.write_int(len(items))
    for item in items:
        writer(item)


@dc.dataclass
class Version:
    """A message describing a version"""

    value: tuple[int, int, int, int]
    """(`major`, `minor`, `build`, `revision`) numbers"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls(data.read("4B", 4))

    def pack(self, data: WriteBuffer) -> None:
        data.write("4B", *self.value)

    @property
    def major(self) -> int:
        """
        The major version
        """
        return self.value[0]

    @property
    def minor(self) -> int:
        """
        The minor version
        """
        return self.value[1]


@dc.dataclass
class FramePrefixData:
    frame_number: int

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        frame_number = data.read_int()
        return cls(frame_number)

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(self.frame_number)


@dc.dataclass
class MarkerSetData:
    """
       The state of a set of markers
    """
    name: str = ""
    """name"""
    positions: list[Vector3] = dc.field(default_factory=list)
    """positions"""


@dc.dataclass
class MarkersData:
    """
       The state of sets of markers
    """
    marker_sets: list[MarkerSetData] = dc.field(default_factory=list)
    """marker sets"""
    unlabeled_markers_positions: list[Vector3] = dc.field(default_factory=list)
    """unlabeled markers"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        markers = cls()
        marker_set_count = data.read_int()
        for i in range(marker_set_count):
            marker_data = MarkerSetData()
            marker_data.name = data.read_string()
            marker_count = data.read_int()
            for j in range(marker_count):
                marker_data.positions.append(data.read_vector())
            markers.marker_sets.append(marker_data)
        unlabeled_markers_count = data.read_int()
        ps = markers.unlabeled_markers_positions
        for i in range(unlabeled_markers_count):
            ps.append(data.read_vector())
        return markers

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(len(self.marker_sets))
        for marker_set in self.marker_sets:
            data.write_string(marker_set.name)
            data.write_int(len(marker_set.positions))
            for p in marker_set.positions:
                data.write_vector(p)
        data.write_int(len(self.unlabeled_markers_positions))
        for p in self.unlabeled_markers_positions:
            data.write_vector(p)


@dc.dataclass
class RigidBodyMarkerData:
    """
       The state of a rigid body marker
    """
    position: Vector3 = (0, 0, 0)
    """position"""
    id: int = 0
    size: float = 0.0
    """marker size"""
    error: float = 0.0
    """marker error residual, in m/ray"""


@dc.dataclass
class RigidBodyData:
    """
        The state of a rigid body.
    """
    id: int
    """
        RigidBody identifier

        For rigid body assets, this is the Streaming ID value.
        For skeleton assets, this combines both skeleton ID (High-bit)
        and Bone ID (Low-bit).
    """
    position: Vector3
    """position"""
    orientation: Quaternion
    """orientation"""
    markers: list[RigidBodyMarkerData] = dc.field(default_factory=list)
    """markers"""
    tracking_valid: bool = False
    """whether the rigid body is currently tracked"""
    error: float = 0.0
    """Mean measure-to-solve deviation (mean marker error) (meters)"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        id = data.read_int()
        pos = data.read_vector()
        rot = data.read_quaternion()
        rigid_body = cls(id, pos, rot)
        # RB Marker Data ( Before version 3.0.
        # After Version 3.0 Marker data is in description )
        if major < 3 and major != 0:
            marker_count = data.read_int()
            markers = rigid_body.markers
            for i in range(marker_count):
                markers.append(
                    RigidBodyMarkerData(position=data.read_vector()))
            if major >= 2:
                for i in range(marker_count):
                    markers[i].id = data.read_int()
                for i in range(marker_count):
                    markers[i].size = data.read_float()
        if major >= 2:
            rigid_body.error = data.read_float()
        # Version 2.6 and later
        if (major == 2 and minor >= 6) or major > 2:
            param = data.read_short()
            rigid_body.tracking_valid = (param & 0x01) != 0
        return rigid_body

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(self.id)
        data.write_vector(self.position)
        data.write_quaternion(self.orientation)
        if major < 3 and major != 0:
            data.write_int(len(self.markers))
            for m in self.markers:
                data.write_vector(m.position)
            if major >= 2:
                for m in self.markers:
                    data.write_int(m.id)
                for m in self.markers:
                    data.write_float(m.size)
        if major >= 2:
            data.write_float(self.error)
        if (major == 2 and minor >= 6) or major > 2:
            param = 0x01 if self.tracking_valid else 0
            data.write_short(param)


@dc.dataclass
class SkeletonData:
    """
        Skeleton data (requires Motive Body)
    """
    id: int = 0
    """Skeleton unique identifier"""
    rigid_bodies: list[RigidBodyData] = dc.field(default_factory=list)
    """Rigid bodies composing the skeleton"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        skeleton = cls(data.read_int())
        skeleton.rigid_bodies = unpack_items(RigidBodyData, data)
        return skeleton

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(self.id)
        pack_items(self.rigid_bodies, data)


def unpack_skeletons(data: Buffer) -> list[SkeletonData]:
    if (major == 2 and minor > 0) or major > 2:
        return unpack_items(SkeletonData, data)
    return []


@dc.dataclass
class LabeledMarkerData:
    """
        State of a labeled marker
    """
    id: int
    """Unique identifier

       For active markers, this is the Active ID. For passive markers, this is the PointCloud assigned ID.
       For legacy assets that are created prior to 2.0, this is both AssetID (High-bit) and Member ID (Lo-bit)
    """
    position: Vector3
    """marker position"""
    size: float = 0.0
    """marker size"""
    param: int = 0
    """bitmask of host defined parameters.  Bit values:

       - 0: Occluded
       - 1: PointCloudSolved
       - 2: ModelFilled
       - 3: HasModel
       - 4: Unlabeled
       - 5: Active
       - 6: Established
       - 7: Measurement
    """
    residual: float = 0.0
    """marker error residual, in m/ray"""

    @property
    def decoded_marker_id(self) -> tuple[int, int]:
        model_id = self.id >> 16
        marker_id = self.id & 0x0000ffff
        return model_id, marker_id

    @property
    def decoded_param(self) -> tuple[bool, bool, bool]:
        occluded = (self.param & 0x01) != 0
        point_cloud_solved = (self.param & 0x02) != 0
        model_solved = (self.param & 0x04) != 0
        return occluded, point_cloud_solved, model_solved

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
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
        return cls(tmp_id, pos, size, param, residual)

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(self.id)
        data.write_vector(self.position)
        data.write_float(self.size)
        if (major == 2 and minor >= 6) or major > 2:
            data.write_short(self.param)
        if major >= 3:
            data.write_float(self.residual)


def unpack_labeled_markers(data: Buffer) -> list[LabeledMarkerData]:
    if (major == 2 and minor > 3) or major > 2:
        return unpack_items(LabeledMarkerData, data)
    return []


@dc.dataclass
class AnalogChannelData:
    """
        Data read from an analog channel
    """
    values: list[float] = dc.field(default_factory=list)
    """Signal readings"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls(read_items(data, data.read_float))

    def pack(self, data: WriteBuffer) -> None:
        write_items(self.values, data, data.write_float)


@dc.dataclass
class ForcePlateData:
    """
        Data read by a force plate
    """
    id: int = 0
    """ForcePlate ID"""
    channels: list[AnalogChannelData] = dc.field(default_factory=list)
    """Channels (signal) (e.g. Fx[], Fy[], Fz[])"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        id_ = data.read_int()
        return cls(id_, unpack_items(AnalogChannelData, data))

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(self.id)
        pack_items(self.channels, data)


def unpack_force_plates(data: Buffer) -> list[ForcePlateData]:
    # Force Plate data (version 2.9 and later)
    if (major == 2 and minor >= 9) or major > 2:
        return unpack_items(ForcePlateData, data)
    return []


@dc.dataclass
class DeviceData:
    """
        Data read by external device
    """
    id: int = 0
    "Device ID"
    channels: list[AnalogChannelData] = dc.field(default_factory=list)
    """Channels data (e.g. ai0, ai1, ai2)"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        id_ = data.read_int()
        return cls(id_, unpack_items(AnalogChannelData, data))

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(self.id)
        pack_items(self.channels, data)


def unpack_devices(data: Buffer) -> list[DeviceData]:
    # Force Plate data (version 2.9 and later)
    if (major == 2 and minor >= 11) or major > 2:
        return unpack_items(DeviceData, data)
    return []


@dc.dataclass
class FrameSuffixData:
    """
        Metadata of an Optitrack update
    """
    timecode: int = -1
    """SMPTE timecode (if available)"""
    timecode_sub: int = -1
    """timecode sub-frame data"""
    timestamp: float = -1
    """timestamp since software start ( software timestamp )"""
    stamp_camera_mid_exposure: int = -1
    """Given in host's high resolution ticks (from e.g. QueryPerformanceCounter)"""
    stamp_data_received: int = -1
    """Given in host's high resolution ticks (from e.g. QueryPerformanceCounter)"""
    stamp_transmit: int = -1
    """Given in host's high resolution ticks (from e.g. QueryPerformanceCounter)"""
    # param: int = 0
    """host defined parameters"""
    is_recording: bool = False
    """whether is recording"""
    tracked_models_changed: bool = False
    """whether the model list changed"""
    is_editing: bool = False
    """whether it is in editing mode (vs live mode)"""
    bitstream_version_changed: bool = False
    """whether the bitstream version has changed"""

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> Self:
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
        frame_suffix_data.is_recording = (param & 0x01) != 0
        frame_suffix_data.tracked_models_changed = (param & 0x02) != 0
        frame_suffix_data.is_editing = (param & 0x04) != 0
        frame_suffix_data.bitstream_version_changed = (param & 0x08) != 0
        return frame_suffix_data

    def pack(self, data: WriteBuffer) -> None:
        data.write_int(self.timecode)
        data.write_int(self.timecode_sub)
        if (major == 2 and minor >= 7) or major > 2:
            data.write_double(self.timestamp)
        else:
            data.write_float(self.timestamp)
        if major >= 3:
            data.write_long(self.stamp_camera_mid_exposure)
            data.write_long(self.stamp_data_received)
            data.write_long(self.stamp_transmit)
        param = 0
        if self.is_recording:
            param += 1
        if self.tracked_models_changed:
            param += 2
        if self.is_editing:
            param += 4
        if self.bitstream_version_changed:
            param += 8
        data.write_short(param)


@dc.dataclass
class MoCapData:
    """
        Data gathered during one Optitrack update
    """
    frame_number: int = -1
    """host defined frame number"""
    marker_sets: list[MarkerSetData] = dc.field(default_factory=list)
    """marker sets"""
    unlabeled_markers_positions: list[Vector3] = dc.field(default_factory=list)
    """unlabeled markers"""
    rigid_bodies: list[RigidBodyData] = dc.field(default_factory=list)
    """rigid bodies"""
    skeletons: list[SkeletonData] = dc.field(default_factory=list)
    """skeletons"""
    labeled_markers: list[LabeledMarkerData] = dc.field(default_factory=list)
    """labeled markers"""
    force_plates: list[ForcePlateData] = dc.field(default_factory=list)
    """force plates"""
    devices: list[DeviceData] = dc.field(default_factory=list)
    """devices"""
    suffix_data: FrameSuffixData | None = None
    """frame metadata (timing, state, ...)"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        mocap_data = cls()
        mocap_data.frame_number = FramePrefixData.unpack(data).frame_number
        msd = MarkersData.unpack(data)
        mocap_data.marker_sets = msd.marker_sets
        mocap_data.unlabeled_markers_positions = msd.unlabeled_markers_positions
        mocap_data.rigid_bodies = unpack_items(RigidBodyData, data)
        mocap_data.skeletons = unpack_skeletons(data)
        mocap_data.labeled_markers = unpack_labeled_markers(data)
        mocap_data.force_plates = unpack_force_plates(data)
        mocap_data.devices = unpack_devices(data)
        mocap_data.suffix_data = FrameSuffixData.unpack(data, major, minor)
        _ = data.read_int()
        return mocap_data

    def pack(self, data: WriteBuffer) -> None:
        FramePrefixData(self.frame_number).pack(data)
        MarkersData(self.marker_sets,
                    self.unlabeled_markers_positions).pack(data)
        pack_items(self.rigid_bodies, data)
        pack_items(self.skeletons, data)
        pack_items(self.labeled_markers, data)
        pack_items(self.force_plates, data)
        pack_items(self.devices, data)
        if self.suffix_data:
            self.suffix_data.pack(data)
        data.write_int(0)


@dc.dataclass
class Response:
    data: bytes

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        # if packet_size == 4:
        #     return cls(str(data.read_int()))
        return cls(data.read_bytes(0))

    def pack(self, data: WriteBuffer) -> None:
        data.write_bytes(self.data)


@dc.dataclass
class EchoResponse:
    """Response from an echo request"""

    request_stamp: int
    """the (client) stamp when the request was sent"""
    received_stamp: int
    """the (server) receiving stamp"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls(data.read_ulong(), data.read_ulong())

    def pack(self, data: WriteBuffer) -> None:
        data.write_ulong(self.request_stamp)
        data.write_ulong(self.received_stamp)


@dc.dataclass
class MarkerSetDescription:
    """A set of markers"""
    name: str = "Not Set"
    """name"""
    markers: list[str] = dc.field(default_factory=list)
    """marker names"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        ms_desc = cls()
        ms_desc.name = data.read_string()
        ms_desc.markers = read_items(data, data.read_string)
        return ms_desc

    def pack(self, data: WriteBuffer) -> None:
        data.write_string(self.name)
        write_items(self.markers, data, data.write_string)


@dc.dataclass
class RBMarker:
    """A marker that is part of a rigid body"""
    name: str = ""
    """name"""
    active_label: int = 0
    """active label (0 if not specified)"""
    position: Vector3 = (0, 0, 0)
    """marker location"""


@dc.dataclass
class RigidBodyDescription:
    """A rigid body"""
    name: str = ""
    """name"""
    id: int = 0
    """
        RigidBody identifier

        Streaming ID value for rigid body assets, and Bone index value for skeleton rigid bodies.
    """
    parent_id: int = 0
    """ID of parent Rigid Body (in case hierarchy exists; otherwise -1)"""
    position: Vector3 = (0, 0, 0)
    """offset position relative to parent"""
    markers: list[RBMarker] = dc.field(default_factory=list)
    """markers"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        rb_desc = cls()
        # Version 2.0 or higher
        if major >= 2 or major == 0:
            rb_desc.name = data.read_string()
        rb_desc.id = data.read_int()
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
                rb_desc.markers.append(RBMarker(name, label, offset))
        return rb_desc

    def pack(self, data: WriteBuffer) -> None:
        if major >= 2 or major == 0:
            data.write_string(self.name)
        data.write_int(self.id)
        data.write_int(self.parent_id)
        data.write_vector(self.position)
        if major >= 3 or major == 0:
            data.write_int(len(self.markers))
            for offset in [m.position for m in self.markers]:
                data.write_vector(offset)
            for label in [m.active_label for m in self.markers]:
                data.write_int(label)
            if major >= 4 or major == 0:
                for name in [m.name for m in self.markers]:
                    data.write_string(name)


@dc.dataclass
class SkeletonDescription:
    """
        A Skeleton
    """
    name: str = ""
    """name"""
    id: int = 0
    """unique identifier"""
    rigid_bodies: list[RigidBodyDescription] = dc.field(default_factory=list)
    """rigid bodies (bones) descriptions"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        skeleton_desc = cls()
        skeleton_desc.name = data.read_string()
        skeleton_desc.id = data.read_int()
        skeleton_desc.rigid_bodies = unpack_items(RigidBodyDescription, data)
        return skeleton_desc

    def pack(self, data: WriteBuffer) -> None:
        data.write_string(self.name)
        data.write_int(self.id)
        pack_items(self.rigid_bodies, data)


@dc.dataclass
class ForcePlateDescription:
    """
       A force plate
    """
    id: int = 0
    """used for order, and for identification in the data stream"""
    serial_number: str = ""
    """for unique plate identification"""
    width: float = 0
    """plate physical width (manufacturer supplied)"""
    length: float = 0
    """plate physical length (manufacturer supplied)"""
    position: Vector3 = (0, 0, 0)
    """electrical center offset (from electrical center to geometric center-top of force plate) (manufacturer supplied)"""
    cal_matrix: Matrix12x12 | None = None
    """force plate calibration matrix (for raw analog voltage channel type only)"""
    corners: Matrix3x4 | None = None
    """plate corners, in world (aka Mocap System) coordinates, clockwise from plate +x,+y (refer to C3D spec for details)"""
    plate_type: int = 0
    """force plate 'type' (refer to C3D spec for details)"""
    channel_data_type: int = 0
    """0=Calibrated force data, 1=Raw analog voltages"""
    channels: list[str] = dc.field(default_factory=list)
    """channel names"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self | None:
        fp_desc = None
        if major >= 3:
            fp_desc = cls()
            fp_desc.id = data.read_int()
            fp_desc.serial_number = data.read_string()
            fp_desc.width = data.read_float()
            fp_desc.length = data.read_float()
            fp_desc.position = data.read_vector()
            # TODO(Jerome): check with original version
            # ... sizes, bytes read and so on
            fp_desc.cal_matrix = cast(
                Matrix12x12, tuple(data.read_matrix_row() for i in range(12)))
            corners = data.read_matrix_row()
            fp_desc.corners = cast(
                Matrix3x4, tuple(corners[3 * i:3 * i + 3] for i in range(4)))
            # Plate Type int
            fp_desc.plate_type = data.read_int()
            fp_desc.channel_data_type = data.read_int()
            fp_desc.channels = read_items(data, data.read_string)
        return fp_desc

    def pack(self, data: WriteBuffer) -> None:
        if major >= 3:
            raise NotImplementedError()
        # data.write_int(self.id)
        # data.write_string(self.serial_number)
        # data.write_float(self.width)
        # data.write_float(self.length)
        # data.write_vector(self.position)
        # TODO(Jerome): complete


@dc.dataclass
class DeviceDescription:
    """
        An external device
    """
    id: int
    """used for order, and for identification in the data stream"""
    name: str
    """device name as appears in Motive"""
    serial_number: str
    """for unique device identification"""
    device_type: int
    """device 'type' code"""
    channel_data_type: int
    """channel data type code"""
    channels: list[str] = dc.field(default_factory=list)
    """channel names"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self | None:
        device_desc = None
        if major >= 3:
            id = data.read_int()
            name = data.read_string()
            serial_number = data.read_string()
            device_type = data.read_int()
            channel_data_type = data.read_int()
            device_desc = cls(id, name, serial_number, device_type,
                              channel_data_type)
            device_desc.channels = read_items(data, data.read_string)
        return device_desc

    def pack(self, data: WriteBuffer) -> None:
        if major >= 3:
            data.write_int(self.id)
            data.write_string(self.name)
            data.write_string(self.serial_number)
            data.write_int(self.device_type)
            data.write_int(self.channel_data_type)
            write_items(self.channels, data, data.write_string)


@dc.dataclass
class CameraDescription:
    """
       A MoCap Camera
    """
    name: str
    """name"""
    position: Vector3
    """position"""
    orientation: Quaternion
    """orientation"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        name = data.read_string()
        position = data.read_vector()
        orientation = data.read_quaternion()
        return cls(name, position, orientation)

    def pack(self, data: WriteBuffer) -> None:
        data.write_string(self.name)
        data.write_vector(self.position)
        data.write_quaternion(self.orientation)


@dc.dataclass
class MoCapDescription:
    """Data Descriptions class"""
    marker_sets: list[MarkerSetDescription] = dc.field(default_factory=list)
    rigid_bodies: list[RigidBodyDescription] = dc.field(default_factory=list)
    skeletons: list[SkeletonDescription] = dc.field(default_factory=list)
    force_plates: list[ForcePlateDescription] = dc.field(default_factory=list)
    devices: list[DeviceDescription] = dc.field(default_factory=list)
    cameras: list[CameraDescription] = dc.field(default_factory=list)

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        data_desc = cls()
        count = data.read_int()
        for _ in range(count):
            data_type = data.read_int()
            if data_type == 0:
                data_desc.marker_sets.append(MarkerSetDescription.unpack(data))
            elif data_type == 1:
                data_desc.rigid_bodies.append(
                    RigidBodyDescription.unpack(data))
            elif data_type == 2:
                data_desc.skeletons.append(SkeletonDescription.unpack(data))
            elif data_type == 3:
                fp = ForcePlateDescription.unpack(data)
                if fp:
                    data_desc.force_plates.append(fp)
            elif data_type == 4:
                dd = DeviceDescription.unpack(data)
                if dd:
                    data_desc.devices.append(dd)
            elif data_type == 5:
                data_desc.cameras.append(CameraDescription.unpack(data))
            else:
                logging.error(f"Type {data_type} is UNKNOWN")
        return data_desc

    def pack(self, data: WriteBuffer) -> None:
        count = (len(self.marker_sets) + len(self.rigid_bodies) +
                 len(self.skeletons) + len(self.force_plates) +
                 len(self.devices) + len(self.cameras))
        data.write_int(count)
        for marker_set in self.marker_sets:
            data.write_int(0)
            marker_set.pack(data)
        for rigid_body in self.rigid_bodies:
            data.write_int(1)
            rigid_body.pack(data)
        for skeleton in self.skeletons:
            data.write_int(2)
            skeleton.pack(data)
        for force_plate in self.force_plates:
            data.write_int(3)
            force_plate.pack(data)
        for device in self.devices:
            data.write_int(4)
            device.pack(data)
        for camera in self.cameras:
            data.write_int(5)
            camera.pack(data)


@dc.dataclass
class ConnectionInfo:
    """Connection information"""
    data_port: int
    """the port used to stream data"""
    multicast: bool
    """whether the server uses multicasting"""
    multicast_address: str
    """the multicast address to stream data"""

    @classmethod
    def unpack(cls, data: Buffer, major: int, minor: int) -> Self:
        data_port = data.read("H", 2)[0]
        multicast = data.read_bool()
        multicast_address = socket.inet_ntoa(data.read_bytes(4))
        return cls(data_port, multicast, multicast_address)

    def pack(self, data: WriteBuffer) -> None:
        data.write("H", self.data_port)
        data.write_bool(self.multicast)
        data.write_bytes(socket.inet_aton(self.multicast_address))


@dc.dataclass
class ServerInfo:
    """Information about the NatNet server"""
    application_name: str
    """host computer name"""
    server_version: Version
    """version of host app"""
    nat_net_stream_version_server: Version
    """host app's version of NatNet"""
    high_resolution_clock_frequency: int = -1
    """host's high resolution clock frequency (ticks per second)"""
    connection_info: ConnectionInfo | None = None
    """connection information"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        application_name = data.read_string(256)
        server_version = Version.unpack(data)
        nat_net_stream_version_server = Version.unpack(data)

        major = nat_net_stream_version_server.major
        minor = nat_net_stream_version_server.minor

        if major >= 3:
            high_resolution_clock_frequency = data.read("Q", 8)[0]
            connection_info: ConnectionInfo | None = ConnectionInfo.unpack(
                data, major, minor)
        else:
            high_resolution_clock_frequency = -1
            connection_info = None

        return cls(application_name, server_version,
                   nat_net_stream_version_server,
                   high_resolution_clock_frequency, connection_info)

    def pack(self, data: WriteBuffer) -> None:
        data.write_string(self.application_name, 256)
        self.server_version.pack(data)
        self.nat_net_stream_version_server.pack(data)
        if major >= 3:
            data.write("Q", self.high_resolution_clock_frequency)
            if self.connection_info:
                self.connection_info.pack(data)


@dc.dataclass
class ConnectRequest:
    """A connection request"""
    version: Version = dc.field(default_factory=lambda: Version((3, 0, 0, 0)))
    """?"""
    version_1: Version = dc.field(
        default_factory=lambda: Version((3, 0, 0, 0)))
    """?"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        _ = data.read("256B", 256)
        version = Version.unpack(data)
        version_1 = Version.unpack(data)
        return cls(version, version_1)

    def pack(self, data: WriteBuffer) -> None:
        data.write_bytes(b"\0" * 256)
        self.version.pack(data)
        self.version_1.pack(data)


@dc.dataclass
class DiscoveryRequest:
    """A discovery request"""
    version: Version = dc.field(default_factory=lambda: Version((3, 0, 0, 0)))
    """?"""
    version_1: Version = dc.field(
        default_factory=lambda: Version((3, 0, 0, 0)))
    """?"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        _ = data.read("256B", 256)
        version = Version.unpack(data)
        version_1 = Version.unpack(data)
        return cls(version, version_1)

    def pack(self, data: WriteBuffer) -> None:
        data.write_bytes(b"\0" * 256)
        self.version.pack(data)
        self.version_1.pack(data)


@dc.dataclass
class EchoRequest:
    """An echo request used to synchronize clocks"""
    timestamp: int
    """the (client) sending stamp"""

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls(data.read_ulong())

    def pack(self, data: WriteBuffer) -> None:
        data.write_ulong(self.timestamp)


@dc.dataclass
class Request:
    data: bytes

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls(data.read_bytes(0))

    def pack(self, data: WriteBuffer) -> None:
        data.write_bytes(self.data)


@dc.dataclass
class ModelDefRequest:

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls()

    def pack(self, data: WriteBuffer) -> None:
        pass


@dc.dataclass
class MessageString:

    value: str

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls(data.read_string())

    def pack(self, data: WriteBuffer) -> None:
        data.write_string(self.value)


@dc.dataclass
class KeepAliveRequest:

    @classmethod
    def unpack(cls, data: Buffer) -> Self:
        return cls()

    def pack(self, data: WriteBuffer) -> None:
        pass


# Client/server message ids
class NAT(enum.Enum):
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


message_types: dict[NAT, Type[Msg]] = {
    NAT.CONNECT: ConnectRequest,
    NAT.SERVERINFO: ServerInfo,
    NAT.REQUEST: Request,
    NAT.RESPONSE: Response,
    NAT.REQUEST_MODELDEF: ModelDefRequest,
    NAT.MODELDEF: MoCapDescription,
    # NAT.REQUEST_FRAMEOFDATA: ,
    NAT.FRAMEOFDATA: MoCapData,
    NAT.MESSAGESTRING: MessageString,
    # NAT.DISCONNECT: ,
    NAT.KEEPALIVE: KeepAliveRequest,
    # NAT.DISCONNECT_BY_TIMEOUT: ,
    NAT.ECHO_REQUEST: EchoRequest,
    NAT.ECHO_RESPONSE: EchoResponse,
    NAT.DISCOVERY: DiscoveryRequest,
    # NAT.UNRECOGNIZED_REQUEST: ,
}

message_ids: dict[Type[Msg], NAT] = {v: k for k, v in message_types.items()}


def get_message_id(data: Buffer) -> NAT | None:
    value = data.read_short()
    try:
        return NAT(value)
    except ValueError:
        logging.error(f"Unknown message id {value}")
        return None


def cmd_set_nat_net_version(major: int, minor: int) -> str:
    return f"Bitstream,{major:1.1d}.{minor:1.1d}"


def unpack(data: Buffer) -> Msg | None:
    message_id = get_message_id(data)
    if not message_id:
        return None
    packet_size = data.read_short()
    logging.debug(f"Unpack {message_id} ({packet_size} bytes)")
    msg: Any = None
    msg_type = message_types.get(message_id)
    if msg_type:
        msg = msg_type.unpack(data)
    else:
        msg = None
        logging.warning(f"Unsupported message type {msg_type}")
    if data.remaining:
        log = logging.warning
    else:
        log = logging.debug
    log(f"Unpacked {msg}, {data.remaining} bytes remaining: {data}")
    return msg


def pack(msg: Msg) -> bytes:
    logging.debug(f"pack {msg}")
    message_id = message_ids.get(type(msg))
    if not message_id:
        return b''
    buffer = WriteBuffer()
    buffer.write_short(message_id.value)
    buffer.write_short(0)
    msg.pack(buffer)
    packet_size = len(buffer.data) - 4
    buffer.set_short(2, packet_size)
    return buffer.data
