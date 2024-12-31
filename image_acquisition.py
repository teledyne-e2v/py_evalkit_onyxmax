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
EXPOSURE_TIME = 25  # Integration time in ms
R_GAIN = 1.8  # Red color gain
G_GAIN = 1  # Green color gain
B_GAIN = 1.6  # Blue color gain

#  SIMPLE OBJECT CREATION AND IMAGE ACQUISITION
if __name__ == "__main__":
    print("*******************************************************************")
    print("*********** Running Eval Kit image acquisition main loop **********")
    print("*******************************************************************")

    # Open connection
    camera = OnyxMax()

    if camera is not None:

        # print("\r\t" + str(NBImageAcquired) + "/" + str(NIMAGES) + " images acquired", end="\t\t\t")
        #camera.load_config("RS-8b")
        #camera.load_config("RS-10b")
        camera.load_config("RS-12b")
        sleep(0.5)

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
                    # img = Image.fromarray(image, 'RGB')
                    img = Image.fromarray(image, )
                    img.save('EK-image.png')

                    # update_figure(fig, image, INTERVAL_PLOT, NBImageAcquired)
                    print("\r\t" + str(NBImageAcquired) + "/" + str(NIMAGES) + " images processed", end="\t\t\t")

                    # This method will show image in any image viewer
                    img.show()

            # Terminate connection
            camera.close()

        else:
            raise Exception("Image acquisition error. Please reboot the camera")
    else:
        raise Exception("Camera initialization error. Please reboot the camera")
