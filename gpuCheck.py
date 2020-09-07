#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 02:46:24 2020
@author: radhakrishna
"""

# GPU TEST FOR PYTHON - TENSORFLOW 


import tensorflow as tf 

if tf.test.gpu_device_name(): 
    print(f'Default GPU Device:{tf.test.gpu_device_name()}')
else:
   print("This Workstation does not appear to have a valid GPU ")