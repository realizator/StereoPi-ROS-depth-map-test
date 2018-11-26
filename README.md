# StereoPi-ROS-depth-map-test

To run this test you need stereoscopic setup with Raspberry Pi Compute Module.

You can use StereoPi board or Raspberry Pi CM3 devboard with 2 Pi cameras.

Tests was performed on Ubiquiti Robotics image https://downloads.ubiquityrobotics.com/pi.html

How to use:

1. Put all files in home folder 

2. Run Wezzoid's publisher:

`python wezzoid_publish_nodes.py`

3. Run stereoscopic processing:

`ROS_NAMESPACE=stereo rosrun stereo_image_proc stereo_ige_proc`

4. To visualize results run:

`rosrun image_view stereo_view stereo:=/stereo image:=image_rect_color`

5. For adjusting depth map settings in a real time run:

`rosrun rqt_reconfigure rqt_reconfigure` 