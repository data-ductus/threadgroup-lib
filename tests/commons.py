import os
import sys

DIR = os.path.dirname(os.path.realpath(__file__))
temp_path = [os.path.dirname(DIR)]
temp_path.extend(sys.path)
sys.path = temp_path

import threadgroup
