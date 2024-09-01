Search.setIndex({"alltitles": {"API Reference": [[7, null]], "Asynchronous (asyncio) Client": [[6, null]], "Clock": [[2, "clock"]], "Connection": [[2, "connection"], [8, "connection"]], "Contents:": [[3, null], [7, null]], "Discover": [[0, "discover"]], "Discovery": [[2, "discovery"], [8, "discovery"]], "Echo": [[8, "echo"]], "Example": [[0, "example"], [0, "id1"], [0, "id2"]], "Executables": [[0, null]], "First steps": [[1, null]], "GUI": [[0, "gui"]], "How it works": [[2, null]], "Installation": [[4, null]], "Interactive shell": [[0, "interactive-shell"]], "Internal API": [[8, null]], "Introduction": [[5, null]], "MoCap Data": [[11, "mocap-data"]], "MoCap Description": [[11, "mocap-description"]], "Named Arguments": [[0, "natnet_py.natnet_discover-parser-named-arguments"], [0, "natnet_py.natnet_cli-parser-named-arguments"]], "Request": [[8, "request"], [8, "id1"], [8, "id3"]], "Requests": [[8, "requests"]], "Response": [[8, "response"], [8, "id2"], [8, "id4"]], "Server": [[9, null]], "Streaming": [[2, "streaming"]], "Synchronous (Blocking) Client": [[10, null]], "Types": [[11, null]], "natnet_py documentation": [[3, null]]}, "docnames": ["executables", "first_steps", "how_it_works", "index", "installation", "introduction", "reference/async_client", "reference/index", "reference/internal", "reference/server", "reference/sync_client", "reference/types"], "envversion": {"sphinx": 63, "sphinx.domains.c": 3, "sphinx.domains.changeset": 1, "sphinx.domains.citation": 1, "sphinx.domains.cpp": 9, "sphinx.domains.index": 1, "sphinx.domains.javascript": 3, "sphinx.domains.math": 2, "sphinx.domains.python": 4, "sphinx.domains.rst": 2, "sphinx.domains.std": 2}, "filenames": ["executables.rst", "first_steps.rst", "how_it_works.rst", "index.rst", "installation.rst", "introduction.rst", "reference/async_client.rst", "reference/index.rst", "reference/internal.rst", "reference/server.rst", "reference/sync_client.rst", "reference/types.rst"], "indexentries": {}, "objects": {"": [[11, 0, 1, "", "Matrix12x12"], [11, 0, 1, "", "Matrix3x4"], [11, 0, 1, "", "Quaternion"], [11, 0, 1, "", "Vector3"]], "natnet_py": [[6, 0, 1, "", "AsyncClient"], [10, 0, 1, "", "SyncClient"]], "natnet_py.AsyncClient": [[6, 1, 1, "", "__init__"], [6, 2, 1, "", "can_change_bitstream_version"], [6, 2, 1, "", "can_subscribe"], [6, 1, 1, "", "clear_subscribtions"], [6, 1, 1, "", "close"], [6, 1, 1, "", "connect"], [6, 2, 1, "", "connected"], [6, 2, 1, "", "data_port"], [6, 2, 1, "", "description"], [6, 1, 1, "", "disable_asset"], [6, 1, 1, "", "discover"], [6, 1, 1, "", "enable_asset"], [6, 1, 1, "", "get_data"], [6, 1, 1, "", "get_framerate"], [6, 2, 1, "", "multicast_address"], [6, 2, 1, "", "server_address"], [6, 2, 1, "", "server_info"], [6, 1, 1, "", "server_ticks_to_client_ns_time"], [6, 1, 1, "", "set_framerate"], [6, 1, 1, "", "set_version"], [6, 1, 1, "", "start_listening_for_data"], [6, 1, 1, "", "subscribe"], [6, 1, 1, "", "subscribe_all"], [6, 1, 1, "", "unconnect"], [6, 1, 1, "", "unsubscribe"], [6, 1, 1, "", "update_description"], [6, 2, 1, "", "use_multicast"], [6, 1, 1, "", "wait"]], "natnet_py.SyncClient": [[10, 1, 1, "", "__init__"], [10, 2, 1, "", "can_change_bitstream_version"], [10, 2, 1, "", "can_subscribe"], [10, 1, 1, "", "close"], [10, 1, 1, "", "connect"], [10, 2, 1, "", "connected"], [10, 2, 1, "", "data_port"], [10, 2, 1, "", "description"], [10, 1, 1, "", "discover"], [10, 1, 1, "", "get_data"], [10, 2, 1, "", "multicast_address"], [10, 2, 1, "", "server_address"], [10, 2, 1, "", "server_info"], [10, 1, 1, "", "server_ticks_to_client_ns_time"], [10, 1, 1, "", "start_listening_for_data"], [10, 1, 1, "", "unconnect"], [10, 2, 1, "", "use_multicast"], [10, 1, 1, "", "wait"]], "natnet_py.protocol": [[11, 0, 1, "", "AnalogChannelData"], [11, 0, 1, "", "CameraDescription"], [8, 0, 1, "", "ConnectRequest"], [8, 0, 1, "", "ConnectionInfo"], [11, 0, 1, "", "DeviceData"], [11, 0, 1, "", "DeviceDescription"], [8, 0, 1, "", "DiscoveryRequest"], [8, 0, 1, "", "EchoRequest"], [8, 0, 1, "", "EchoResponse"], [11, 0, 1, "", "ForcePlateData"], [11, 0, 1, "", "ForcePlateDescription"], [11, 0, 1, "", "FrameSuffixData"], [11, 0, 1, "", "LabeledMarkerData"], [11, 0, 1, "", "MarkerSetData"], [11, 0, 1, "", "MarkerSetDescription"], [11, 0, 1, "", "MarkersData"], [11, 0, 1, "", "MoCapData"], [11, 0, 1, "", "MoCapDescription"], [11, 0, 1, "", "RBMarker"], [11, 0, 1, "", "RigidBodyData"], [11, 0, 1, "", "RigidBodyDescription"], [8, 0, 1, "", "ServerInfo"], [11, 0, 1, "", "SkeletonData"], [11, 0, 1, "", "SkeletonDescription"], [8, 0, 1, "", "Version"]], "natnet_py.protocol.AnalogChannelData": [[11, 3, 1, "", "values"]], "natnet_py.protocol.CameraDescription": [[11, 3, 1, "", "name"], [11, 3, 1, "", "orientation"], [11, 3, 1, "", "position"]], "natnet_py.protocol.ConnectRequest": [[8, 3, 1, "", "version"], [8, 3, 1, "", "version_1"]], "natnet_py.protocol.ConnectionInfo": [[8, 3, 1, "", "data_port"], [8, 3, 1, "", "multicast"], [8, 3, 1, "", "multicast_address"]], "natnet_py.protocol.DeviceData": [[11, 3, 1, "", "channels"], [11, 3, 1, "", "id"]], "natnet_py.protocol.DeviceDescription": [[11, 3, 1, "", "channel_data_type"], [11, 3, 1, "", "channels"], [11, 3, 1, "", "device_type"], [11, 3, 1, "", "id"], [11, 3, 1, "", "name"], [11, 3, 1, "", "serial_number"]], "natnet_py.protocol.DiscoveryRequest": [[8, 3, 1, "", "version"], [8, 3, 1, "", "version_1"]], "natnet_py.protocol.EchoRequest": [[8, 3, 1, "", "timestamp"]], "natnet_py.protocol.EchoResponse": [[8, 3, 1, "", "received_stamp"], [8, 3, 1, "", "request_stamp"]], "natnet_py.protocol.ForcePlateData": [[11, 3, 1, "", "channels"], [11, 3, 1, "", "id"]], "natnet_py.protocol.ForcePlateDescription": [[11, 3, 1, "", "cal_matrix"], [11, 3, 1, "", "channel_data_type"], [11, 3, 1, "", "channels"], [11, 3, 1, "", "corners"], [11, 3, 1, "", "id"], [11, 3, 1, "", "length"], [11, 3, 1, "", "plate_type"], [11, 3, 1, "", "position"], [11, 3, 1, "", "serial_number"], [11, 3, 1, "", "width"]], "natnet_py.protocol.FrameSuffixData": [[11, 3, 1, "", "bitstream_version_changed"], [11, 3, 1, "", "is_editing"], [11, 3, 1, "", "is_recording"], [11, 3, 1, "", "stamp_camera_mid_exposure"], [11, 3, 1, "", "stamp_data_received"], [11, 3, 1, "", "stamp_transmit"], [11, 3, 1, "", "timecode"], [11, 3, 1, "", "timecode_sub"], [11, 3, 1, "", "timestamp"], [11, 3, 1, "", "tracked_models_changed"]], "natnet_py.protocol.LabeledMarkerData": [[11, 2, 1, "", "decoded_marker_id"], [11, 2, 1, "", "decoded_param"], [11, 3, 1, "", "id"], [11, 3, 1, "", "param"], [11, 3, 1, "", "position"], [11, 3, 1, "", "residual"], [11, 3, 1, "", "size"]], "natnet_py.protocol.MarkerSetData": [[11, 3, 1, "", "name"], [11, 3, 1, "", "positions"]], "natnet_py.protocol.MarkerSetDescription": [[11, 3, 1, "", "markers"], [11, 3, 1, "", "name"]], "natnet_py.protocol.MarkersData": [[11, 3, 1, "", "marker_sets"], [11, 3, 1, "", "unlabeled_markers_positions"]], "natnet_py.protocol.MoCapData": [[11, 3, 1, "", "devices"], [11, 3, 1, "", "force_plates"], [11, 3, 1, "", "frame_number"], [11, 3, 1, "", "labeled_markers"], [11, 3, 1, "", "marker_sets"], [11, 3, 1, "", "rigid_bodies"], [11, 3, 1, "", "skeletons"], [11, 3, 1, "", "suffix_data"], [11, 3, 1, "", "unlabeled_markers_positions"]], "natnet_py.protocol.MoCapDescription": [[11, 3, 1, "", "cameras"], [11, 3, 1, "", "devices"], [11, 3, 1, "", "force_plates"], [11, 3, 1, "", "marker_sets"], [11, 3, 1, "", "rigid_bodies"], [11, 3, 1, "", "skeletons"]], "natnet_py.protocol.RBMarker": [[11, 3, 1, "", "active_label"], [11, 3, 1, "", "name"], [11, 3, 1, "", "position"]], "natnet_py.protocol.RigidBodyData": [[11, 3, 1, "", "error"], [11, 3, 1, "", "id"], [11, 3, 1, "", "markers"], [11, 3, 1, "", "orientation"], [11, 3, 1, "", "position"], [11, 3, 1, "", "tracking_valid"]], "natnet_py.protocol.RigidBodyDescription": [[11, 3, 1, "", "id"], [11, 3, 1, "", "markers"], [11, 3, 1, "", "name"], [11, 3, 1, "", "parent_id"], [11, 3, 1, "", "position"]], "natnet_py.protocol.ServerInfo": [[8, 3, 1, "", "application_name"], [8, 3, 1, "", "connection_info"], [8, 3, 1, "", "high_resolution_clock_frequency"], [8, 3, 1, "", "nat_net_stream_version_server"], [8, 3, 1, "", "server_version"]], "natnet_py.protocol.SkeletonData": [[11, 3, 1, "", "id"], [11, 3, 1, "", "rigid_bodies"]], "natnet_py.protocol.SkeletonDescription": [[11, 3, 1, "", "id"], [11, 3, 1, "", "name"], [11, 3, 1, "", "rigid_bodies"]], "natnet_py.protocol.Version": [[8, 2, 1, "", "major"], [8, 2, 1, "", "minor"], [8, 3, 1, "", "value"]], "natnet_py.server": [[9, 0, 1, "", "Server"]], "natnet_py.server.Server": [[9, 1, 1, "", "__init__"], [9, 1, 1, "", "close"], [9, 1, 1, "", "get_rigid_bodies_data"], [9, 1, 1, "", "get_rigid_bodies_def"], [9, 2, 1, "", "rate"], [9, 1, 1, "", "run"]]}, "objnames": {"0": ["py", "class", "Python class"], "1": ["py", "method", "Python method"], "2": ["py", "property", "Python property"], "3": ["py", "attribute", "Python attribute"]}, "objtypes": {"0": "py:class", "1": "py:method", "2": "py:property", "3": "py:attribute"}, "terms": {"": [1, 8, 11], "0": [0, 1, 5, 6, 9, 10, 11], "00": 1, "000e": 1, "001": 1, "009": 1, "015": 1, "04": 1, "1": [0, 1, 5, 6, 8, 9, 10, 11], "10": [0, 5, 6, 10], "105e": 1, "12": 11, "127": [0, 5, 6, 9, 10], "1510": [0, 1, 2, 6, 10], "1511": [0, 1], "2": [5, 11], "251000": 0, "255": [0, 5, 6, 10], "2d": 0, "3": [0, 1, 9, 11], "3e": 1, "4": [1, 6, 10, 11], "5": [1, 6, 10, 11], "559e": 1, "6": 11, "60": [5, 6, 9, 10], "695e": 1, "6e": 1, "7": 11, "767e": 1, "8": 1, "975e": 1, "982e": 1, "A": [0, 6, 8, 9, 10, 11], "For": [5, 11], "If": [2, 6, 10], "It": [0, 5, 6, 10], "Not": 11, "The": [0, 2, 5, 6, 8, 9, 10, 11], "Then": 2, "To": [2, 4], "Will": [], "_": 5, "__init__": [6, 9, 10], "abil": [6, 10], "abl": [6, 10], "about": [2, 8], "accept": [6, 10], "access": 5, "activ": 11, "active_label": 11, "actual": [6, 10], "add": [0, 6, 10], "address": [0, 2, 6, 8, 9, 10], "after": [2, 6, 10], "ai0": 11, "ai1": 11, "ai2": 11, "aka": 11, "alia": 11, "all": [2, 6, 10], "alreadi": 2, "an": [5, 6, 8, 10, 11], "analog": 11, "analogchanneldata": 11, "announc": [0, 2, 6, 10], "api": 3, "app": 8, "appear": 11, "application_nam": 8, "ar": [2, 6, 10, 11], "architectur": 2, "ask": [6, 10], "asset": [6, 11], "assetid": 11, "assign": 11, "async": [6, 9], "asynccli": [2, 5, 6, 7], "asynchron": [3, 5, 7], "asyncio": [3, 7], "auto": [6, 10], "automat": [0, 6, 10], "avail": [6, 10, 11], "await": [5, 6, 9], "b": [5, 6], "back": 2, "base": [0, 2, 4, 5], "basic": 0, "beta": 0, "bind": [0, 6, 10], "bit": 11, "bitmask": 11, "bitstream": [6, 10, 11], "bitstream_version_chang": 11, "block": [3, 7], "bodi": [0, 1, 2, 5, 6, 11], "bone": 11, "bool": [6, 8, 9, 10, 11], "both": [5, 11], "broadcast": [0, 6, 10], "broadcast_address": [6, 10], "browser": 0, "build": [4, 8], "built": [6, 10], "byte": [5, 6], "c": 5, "c3d": 11, "cal_matrix": 11, "calibr": 11, "call": [2, 6], "callabl": [6, 10], "callback": [5, 6, 10], "camera": 11, "cameradescript": 11, "can": [2, 4, 5, 6, 10], "can_change_bitstream_vers": [6, 10], "can_subscrib": [6, 10], "case": 11, "cd": 4, "center": 11, "chang": [5, 6, 10, 11], "channel": 11, "channel_data_typ": 11, "chosen": 5, "class": [6, 8, 9, 10, 11], "clear_subscribt": 6, "cli": [0, 1], "client": [0, 1, 2, 3, 5, 7, 8, 9], "client_async": 1, "clock": [0, 1, 3, 6, 8, 10], "clockwis": 11, "clone": 4, "close": [0, 1, 5, 6, 9, 10], "code": [9, 11], "colcon": 4, "com": 4, "combin": 11, "command": [0, 1, 2, 6, 10], "command_port": [6, 10], "commun": 5, "compil": 5, "compos": 11, "comput": 8, "configur": [2, 5, 6, 10], "connect": [0, 1, 3, 5, 6, 10], "connection_info": 8, "connectioninfo": 8, "connectrequest": 8, "connet": 6, "construct": [6, 9, 10], "constructor": 2, "contain": [0, 2], "convert": [2, 6, 10], "coordin": 11, "corner": 11, "creat": [0, 1, 6, 10, 11], "current": [6, 10, 11], "cycl": 5, "data": [0, 1, 2, 5, 6, 7, 8, 9, 10], "data_callback": [5, 6, 10], "data_port": [6, 8, 10], "debug": 0, "decoded_marker_id": 11, "decoded_param": 11, "def": 5, "default": [0, 2, 6, 10], "defin": [9, 11], "delai": [0, 1], "delta": 0, "depacket": 5, "depend": [2, 4], "describ": [0, 1, 6, 8, 10], "descript": [0, 1, 6, 7, 9, 10], "desir": 6, "detail": 11, "determin": [6, 10], "deviat": 11, "devic": 11, "device_typ": 11, "devicedata": 11, "devicedescript": 11, "dict": [6, 10], "dictionari": [6, 10], "directli": [2, 5, 6, 10], "disabl": [0, 6], "disable_asset": 6, "disconnect": [0, 1, 6, 10], "discov": [1, 2, 3, 5, 6, 10], "discoveri": [0, 3, 6, 10], "discovery_address": [5, 6, 10], "discoveryrequest": 8, "displai": 0, "document": [0, 1, 2], "done": 0, "draw": 0, "durat": [5, 6, 10], "dure": 11, "e": [5, 11], "each": 2, "echo": 2, "echorequest": [2, 8], "echorespons": [2, 8], "edit": 11, "effort": 5, "electr": 11, "els": [6, 10], "enabl": 6, "enable_asset": 6, "engin": 5, "enough": [6, 10], "epoch": [6, 10], "equival": 5, "error": [0, 11], "establish": 11, "exampl": [1, 5], "exchang": 2, "execut": 3, "exist": 11, "extern": [4, 11], "fals": [0, 5, 6, 9, 10, 11], "fetch": [6, 10], "fill": 0, "first": [3, 5, 6, 10], "float": [6, 10, 11], "forc": 11, "force_pl": 11, "forcepl": 11, "forceplatedata": 11, "forceplatedescript": 11, "frame": [9, 11], "frame_numb": 11, "framer": [5, 6, 9], "framesuffixdata": [2, 11], "frequenc": 8, "from": [2, 5, 6, 8, 11], "function": [6, 10], "fx": 11, "fy": 11, "fz": 11, "g": [5, 11], "gather": 11, "geometr": 11, "get": [2, 5, 6, 10], "get_data": [5, 6, 10], "get_framer": [5, 6], "get_properti": 5, "get_rigid_bodies_data": 9, "get_rigid_bodies_def": 9, "git": 4, "github": 4, "give": 2, "given": [6, 10, 11], "got": [0, 1], "gui": [3, 4], "h": 0, "ha": [6, 10, 11], "hasmodel": 11, "have": 5, "help": [0, 1], "helper": 0, "hierarchi": 11, "high": [8, 11], "high_resolution_clock_frequ": 8, "host": [2, 8, 11], "how": [0, 3], "http": 4, "hz": 6, "i": [2, 5, 6, 10, 11], "id": [6, 11], "identif": 11, "identifi": 11, "ifac": 0, "ignor": [6, 10], "implement": [4, 5, 9], "import": 5, "incom": [6, 10], "index": 11, "info": [0, 1], "inform": [2, 6, 8, 10], "initi": [0, 1], "inspect": 5, "instal": 3, "instanc": [5, 6, 9, 10], "int": [5, 6, 8, 9, 10, 11], "interact": [1, 3, 5], "interfac": [0, 5, 6, 10], "intern": [3, 7], "introduct": 3, "ip4": [6, 10], "ipv4": [6, 10], "is_edit": 11, "is_record": 11, "its": 2, "itself": 2, "jeguzzi": 4, "kei": [6, 10], "kind": [5, 6], "know": 2, "label": 11, "labeled_mark": 11, "labeledmarkerdata": 11, "lambda": [6, 10], "languag": 5, "last": [6, 10], "later": [6, 10], "least": 1, "leav": [6, 10], "legaci": 11, "length": [0, 6, 10, 11], "let": [1, 2], "level": 0, "librari": 5, "life": 5, "limit": 2, "list": [0, 1, 9, 11], "listen": [2, 6, 10], "live": 11, "lo": 11, "local": 0, "locat": 11, "log": [0, 6, 10], "log_level": [0, 1], "logger": [6, 10], "low": 11, "m": 11, "mai": [2, 6, 10], "major": [6, 8, 9], "mani": 0, "manufactur": 11, "map": 0, "marker": 11, "marker_set": 11, "markersdata": 11, "markersetdata": 11, "markersetdescript": 11, "matrix": 11, "matrix12x12": [7, 11], "matrix3x4": [7, 11], "maxim": [6, 10], "maximal_numb": [6, 10], "mean": 11, "measur": 11, "member": 11, "messag": [2, 5, 6, 8, 10], "metadata": 11, "meter": 11, "min_rtt": 0, "minor": [6, 8, 9], "mm": 11, "mocap": [0, 2, 6, 7, 9, 10], "mocapdata": [5, 6, 10, 11], "mocapdescript": [6, 10, 11], "mock": 9, "mode": 11, "model": 11, "modelfil": 11, "more": 2, "moreov": 5, "motiv": [1, 2, 5, 6, 10, 11], "msg": [5, 6, 10], "multicast": [2, 6, 8, 9, 10], "multicast_address": [6, 8, 10], "multipl": 2, "my_callback": 5, "my_nam": 5, "n": [0, 6, 10], "name": [5, 6, 8, 11], "nanosecond": [6, 10], "nat_net_stream_version_serv": 8, "natnet": [0, 1, 2, 4, 5, 6, 8, 9, 10], "natnet_cli": [0, 1], "natnet_discov": 0, "natnet_gui": 0, "natnet_pi": [2, 4, 5, 6, 8, 9, 10, 11], "natnet_vers": 9, "need": [2, 4], "network": [0, 2, 6, 10], "new": [6, 9], "no_sync": 0, "node": 5, "none": [5, 6, 8, 10, 11], "now": [6, 10], "number": [0, 6, 8, 10, 11], "numpi": 4, "occlud": 11, "offer": 5, "offici": [2, 5], "offset": 11, "onc": [2, 6, 10], "one": [0, 1, 2, 11], "onli": [6, 9, 10, 11], "open": 0, "optitrack": [2, 5, 11], "order": 11, "orient": 11, "other": 5, "otherwis": [6, 10, 11], "overview": 2, "overwrit": 9, "packag": [0, 4, 5], "param": 11, "paramet": [5, 6, 9, 10, 11], "parent": 11, "parent_id": 11, "part": 11, "partial": 9, "passiv": 11, "per": 8, "perform": [6, 10], "physic": 11, "pip": 4, "plate": 11, "plate_typ": 11, "pleas": 2, "pointcloud": 11, "pointcloudsolv": 11, "port": [1, 2, 6, 8, 10], "pose": [0, 2, 5], "posit": 11, "possibli": 2, "primari": 5, "print": [6, 10], "prior": 11, "program": 5, "properti": [6, 8, 9, 10, 11], "protocol": [2, 5, 6, 8, 10, 11], "provid": [0, 5], "pure": [4, 5], "py": [1, 4], "python": [1, 2, 4, 5], "python3": 1, "python_natnet": [0, 5], "quaternion": [4, 7, 11], "queryperformancecount": 11, "queue": [0, 6, 10], "quit": [0, 1], "rai": 11, "rang": 5, "rate": [6, 9], "raw": 11, "rb0": [0, 1], "rb1": 0, "rbmarker": 11, "reachabl": [2, 6, 10], "read": [5, 6, 10, 11], "receiv": [2, 5, 6, 8, 10], "received_stamp": 8, "record": 11, "refer": [2, 3, 11], "rel": 11, "releas": 5, "repo": 4, "request": [2, 6, 7, 10], "request_stamp": 8, "requir": [6, 10, 11], "residu": 11, "resolut": [8, 11], "return": [6, 10], "revers": 5, "revis": 8, "right": 2, "rigid": [0, 1, 2, 5, 6, 11], "rigid_bodi": 11, "rigid_bodies_nam": [6, 10], "rigidbodi": [6, 11], "rigidbodydata": [9, 11], "rigidbodydescript": [9, 11], "rigidbodymarkerdata": 11, "root": [6, 10], "rootlogg": [6, 10], "run": [1, 5, 9], "same": 2, "script": 0, "second": [0, 8], "select": 4, "send": [2, 6, 8, 10], "sent": [2, 8], "serial_numb": 11, "server": [0, 1, 2, 3, 5, 6, 7, 8, 10], "server_address": [5, 6, 10], "server_info": [6, 10], "server_ticks_to_client_ns_tim": [2, 6, 10], "server_vers": 8, "serverinfo": [6, 8, 10], "servic": [6, 10], "set": [2, 5, 6, 10, 11], "set_framer": [5, 6], "set_properti": 5, "set_vers": 6, "setup": [1, 4], "sever": 4, "shape": 11, "share": 5, "shell": 3, "short": 2, "signal": 11, "sinc": [6, 10, 11], "size": 11, "skeleton": 11, "skeletondata": 11, "skeletondescript": 11, "smpte": 11, "so": 2, "socket": [0, 1, 2, 5], "softwar": 11, "solv": 11, "some": [5, 6, 10], "spec": 11, "specif": 2, "specifi": [2, 11], "sphinx": [], "src": 4, "srv": 9, "stamp": [1, 2, 6, 8, 10], "stamp_camera_mid_exposur": 11, "stamp_data_receiv": 11, "stamp_n": [1, 5], "stamp_transmit": 11, "start": [0, 1, 6, 10, 11], "start_listening_for_data": [5, 6, 10], "state": 11, "step": 3, "still": [6, 10], "str": [6, 8, 9, 10, 11], "stream": [0, 3, 6, 8, 10, 11], "sub": 11, "subscrib": [6, 10], "subscribe_al": 6, "success": [6, 10], "suffix_data": 11, "suppli": 11, "support": 2, "sync": [0, 1, 2, 6, 10], "syncclient": [2, 5, 7, 10], "synchron": [0, 2, 3, 5, 6, 7, 8], "system": 11, "tabl": 0, "test": [1, 9], "themselv": [6, 10], "thi": [0, 2, 4, 5, 6, 10, 11], "through": 2, "tick": [2, 6, 8, 10, 11], "time": [2, 6, 10, 11], "time_n": [6, 10], "timecod": 11, "timecode_sub": 11, "timeout": [0, 6, 10], "timestamp": [8, 11], "togeth": 5, "too": 4, "top": 11, "topic": [0, 1], "track": [1, 2, 5, 11], "tracked_models_chang": 11, "tracking_valid": 11, "trigger": [6, 10], "true": [1, 2, 6, 10], "try": [6, 10], "tupl": [6, 8, 9, 10, 11], "two": 0, "type": [0, 1, 3, 6, 7, 10], "typic": 5, "udp": [2, 5], "unconnect": [1, 6, 10], "unicast": [0, 1, 2], "uniqu": 11, "unlabel": 11, "unlabeled_markers_posit": 11, "unsubscrib": 6, "until": [6, 10], "up": [5, 9], "updat": [0, 2, 5, 6, 10, 11], "update_descript": 6, "upon": [6, 10], "us": [0, 2, 4, 5, 6, 8, 9, 10, 11], "usag": [0, 6, 9, 10], "use_multicast": [6, 10], "v": 11, "valu": [5, 8, 11], "vector3": [7, 11], "veri": 0, "version": [0, 2, 6, 7, 8, 9, 10, 11], "version_1": 8, "via": 5, "voltag": 11, "w": 11, "wa": [6, 8], "wai": 4, "wait": [6, 10], "warn": [0, 1, 6, 10], "we": [2, 6, 10], "web": [0, 4], "websocket": 4, "when": [0, 2, 8], "where": [0, 5, 6, 10], "whether": [6, 8, 9, 10, 11], "which": [5, 6, 10], "while": 5, "width": 11, "without": 4, "work": 3, "workspac": 4, "world": 11, "x": 11, "xxx": 1, "y": 11, "you": [2, 4, 5], "your": 4, "z": 11}, "titles": ["Executables", "First steps", "How it works", "natnet_py documentation", "Installation", "Introduction", "Asynchronous (asyncio) Client", "API Reference", "Internal API", "Server", "Synchronous (Blocking) Client", "Types"], "titleterms": {"api": [7, 8], "argument": 0, "asynchron": 6, "asyncio": 6, "block": 10, "client": [6, 10], "clock": 2, "connect": [2, 8], "content": [3, 7], "data": 11, "descript": 11, "discov": 0, "discoveri": [2, 8], "document": 3, "echo": 8, "exampl": 0, "execut": 0, "first": 1, "gui": 0, "how": 2, "instal": 4, "interact": 0, "intern": 8, "introduct": 5, "mocap": 11, "name": 0, "natnet_pi": 3, "refer": 7, "request": 8, "respons": 8, "server": 9, "shell": 0, "step": 1, "stream": 2, "synchron": 10, "type": 11, "work": 2}})