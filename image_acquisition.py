# -*- coding: utf-8 -*-
"""
Created on Aug 2024

@author: Teledyne E2V
"""
from sensor import *
from utils import *

from PIL import Image

# USER PARAMETERS
from sensor import Topaz

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
    camera = Topaz()

    if camera is not None:

        # Global subsampling management
        SUBSAMPLING = 0  # 0=Full 1x1 image, 1=Subsampling both axis
        print("Subsampling = ", str(SUBSAMPLING))

        # print("\r\t" + str(NBImageAcquired) + "/" + str(NIMAGES) + " images acquired", end="\t\t\t")

        # Vertical subsampling: activation in sensor
        if SUBSAMPLING == 0:
            camera.enable_vertical_subsampling(enable=0)  # Vertical subsampling disable
        else:
            camera.enable_vertical_subsampling(enable=1)  # Vertical subsampling enable

        # Exposure time
        camera.exposure_time = EXPOSURE_TIME
        # Pixel format and acquisition image size
        if camera.pixel_format == "RGB24":
            # camera.white_balance(red=R_GAIN, green=G_GAIN, blue=B_GAIN)
            camera.enable_white_balance(enable=1)
            shape = (NIMAGES, camera.sensor_height, camera.sensor_width * 3)
        else:
            shape = (NIMAGES, camera.sensor_height, camera.sensor_width)
        
        im = np.zeros(shape, dtype=xml_pixel_format_nptypes[camera.pixel_format])

        # Get current setting
        print_info(camera)

        # Start acquisition for white balance
        camera.start_acquisition()
        # Do white balance
        if camera.pixel_format == "RGB24":
            camera.do_white_balance(enable=1)
            camera.do_white_balance(enable=0)
        from time import sleep
        sleep(0.05)
        # Terminate acquisition
        camera.stop_acquisition()

        # Image acquisition
        print("\nImage acquisition:")
        if camera.start_acquisition() == 0:
            NBImageAcquired = 0

            # Do white balance
            if camera.pixel_format == "RGB24":
                camera.do_white_balance(enable=1)
                camera.do_white_balance(enable=0)

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

                    if SUBSAMPLING == 0:
                        # Horizontal subsampling: activation during image processing
                        image = image_rearange(im[i, :, :], camera.pixel_format)  # Horizontal subsampling disable
                        # img = Image.fromarray(image, 'RGB')
                        img = Image.fromarray(image, )    
                        img.save('FullResImage.png')
                    else:
                        # Horizontal subsampling: activation during image processing
                        image = image_rearange_subsampling22(im[i, :, :], camera.pixel_format)  # Horizontal subsampling enable
                        # img = Image.fromarray(image, 'RGB')
                        img = Image.fromarray(image,) 
                        img.save('SubsampledImage.png')

                    """
                    Insert your processing code here
                    image is the current image acquired
                    """

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
