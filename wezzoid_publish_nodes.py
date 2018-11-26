#!/usr/bin/env python

# picamera stereo ROS node using dual CSI Pi CS3 board
# Wes Freeman 2018
# modified from code by Adrian Rosebrock, pyimagesearch.com
# and jensenb, https://gist.github.com/jensenb/7303362

from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import rospy
from sensor_msgs.msg import CameraInfo, Image
import yaml
import io
import signal # for ctrl-C handling
import sys


def parse_calibration_yaml(calib_file):
    with file(calib_file, 'r') as f:
        params = yaml.load(f)

    cam_info = CameraInfo()
    cam_info.height = params['image_height']
    cam_info.width = params['image_width']
    cam_info.distortion_model = params['distortion_model']
    cam_info.K = params['camera_matrix']['data']
    cam_info.D = params['distortion_coefficients']['data']
    cam_info.R = params['rectification_matrix']['data']
    cam_info.P = params['projection_matrix']['data']

    return cam_info


# cam resolution
res_x = 320 #320 # per camera
res_y = 240 #240 
target_FPS = 15

# initialize the camera
print "Init camera..."
camera = PiCamera(stereo_mode = 'top-bottom',stereo_decimate=False)
camera.resolution = (res_x, res_y*2) # top-bottom stereo
camera.framerate = target_FPS
# using several camera options can cause instability, hangs after a while
camera.exposure_mode = 'antishake'
#camera.video_stabilization = True # fussy about res?

stream = io.BytesIO()
 
# ----------------------------------------------------------
#setup the publishers
print "init publishers"
# queue_size should be roughly equal to FPS or that causes lag?
left_img_pub = rospy.Publisher('stereo/right/image_raw', Image, queue_size=1)
right_img_pub = rospy.Publisher('stereo/left/image_raw', Image, queue_size=1)

left_cam_pub = rospy.Publisher('stereo/right/camera_info', CameraInfo, queue_size=1)
right_cam_pub = rospy.Publisher('stereo/left/camera_info', CameraInfo, queue_size=1)

rospy.init_node('stereo_pub')

# init messages
left_img_msg = Image()
left_img_msg.height = res_y
left_img_msg.width = res_x
left_img_msg.step = res_x*3 # bytes per row: pixels * channels * bytes per channel (1 normally)
left_img_msg.encoding = 'rgb8'
left_img_msg.header.frame_id = 'stereo_camera' # TF frame

right_img_msg = Image()
right_img_msg.height = res_y
right_img_msg.width = res_x
right_img_msg.step = res_x*3
right_img_msg.encoding = 'rgb8'
right_img_msg.header.frame_id = 'stereo_camera'

imageBytes = res_x*res_y*3

# parse the left and right camera calibration yaml files
left_cam_info = parse_calibration_yaml('/home/ubuntu/left.yaml')
right_cam_info = parse_calibration_yaml('/home/ubuntu/right.yaml')

# ---------------------------------------------------------------
# this is supposed to shut down gracefully on CTRL-C but doesn't quite work:
def signal_handler(signal, frame):
    print 'CTRL-C caught'
    print 'closing camera'
    camera.close()
    time.sleep(1)
    print 'camera closed'    
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#-----------------------------------------------------------

print "Setup done, entering main loop"
framecount=0
frametimer=time.time()
toggle = True
# capture frames from the camera
for frame in camera.capture_continuous(stream, format="rgb", use_video_port=True):
    framecount +=1
    
    stamp = rospy.Time.now()
    left_img_msg.header.stamp = stamp
    right_img_msg.header.stamp = stamp
    left_cam_info.header.stamp = stamp
    right_cam_info.header.stamp = stamp    
    
    left_cam_pub.publish(left_cam_info)
    right_cam_pub.publish(right_cam_info)    
    
    frameBytes = stream.getvalue()    
    left_img_msg.data = frameBytes[:imageBytes]
    right_img_msg.data = frameBytes[imageBytes:]      

    #publish the image pair
    left_img_pub.publish(left_img_msg)
    right_img_pub.publish(right_img_msg)
    
    # console info
    if time.time() > frametimer +1.0:
        if toggle: 
            indicator = '  o' # just so it's obviously alive if values aren't changing
        else:
            indicator = '  -'
        toggle = not toggle        
        print 'approx publish rate:', framecount, 'target FPS:', target_FPS, indicator
        frametimer=time.time()
        framecount=0
        
    # clear the stream ready for next frame
    stream.truncate(0)
    stream.seek(0)