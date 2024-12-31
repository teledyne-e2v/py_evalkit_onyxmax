import os
import ctypes
import numpy as np
import matplotlib.pyplot as plt


# used to convert from the EK/XML pixel format to colormap
xml_pixel_format_cmap = {
    "Unknown": "gray",  # Unknown or YUV422
    "Mono8": "gray",  # Mono8
    "Mono10": "gray",  # Mono10
    "Mono12": "gray",  # Mono12
    "Mono14": "gray",  # Mono14
    "Mono16": "gray",  # Mono16
    "RGB24": "hsv",  # RGB24
    "YUV444": "hsv",  # YUV444
    "Mono10p": "gray",  # Mono10p
}

# used to convert from the EK/XML pixel format to numpy
xml_pixel_format_nptypes = {
    "Unknown": np.uint8,  # Unknown or YUV422
    "Mono8": np.uint8,  # Mono8
    "Mono10": np.uint16,  # Mono10
    "Mono12": np.uint16,  # Mono12
    "Mono14": np.uint16,  # Mono14
    "Mono16": np.uint16,  # Mono16
    "RGB24": np.uint8,  # RGB24
    "YUV444": np.uint16,  # YUV444
    "Mono10p": np.uint16,  # Mono10p
}


def image_rearange(aux, pixel_format):
    if pixel_format == "RGB24":  # RGB
        # RGB24 is (5760 x 1080) uint8 array R-G-B
        red = aux[:, 0::3].copy()
        green = aux[:, 1::3].copy()
        blue = aux[:, 2::3].copy()
        image = np.stack((red, green, blue), axis=2)
    else:  # Mono
        image = aux[:, :].copy()
    return image


def image_rearange_subsampling22(aux, pixel_format):
    if pixel_format == "RGB24":  # RGB
        # RGB24 is (2880 x 1080) uint8 array R-G-B
        red = aux[:, 0::6].copy()
        green = aux[:, 1::6].copy()
        blue = aux[:, 2::6].copy()
        image = np.stack((red, green, blue), axis=2)
    else:  # Mono
        image = aux[:, 0::2].copy()
    return image


def init_figure(ek):
    plt.ion()
    fig = plt.figure(1)
    fig.clf()
    ax = fig.add_subplot(111)
    shape = (ek.sensor_height, ek.sensor_width)
    image = np.zeros(shape, dtype=xml_pixel_format_nptypes[ek.pixel_format])
    fig_handle = ax.imshow(np.flip(image, 0), origin="lower", cmap=xml_pixel_format_cmap[ek.pixel_format])
    fig_handle.autoscale()
    return fig_handle


def update_figure(fig_handle, image, INTERVAL_PLOT, nim):
    fig_handle.set_data(np.flip(image, 0))
    fig_handle.autoscale()
    plt.title("#" + str(nim))
    plt.pause(INTERVAL_PLOT)
    plt.draw()


def make_nd_array(c_pointer, shape, dtype=np.uint16, order="C"):
    """Safely copy an array from a given pointer into a numpy array."""
    # set up access to Python 3 PyMemoryView_FromMemory() function
    PyBUF_READ = 0x200
    buf_from_mem = ctypes.pythonapi.PyMemoryView_FromMemory
    buf_from_mem.restype = ctypes.py_object
    buf_from_mem.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int)
    arr_size = np.prod(shape[:]) * np.dtype(dtype).itemsize
    buffer = buf_from_mem(c_pointer, arr_size, PyBUF_READ)
    arr = np.ndarray(tuple(shape[:]), dtype, buffer, order=order)
    return arr.copy()


def imgWriteOpenCV(dirOut, imgs):
    import cv2 as cv
    import os

    # Create directory if it doesn't exist
    if not (os.path.exists(dirOut)):
        os.mkdir(dirOut)
    # Save images in non-loss quality compresion and 16b
    cv.imwrite(dirOut + "/im_" + str(i) + ".tiff", imgs[i, :, :].copy() << 4)

    return 0


def write_image(dirOut, imgs):
    # Create directory if it doesn't exist
    if not (os.path.exists(dirOut)):
        os.mkdir(dirOut)
    # Save images in non-loss quality compression and 16b
    for i in range(imgs.shape[0]):
        cv.imwrite(dirOut + "/im_" + str(i) + ".tiff", imgs[i, :, :].copy() << 4)
    return 0


def imagesc(im, autoscale=True):
    # Image show
    fig = plt.figure(1)
    aux = im.copy()
    fig.clf()
    plt.imshow(aux, cmap="gray")
    plt.autoscale(enable=autoscale)
    plt.colorbar()
    plt.xlabel("#cols")
    plt.ylabel("#rows")
    plt.title("Lince11M image")


def imageProfile(im):
    # H-V profiles
    fig = plt.figure(2)
    aux = im.copy()
    fig.clf()
    plt.subplot(211)
    plt.plot(np.mean(aux, axis=0))
    plt.grid()
    plt.xlabel("#cols")
    plt.ylabel("Signal level[LSB]")
    plt.title("Vertical profile")
    plt.subplot(212)
    plt.plot(np.mean(aux, axis=1))
    plt.grid()
    plt.xlabel("#rows")
    plt.ylabel("Signal level[LSB]")
    plt.title("Horizontal profile")


def imageHist(im):
    # Histogram
    fig = plt.figure(3)
    aux = im.copy()
    fig.clf()
    plt.hist(aux.ravel(), bins=1024, fc="k", ec="k")
    plt.grid()
    plt.ylabel("Number of pixels")
    plt.xlabel("Signal level[LSB]")
    plt.title("Histogram")

    # Accumulated Histogram
    fig = plt.figure(4)
    aux = im.copy()
    fig.clf()
    plt.hist(aux.ravel(), bins=1024, fc="k", ec="k")
    plt.gca().set_yscale("log")
    plt.grid()
    plt.ylabel("Number of pixels")
    plt.xlabel("Signal level[LSB]")
    plt.title("Accumulated histogram")
