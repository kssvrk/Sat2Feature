#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 03:39:04 2020

@author: radhakrishna
"""

#Cloud data generator




import tensorflow as tf
import glob,os
import numpy as np
from pprint import pprint
import gdal


testnir_dir='/appdisk/radhakrishna/95cl/38-Cloud_training/train_nir'
testgreen_dir='/appdisk/radhakrishna/95cl/38-Cloud_training/train_green'
testblue_dir='/appdisk/radhakrishna/95cl/38-Cloud_training/train_blue'
testred_dir='/appdisk/radhakrishna/95cl/38-Cloud_training/train_red'
testout_dir='/appdisk/radhakrishna/95cl/38-Cloud_training/train_gt'




nir_dir='/appdisk/radhakrishna/95cl/95-cloud_training_only_additional_to38-cloud/train_nir'
green_dir='/appdisk/radhakrishna/95cl/95-cloud_training_only_additional_to38-cloud/train_green'
blue_dir='/appdisk/radhakrishna/95cl/95-cloud_training_only_additional_to38-cloud/train_blue'
red_dir='/appdisk/radhakrishna/95cl/95-cloud_training_only_additional_to38-cloud/train_red'
out_dir='/appdisk/radhakrishna/95cl/95-cloud_training_only_additional_to38-cloud/train_gt'

data_dirs=[nir_dir,green_dir,blue_dir,red_dir]


# testnir_dir='/appdisk/radhakrishna/95cl/38-Cloud_test/test_nir'
# testgreen_dir='/appdisk/radhakrishna/95cl/38-Cloud_test/test_green'
# testblue_dir='/appdisk/radhakrishna/95cl/38-Cloud_test/test_blue'
# testred_dir='/appdisk/radhakrishna/95cl/38-Cloud_test/test_red'
# testout_dir='/appdisk/radhakrishna/95cl/38-Cloud_test/test_gt'

testdata_dirs=[testnir_dir,testgreen_dir,testblue_dir,testred_dir]

#https://towardsdatascience.com/writing-custom-keras-generators-fe815d992c5a


def get_input(file_names):
    inputs=[]
    for file_name in file_names:
        data=gdal.Open(file_name).ReadAsArray()
        maxi=data.max()
        mini=data.min()
        if(maxi!=mini):
            data=(data-mini)/(maxi-mini)
        inputs.append(data)
    return np.reshape(np.array(inputs),(384,384,4))

def get_output(file_name):
    data=gdal.Open(file_name).ReadAsArray()
    y = np.expand_dims(data, axis=0)
    return np.reshape(y,(384,384,1))

def preprocess_input(image_path):
    pass
def image_generator(data_dirs=data_dirs, out_dir=out_dir, batch_size = 16):
    
    while True:
          # Select files (paths/indices) for the batch
          label_names=glob.glob(os.path.join(out_dir,'*.TIF'))
          
          batch_paths  = np.random.choice(a    = label_names, 
                                          size = batch_size)
          
          batch_input  = []
          batch_output = [] 
          for path in batch_paths:
              pattern=os.path.basename(path)
              common=pattern[pattern.index('_'):]
              input_paths=[]
              for fol in data_dirs:
                  folpattern=os.path.basename(fol)
                  follabel=folpattern[folpattern.index('_')+1:]
                  filename=follabel+common
                  input_paths.append(os.path.join(fol,filename))
              batch_input.append(get_input(input_paths))
              batch_output.append(get_output(path))
          batch_x = np.array( batch_input )
          batch_y = np.array( batch_output )
        
          yield( batch_x, batch_y )
    
def valid_generator(data_dirs=testdata_dirs, out_dir=testout_dir, batch_size = 16):
    
    while True:
          # Select files (paths/indices) for the batch
          label_names=glob.glob(os.path.join(out_dir,'*.TIF'))
          
          batch_paths  = np.random.choice(a = label_names, 
                                          size = batch_size)
          
          batch_input  = []
          batch_output = [] 
          for path in batch_paths:
              pattern=os.path.basename(path)
              common=pattern[pattern.index('_'):]
              input_paths=[]
              for fol in data_dirs:
                  folpattern=os.path.basename(fol)
                  follabel=folpattern[folpattern.index('_')+1:]
                  filename=follabel+common
                  input_paths.append(os.path.join(fol,filename))
              batch_input.append(get_input(input_paths))
              batch_output.append(get_output(path))
          batch_x = np.array( batch_input )
          batch_y = np.array( batch_output )
        
          yield( batch_x, batch_y )
if(__name__=="__main__"):
    # input_data=get_input()
    # output_data=get_output()
    s=image_generator(data_dirs,out_dir)
    
