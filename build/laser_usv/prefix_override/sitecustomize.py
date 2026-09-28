import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/duda/ros2_ws/src/LASER_PIBIC/install/laser_usv'
