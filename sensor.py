from evaluationkit import *
from time import sleep

DEFAULT_PIGENTL_DIR = "C:/Program Files/Teledyne e2v/pigentl/1.4"
DEFAULT_CTI_NAME = "bin/pigentl.cti"
DEFAULT_DLL_NAME = "bin/pigentl-sdk.dll"

# used to map EK features address from XML file
_xml_bootstrap_nodes_addresses = {
    "DeviceVendorName": 0x0,
    "DeviceModelName": 0x20,
    "DeviceVersion": 0x40,
    "DeviceFirmwareVersion": 0x60,
    "SerialNumber": 0xE0,
    "SensorWidth": 0x1000C,
    "SensorHeight": 0x10010,
    "PixelFormat": 0x10014,
    "LoadConfig": 0x10024,
    "AutoExposure": 0x10300,
    "VbsDac": 0x1060001,
}

# used to map Sensor features address from XML file
_xml_sensor_nodes_addresses = {
    "BaseAddress": 0x30000,
    "ChipID": 0x3007F,
    "ExposureTime": 0x3000C,
    "WaitTime": 0x3000B,
    "LineLength": 0x3003C,
    "AnalogGain": 0x30015,
    "ImageOffset": 0x3002A,
}

# used to get the number of bits per pixel from the EK/XML pixel format
xml_pixel_format_nbits = {
    0x01080001: 8,  # Mono8
    0x010A0046: 10,  # Mono10p
    0x010C0047: 12,  # Mono12p
    0x01100025: 14,  # Mono14
    0x01100007: 16,  # Mono16
    0x02180014: 32,  # RGB24
}

# used to get the pixel type from the EK/XML pixel format
xml_pixel_format_type = {
    0x0: "Unknown",  # Unknown or YUV422
    0x01080001: "Mono8",  # Mono8
    0x010A0046: "Mono10p",
    0x010C0047: "Mono12p",
    0x01100025: "Mono14",
    0x01100007: "Mono16",
    0x02180014: "RGB24",
}

# used to load the configuration from the EK/XML LoadConfig
xml_load_config_type = {
    "RS-8b": 6,
    "RS-10b": 5,
    "RS-12b": 0,
    "RS-14b": 2,
    "RS-HDR-12b": 7,
    "RS-HDR-14b": 1,
    "GS-10b": 4,
    "GS-DDS-12b": 3,
    "User0": 8,
    "User1": 9,
    "User2": 10,
    "User3": 11,
    "User4": 12,
    "User5": 13,
    "User6": 14,
    "User7": 15,
}

onyx_analog_gain = {
    "x0.5": 0x0000,
    "x1": 0x0040,
    "x1.5": 0x0080,
    "x2": 0x00C0,
    "x3": 0x0100,
    "x4": 0x0140,
    "x6": 0x0180,
    "x8": 0x01C0,
}

def print_info(ek):
    print("Camera INFO:")
    print("\tManufacturer info          ", ek.vendor_name)
    print("\tDevice name                ", ek.model_name)
    print("\tSerial number              ", ek.serial_number)
    print("\tDevice firmware version    ", ek.firmware_version)
    print("\tImage width                ", ek.sensor_width)
    print("\tImage height               ", ek.sensor_height)
    print("\tPixel format               ", ek.pixel_format)
    print("\tLine length                 %.2f us" % (ek.line_length * 20e-3))
    print("\tExposure time               %.2f ms" % ek.exposure_time)
    print("\tWait time                   %.2f ms" % ek.wait_time)
    print("\tImage Offset               ", ek.image_offset)

class OnyxMax(EvaluationKit):
    def __init__(self, dll_path=None, cti_path=None):
        self.DEFAULT_PIGENTL_DIR = DEFAULT_PIGENTL_DIR
        self.DEFAULT_CTI_NAME = DEFAULT_CTI_NAME
        self.DEFAULT_DLL_NAME = DEFAULT_DLL_NAME
        if dll_path is None:
            dll_path = os.path.join(os.path.dirname(__file__), self.DEFAULT_PIGENTL_DIR, self.DEFAULT_DLL_NAME)
        if cti_path is None:
            cti_path = os.path.join(os.path.dirname(__file__), self.DEFAULT_PIGENTL_DIR, self.DEFAULT_CTI_NAME)
        super().__init__(dll_path, cti_path)

    def __del__(self):
        super().__del__()

    @property
    def clkref(self):
        return 80  # MHz

    @property
    def model_name(self):
        return self.read(address=_xml_bootstrap_nodes_addresses["DeviceModelName"], size=32)[1]

    @property
    def vendor_name(self):
        return self.read(address=_xml_bootstrap_nodes_addresses["DeviceVendorName"], size=32)[1]

    @property
    def firmware_version(self):
        return self.read(address=_xml_bootstrap_nodes_addresses["DeviceFirmwareVersion"], size=32)[1]

    @property
    def serial_number(self):
        return self.read(address=_xml_bootstrap_nodes_addresses["SerialNumber"], size=16)[1]

    @property
    def pixel_format(self):
        return xml_pixel_format_type[
            int.from_bytes(
                self.read(address=_xml_bootstrap_nodes_addresses["PixelFormat"], size=4, decode=False)[1],
                byteorder="little",
            )
        ]

    @property
    def sensor_width(self):
        return int.from_bytes(
            self.read(address=_xml_bootstrap_nodes_addresses["SensorWidth"], size=4, decode=False)[1],
            byteorder="little",
        )

    @property
    def sensor_height(self):
        return int.from_bytes(
            self.read(address=_xml_bootstrap_nodes_addresses["SensorHeight"], size=4, decode=False)[1],
            byteorder="little",
        )

    @property
    def line_length(self):  # in
        return int.from_bytes(
            self.read(address=_xml_sensor_nodes_addresses["LineLength"], size=2, decode=False)[1], byteorder="little"
        )

    @property
    def wait_time(self):  # in ms
        return (
            int.from_bytes(
                self.read(address=_xml_sensor_nodes_addresses["WaitTime"], size=2, decode=False)[1],
                byteorder="little",
            )
            * (self.line_length / self.clkref)
        ) * 1e-3

    @property
    def exposure_time(self):  # in ms
        return (
            int.from_bytes(
                self.read(address=_xml_sensor_nodes_addresses["ExposureTime"], size=2, decode=False)[1],
                byteorder="little",
            )
            * (self.line_length / self.clkref)
        ) * 1e-3

    @exposure_time.setter
    def exposure_time(self, value):  # in ms
        return self.write(
            address=_xml_sensor_nodes_addresses["ExposureTime"],
            data=np.uint16((value * self.clkref / self.line_length) * 1e3),
        )

    @property
    def image_offset(self):
        return (
            int.from_bytes(
                self.read(address=_xml_sensor_nodes_addresses["ImageOffset"], size=2, decode=False)[1],
                byteorder="little",
            )
        )

    @image_offset.setter
    def image_offset(self, value):
        return self.write(
            address=_xml_sensor_nodes_addresses["ImageOffset"],
            data=np.uint16(value),
        )

    def load_config(self, value):  # in ms
        return self.write(
            address=_xml_bootstrap_nodes_addresses["LoadConfig"],
            data=xml_load_config_type[value],
        )

    def read_sensor_reg(self, address):
        addr=address+_xml_sensor_nodes_addresses["BaseAddress"]
        rval=int.from_bytes(self.read(address=addr, size=2, decode=False)[1], byteorder="little", )
        # print("RD 0x{:05x} = 0x{:04x}".format(addr, rval))
        return rval

    def write_sensor_reg(self, address, value):
        addr=address+_xml_sensor_nodes_addresses["BaseAddress"]
        val = np.uint16(value)
        # print("WR 0x{:05x} = 0x{:04x}".format(addr, val))
        error = self.write(address=addr, data=val)
        return error

    def write_vbs_dac(self, value):
        addr=_xml_bootstrap_nodes_addresses["VbsDac"]
        val = np.uint16(value)
        # print("WR 0x{:05x} = 0x{:04x}".format(addr, val))
        error = self.write(address=addr, data=val)
        return error

    def clamp_mode(self, value):
        addr = 0x0004
        mask = 0xFF3F
        rd = self.read_sensor_reg(addr)
        wr = rd & mask
        shifted = value << 6
        wr = wr + shifted
        error = self.write_sensor_reg(address=addr, value=wr)
        return error

    def load_sensor_config(self, config):
        for i in config:
            addr=i[0]
            val=i[1]
            error = self.write_sensor_reg(address=addr, value=val)
            print("WR 0x{:02x} = 0x{:04x}".format(addr, val))
            sleep(0.1)
        return error

    def enable_thermo(self):
        # @0x03 - reg_dig_power - clk_thermo_en[5]=1
        addr = 0x0003
        value = 0x0020
        mask = 0xFFDF
        rd = self.read_sensor_reg(addr)
        wr = (rd & mask) + value
        error = self.write_sensor_reg(address=addr, value=wr)

        #  @0x05 - reg_dig_config_2 - thermo_en[13]=1
        addr = 0x0005
        value = 0x2000
        mask = 0xDFFF
        rd = self.read_sensor_reg(addr)
        wr = (rd & mask) + value
        error = self.write_sensor_reg(address=addr, value=wr)

        # @0x43 - reg_thermo_ctrl - thermo_selection[2:1] = 2 (counter start control)
        addr = 0x0043
        value = 0x0005
        mask = 0xFFF8
        rd = self.read_sensor_reg(addr)
        wr = (rd & mask) + value
        error = self.write_sensor_reg(address=addr, value=wr)

        # @0x45
        addr = 0x0045
        value = 0x03C3
        error = self.write_sensor_reg(address=addr, value=value)

        # @0x46
        addr = 0x0046
        value = 0x0453
        error = self.write_sensor_reg(address=addr, value=value)

        # @0x4B
        addr = 0x004B
        value = 0x0453
        error = self.write_sensor_reg(address=addr, value=value)

        return error

    def read_thermo(self):
        addr = 0x0052
        mask = 0x03FF
        rd = self.read_sensor_reg(addr)
        value = round(float(((rd & mask) * (125/1024)) - 40),2)
        return value

    def close(self):
        super().__del__()
