#!/usr/bin/env python
import numpy
import rospy
import mavros
from geometry_msgs.msg import PoseStamped,Vector3
from mavros_msgs.msg import State,AttitudeTarget
from mavros_msgs.srv import CommandBool, SetMode

from std_msgs.msg import Bool,Float32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
import tf.transformations
import sys, time
import PID

import timeit

from argparse import ArgumentParser

from pyquaternion import Quaternion

import roslaunch
class test:
    def __init__(self):
	print('start')
        self.vicon_cb_flag = False
        self.state_cb_flag = False

        self.P = rospy.get_param('/attitude_thrust_controller/height_hover_P')
        self.I = rospy.get_param('/attitude_thrust_controller/height_hover_I')
        self.D = rospy.get_param('/attitude_thrust_controller/height_hover_D')
        self.height_pid = PID.PID(self.P, self.I, self.D)
        self.height_pid.setSampleTime(0.01)

        #Rate init
        #DECIDE ON PUBLISHING RATE
        self.rate = rospy.Rate(20.0) # MUST be more then 2Hz
        
        self.height_target_pub = rospy.Publisher("/attitude_thrust_controller/thrust_sp", PoseStamped, queue_size=10)

        #ADD SUBSCRIBER FOR VICON DATA
        vicon_sub = rospy.Subscriber("/intel_aero_quad/odom", Odometry, self.vicon_sub_callback)

        state_sub = rospy.Subscriber("/mavros/state", State, self.state_subscriber_callback)

        
        while not rospy.is_shutdown():
	    print('inside')
            if(self.vicon_cb_flag==True and self.state_cb_flag==True):
                #Update PID
                self.P = rospy.get_param('/attitude_thrust_controller/height_hover_P')
                self.I = rospy.get_param('/attitude_thrust_controller/height_hover_I')
                self.D = rospy.get_param('/attitude_thrust_controller/height_hover_D')
                self.height_pid.setKp(self.P)
                self.height_pid.setKi(self.I)
                self.height_pid.setKd(self.D)
                #Update setpoint
                self.height_sp = rospy.get_param('/attitude_thrust_controller/height_sp')
                self.height_pid.SetPoint = self.height_sp
                if(self.current_state=='OFFBOARD'):
                    self.height_pid.update(self.vicon_height)
                else:
                    self.height_pid.clear()
		
                #For this to work, we have to align x,y of quad and vicon
                thrust_output = self.height_pid.output
                target_thrust = PoseStamped()
                target_thrust.header.frame_id = "home"
                target_thrust.header.stamp = rospy.Time.now()
                target_thrust.pose.position.x = thrust_output

                self.height_target_pub.publish(target_thrust)

            self.rate.sleep()

    def vicon_sub_callback(self,state):
        self.vicon_height = state.pose.pose.position.z
        self.vicon_cb_flag = True

    #Current state subscriber
    def state_subscriber_callback(self,state):
        self.current_state = state.mode
        self.state_cb_flag = True

        self.rate.sleep()
def main(args):
    rospy.init_node('offb_node', anonymous=True)
    ic=test()

    try:
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

if __name__ == '__main__':
    main(sys.argv)
