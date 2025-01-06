import time
import struct
from utils import *

CAM_ERR_SUCCESS = 0
NBUFFER = 100

# set up access to Python 3 PyMemoryView_FromMemory() function
PyBUF_READ = 0x200
buf_from_mem = ctypes.pythonapi.PyMemoryView_FromMemory
buf_from_mem.restype = ctypes.py_object
buf_from_mem.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int)


# Define structs C
class tCameraInfo(ctypes.Structure):
    _fields_ = [
        ("vendor", ctypes.c_char * 32),
        ("model", ctypes.c_char * 32),
        ("serial", ctypes.c_char * 64),
        ("pcID", ctypes.c_char * 260),
    ]


class tImagePixelType:
    eUnknown, eMono8, eMono10, eMono12, eMono14, eMono26, eRGB8, eYUV422, eMono10p = range(9)


class tImageInfos(ctypes.Structure):
    _fields_ = [
        ("hBuffer", ctypes.c_void_p),
        ("isNewData", ctypes.c_uint8),
        ("isIncomplete", ctypes.c_uint8),
        ("pDatas", ctypes.c_void_p),
        ("iImageSize", ctypes.c_size_t),
        ("iImageWidth", ctypes.c_size_t),
        ("iImageHeight", ctypes.c_size_t),
        ("eImagePixelType", ctypes.c_int),
        # ("iLinePitch", ctypes.c_size_t),
        ("iBlockId", ctypes.c_ulonglong),
        ("iTimestamp", ctypes.c_ulonglong),
        # ("iNbPacketLost", ctypes.c_ulonglong),
        # ("iNbFrameLost", ctypes.c_ulonglong),
        # ("iNbImageAcquired", ctypes.c_ulonglong),
        ("eBufferType", ctypes.c_int),
        ("iContextualDataSize", ctypes.c_size_t),
    ]


class EvaluationKit:
    """A Python wrapper for the pigentl-sdk library."""

    def __init__(self, dll_path=None, cti_path=None):
        """Constructor
        :param dll_path: Optionally specify the absolute path to the pigentl DLL.
        :param cti_path: Optionally specify the absolute path to the pigentl CTI.
                      is in the directory of the DLL."""
        self._is_init = False
        self.camera_opened = False

        if not os.path.isfile(dll_path):
            raise FileNotFoundError(f"The pigentl-sdk DLL was not found at the following location: {dll_path}")
        if not os.path.isfile(cti_path):
            raise FileNotFoundError(f"The pigentl-sdk CTI was not found at the following location: {cti_path}")
        try:
            ctypes.cdll.LoadLibrary(cti_path)
            libc = ctypes.cdll.LoadLibrary(dll_path)
        except ModuleNotFoundError:
            raise ModuleNotFoundError("The pigentl-sdk DLL, CTI, or one or more of their dependencies were not found.")
        self.lib = self._register_lib_args(libc)

        # Initializate library
        err = self.lib.PiGentlSdkInitializeLibrary()
        if err != CAM_ERR_SUCCESS:
            raise Exception(f"PiGentlSdkInitializeLibrary: {err}. Is the camera already in use?")
        else:
            self._is_init = True
            # update camera list
            ulNbCameras = ctypes.c_ulong(0)
            numattempts = 0
            while ulNbCameras.value == 0 & numattempts < 10:
                err = self.lib.PiGentlSdkUpdateCameraList(ctypes.byref(ulNbCameras))
                numattempts += 1
            if err != CAM_ERR_SUCCESS:
                raise Exception(f"PiGentlSdkUpdateCameraList: {err}")
            else:
                print(str(ulNbCameras.value) + " camera(s) found")
                # Retrieve camera info
                camera_info = tCameraInfo()
                err = self.lib.PiGentlSdkGetCameraInfo(ctypes.c_ulong(0), ctypes.byref(camera_info))
                if err != CAM_ERR_SUCCESS:
                    raise Exception(f"PiGentlSdkGetCameraInfo: {err}")
                else:
                    print("\t\tCamera found: " + camera_info.pcID.decode())
                    self._handle = ctypes.c_void_p()
                    err = self.lib.PiGentlSdkOpenCamera(ctypes.byref(camera_info), self._handle)
                    if err != CAM_ERR_SUCCESS:
                        raise Exception(f"PiGentlSdkOpenCamera: {err}. Is the camera connected? Is it already in use?")
                    else:
                        print("\t\t\t\tPiGentlSdkOpenCamera OK")
                        self.camera_opened = True
                        # Before acquiring an image the height of the image and the number of buffers has to be defined
                        err = self.lib.PiGentlSdkSetNumberOfBuffers(self._handle, ctypes.c_size_t(NBUFFER))
                        if err != CAM_ERR_SUCCESS:
                            raise Exception(f"PiGentlSdkSetNumberOfBuffers: {err}")
                        else:
                            print("\t\t\t\t\t\tBuffers allocation OK")

    def __del__(self):
        self.lib.PiGentlSdkCloseCamera(self._handle)
        self.lib.PiGentlSdkTerminateLibrary()

    @staticmethod
    def _register_lib_args(libc):
        # Define arg types expected
        libc.PiGentlSdkUpdateCameraList.argtypes = [ctypes.POINTER(ctypes.c_ulong)]
        libc.PiGentlSdkGetCameraInfo.argtypes = [ctypes.c_ulong, ctypes.POINTER(tCameraInfo)]
        libc.PiGentlSdkOpenCamera.argtypes = [ctypes.POINTER(tCameraInfo), ctypes.POINTER(ctypes.c_void_p)]
        libc.PiGentlSdkSetNumberOfBuffers.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        libc.PiGentlSdkGetBuffer.argtypes = [ctypes.c_void_p, ctypes.POINTER(tImageInfos), ctypes.c_size_t]
        libc.PiGentlSdkStartAcquisition.argtypes = [ctypes.c_void_p]
        libc.PiGentlSdkRequeueBuffer.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        libc.PiGentlSdkStopAcquisition.argtypes = [ctypes.c_void_p]
        libc.PiGentlSdkFlushBuffers.argtypes = [ctypes.c_void_p]
        libc.PiGentlSdkCloseCamera.argtypes = [ctypes.c_void_p]
        libc.PiGentlSdkReadRegister.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        libc.PiGentlSdkWriteRegister.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        libc.PiGentlSdkGetLastError.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
        libc.PiGentlSdkUpgradeCamera.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_ulong), ctypes.c_char_p]
        return libc

    def read(self, address, size, decode=True):
        """This function reads a camera register at a specified address.
        :param address:     The register address to read.
        :param size: Size of the provided pBuffer and thus the amount of bytes to read from the register.
        :param decode: Optionally decode the buffer.
        returns (error code, decoded buffer of read data)
        NOTE: The buffer endianness is little endian"""
        ulAddress = ctypes.c_ulong(address)
        size = ctypes.c_size_t(size)
        byte_buffer = ctypes.create_string_buffer(size.value)
        err = self.lib.PiGentlSdkReadRegister(self._handle, ulAddress, byte_buffer, ctypes.byref(size))
        if decode:
            data = byte_buffer.raw.decode()
        else:
            data = byte_buffer.raw
        return err, data

    def write(self, address, data):
        """This function writes a camera register at a specified address.
        :param address:     The register address to write.
        :param data:     A user allocated byte buffer to send data.
        returns (error code, size of buffer written)
        NOTE: The buffer endianness is little endian"""
        if type(data) == int:  # integer
            ba = bytearray(struct.pack("<i", data))
        elif type(data) == float:  # float
            ba = bytearray(struct.pack("<f", data))
        elif type(data) == np.uint16:  # unsigned short (16bit)
            ba = bytearray(struct.pack("<H", data))
        else:  # unsigned integer
            ba = bytearray(struct.pack("<I", data))
        ulAddress = ctypes.c_ulong(address)
        char_array = ctypes.c_char * len(ba)
        byte_buffer = char_array.from_buffer(ba)
        size = ctypes.c_size_t(ctypes.sizeof(byte_buffer))
        err = self.lib.PiGentlSdkWriteRegister(self._handle, ulAddress, byte_buffer, ctypes.byref(size))
        return err

    def start_acquisition(self):
        """This function starts the acquisition engine for the specified camera.
        returns error code
        NOTE: Once started, the acquisition engine uses all buffers in the "InputQueue" and when grabbed, moves them to
              the "OutputQueue" where they can be retrieved with getBuffer.
        NOTE: Before starting acquisition the SDK internally calls flushBuffers to restore all buffers from the
              output queue to the input queue"""
        err = self.lib.PiGentlSdkFlushBuffers(self._handle)
        time.sleep(0.1)
        err = self.lib.PiGentlSdkStartAcquisition(self._handle)
        return err

    def stop_acquisition(self):
        """This function stops the acquisition engine for the specified camera.
        NOTE: SDK automatically allocates the size of the memory for each buffer specified by setNumberOfBuffers.
        returns error code"""
        err = self.lib.PiGentlSdkStopAcquisition(self._handle)
        time.sleep(0.1)
        err = self.lib.PiGentlSdkFlushBuffers(self._handle)
        return err

    def get_image(self, timeout=5000):
        """This function get an image from preallocated buffer.
        """
        image = None
        ImageInfos = tImageInfos()
        err = self.lib.PiGentlSdkGetBuffer(self._handle, ctypes.byref(ImageInfos), timeout)
        if err == CAM_ERR_SUCCESS:
            data = ctypes.cast(ImageInfos.pDatas, ctypes.POINTER(ctypes.c_ubyte))
            bytesPerPixel = int((ImageInfos.iImageSize / (ImageInfos.iImageHeight * ImageInfos.iImageWidth)))
            # Get image from byte buffer
            if bytesPerPixel == 3:  # RGB 8bit/Color
                shape = (ImageInfos.iImageHeight, ImageInfos.iImageWidth * bytesPerPixel)
                image = make_nd_array(data, shape, dtype=np.uint8, order="C")
            else:
                if bytesPerPixel == 1: # 8bit
                    shape = (ImageInfos.iImageHeight, ImageInfos.iImageWidth)
                    image = make_nd_array(data, shape, dtype=np.uint8, order="C")
                else: # 16bit
                    shape = (ImageInfos.iImageHeight, ImageInfos.iImageWidth)
                    image = make_nd_array(data, shape, dtype=np.uint16, order="C")
            err = self.lib.PiGentlSdkRequeueBuffer(self._handle, ImageInfos.hBuffer)
            if err != CAM_ERR_SUCCESS:
                raise Exception(f"PiGentlSdkRequeueBuffer: {err}")
        else:
            raise Exception(f"getBuffer: {err}")
        return err, image

    def get_error_text(self, error_code):
        """This function gets the text corresponding to an error.
        :param error_code:  The error.
        returns (error code, the error text)"""
        size = ctypes.c_size_t(512)
        buffer = ctypes.create_string_buffer(size.value)
        err = self.lib.PiGentlSdkGetLastError(ctypes.c_int(error_code), buffer, ctypes.byref(size))
        return err, buffer.raw.decode("latin-1").replace("\x00", "")
