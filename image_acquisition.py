# -*- coding: utf-8 -*-
"""
Created on Aug 2024

@author: Teledyne E2V
"""
from sensor import *
from utils import *
from time import sleep
from PIL import Image

# USER PARAMETERS
from sensor import OnyxMax

NIMAGES = 1  # Number of images to be acquired
INTERVAL_PLOT = 0.0001  # Refresh rate in ms
EXPOSURE_TIME = 20  # Integration time in ms

# Specific init config for range gating
init_config = [
    [0x04,0x21C2],
    [0x05,0x1F62],
    [0x58,0x06E4],
    [0x64,0x3069],
    [0x65,0x0011],
    [0x66,0x007A],
    [0x67,0x0022],
    [0x68,0x0030],
    [0x70,0x0B0A],
]


#  SIMPLE OBJECT CREATION AND IMAGE ACQUISITION
if __name__ == "__main__":
    print("*******************************************************************")
    print("*********** Running Eval Kit image acquisition main loop **********")
    print("*******************************************************************")

    # Open connection
    camera = OnyxMax()

    if camera is not None:

        addr=0x7F
        rval=camera.read_sensor_reg(addr) #Read chipID
        print("RD 0x{:02x} = 0x{:04x}".format(addr, rval))

        # print("\r\t" + str(NBImageAcquired) + "/" + str(NIMAGES) + " images acquired", end="\t\t\t")
        #camera.load_config("RS-8b")
        #camera.load_config("RS-10b")
        #camera.load_config("RS-12b")
        camera.load_config("GS-10b")
        sleep(0.5)

        # Load specific init config
        for i in init_config:
            addr=i[0]
            val=i[1]
            error = camera.write_sensor_reg(address=addr, value=val)
            print("WR 0x{:02x} = 0x{:04x}".format(addr, val))
            sleep(0.1)

        # Set VBS to 0V
        camera.write_vbs_dac(0)

        # Exposure time
        camera.exposure_time = EXPOSURE_TIME

        # Pixel format and acquisition image size
        if camera.pixel_format == "RGB24":
            shape = (NIMAGES, camera.sensor_height, camera.sensor_width * 3)
        else:
            shape = (NIMAGES, camera.sensor_height, camera.sensor_width)
        
        im = np.zeros(shape, dtype=xml_pixel_format_nptypes[camera.pixel_format])

        # Get current setting
        print_info(camera)

        # Image acquisition
        print("\nImage acquisition:")
        if camera.start_acquisition() == 0:
            NBImageAcquired = 0

            for i in range(0, NIMAGES):
                # Get image from internal buffer
                im[i, :, :] = camera.get_image()[1]
                NBImageAcquired += 1
                print("\r\t" + str(NBImageAcquired) + "/" + str(NIMAGES) + " images acquired", end="\t\t\t")
            print("")

            # Terminate acquisition and image processing
            if camera.stop_acquisition() == 0:
                NBImageAcquired = 0
                fig = init_figure(camera)

                for i in range(0, NIMAGES):
                    NBImageAcquired += 1

                    """
                    Insert your processing code here
                    image is the current image acquired
                    """

                    image = image_rearange(im[i, :, :], camera.pixel_format)
                    imageProfile(image)
                    update_figure(fig, image, INTERVAL_PLOT, NBImageAcquired)

                    # Convert to PIL object
                    # img = Image.fromarray(image, 'RGB')
                    img = Image.fromarray(image, )
                    imgName = "EK-image_" + str(NBImageAcquired) + ".tiff"
                    img.save(imgName)
                    print("\r\t" + str(NBImageAcquired) + "/" + str(NIMAGES) + " images processed", end="\t\t\t")

                    # This method will show image in any image viewer
                    img.show()

            # Terminate connection
            camera.close()

        else:
            raise Exception("Image acquisition error. Please reboot the camera")
    else:
        raise Exception("Camera initialization error. Please reboot the camera")
