#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Created on Tue Aug 25 04:15:00 2020

# @author: radhakrishna
# """

# from keras import backend as K
# K.tensorflow_backend._get_available_gpus()


import tensorflow as tf
import keras


print(f"Tensorflow Version : {tf.__version__}")
print(f"Keras Version : {keras.__version__}")
from tensorflow.python.client import device_lib
print('-----------------------LOCAL DEVICES START---------------------------------')
print(device_lib.list_local_devices())
print('-----------------------LOCAL DEVICES END---------------------------------')
from keras.models import Model,Sequential
from keras.layers import Dense, Activation,Conv2D,MaxPooling2D,Flatten,Dropout,Conv2DTranspose
from keras.layers import concatenate,BatchNormalization,Input
from loader import image_generator,valid_generator
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau

def conv2d_block(input_tensor, n_filters, kernel_size = 3, batchnorm = True):
    """Function to add 2 convolutional layers with the parameters passed to it"""
    # first layer
    x = Conv2D(filters = n_filters, kernel_size = (kernel_size, kernel_size),\
              kernel_initializer = 'he_normal', padding = 'same')(input_tensor)
    if batchnorm:
        x = BatchNormalization()(x)
    x = Activation('relu')(x)
    
    # second layer
    x = Conv2D(filters = n_filters, kernel_size = (kernel_size, kernel_size),\
              kernel_initializer = 'he_normal', padding = 'same')(x)
    if batchnorm:
        x = BatchNormalization()(x)
    x = Activation('relu')(x)
    
    return x


def get_unet(input_img, n_filters = 32, dropout = 0.05, batchnorm = True):
    # Contracting Path
    c1 = conv2d_block(input_img, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)
    p1 = MaxPooling2D((2, 2))(c1)
    p1 = Dropout(dropout)(p1)
    
    c2 = conv2d_block(p1, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)
    p2 = MaxPooling2D((2, 2))(c2)
    p2 = Dropout(dropout)(p2)
    
    c3 = conv2d_block(p2, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)
    p3 = MaxPooling2D((2, 2))(c3)
    p3 = Dropout(dropout)(p3)
    
    c4 = conv2d_block(p3, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)
    p4 = MaxPooling2D((2, 2))(c4)
    p4 = Dropout(dropout)(p4)
    
    c5 = conv2d_block(p4, n_filters = n_filters * 16, kernel_size = 3, batchnorm = batchnorm)
    
    # Expansive Path
    u6 = Conv2DTranspose(n_filters * 8, (3, 3), strides = (2, 2), padding = 'same')(c5)
    u6 = concatenate([u6, c4])
    u6 = Dropout(dropout)(u6)
    c6 = conv2d_block(u6, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)
    
    u7 = Conv2DTranspose(n_filters * 4, (3, 3), strides = (2, 2), padding = 'same')(c6)
    u7 = concatenate([u7, c3])
    u7 = Dropout(dropout)(u7)
    c7 = conv2d_block(u7, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)
    
    u8 = Conv2DTranspose(n_filters * 2, (3, 3), strides = (2, 2), padding = 'same')(c7)
    u8 = concatenate([u8, c2])
    u8 = Dropout(dropout)(u8)
    c8 = conv2d_block(u8, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)
    
    u9 = Conv2DTranspose(n_filters * 1, (3, 3), strides = (2, 2), padding = 'same')(c8)
    u9 = concatenate([u9, c1])
    u9 = Dropout(dropout)(u9)
    c9 = conv2d_block(u9, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)
    
    outputs = Conv2D(1, (1, 1), activation='sigmoid')(c9)
    model = Model(inputs=[input_img], outputs=[outputs])
    return model

#-----------------------  MODEL DEFINITION ------------------------
model=Sequential()
inputShape = (384, 384, 4)
in1 = Input(shape=inputShape)
model=get_unet(in1)
# losses = {'seg': 'binary_crossentropy'}
# metrics = {'seg': ['acc']}
optimizer = keras.optimizers.Adam(lr=0.000025)
model.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])

#------------------------------------------------------------------



model_name = "models/"+"Unet_black_background.h5"


modelcheckpoint = ModelCheckpoint(model_name, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')

lr_callback = ReduceLROnPlateau(min_lr=0.000001)

callback_list = [modelcheckpoint, lr_callback]

history = model.fit_generator(
    image_generator(batch_size=16),
    validation_data = valid_generator(batch_size=32),
    validation_steps = 100,
    steps_per_epoch=100,
    epochs=1000,
    verbose=1, 
    shuffle=True,
    callbacks = callback_list,
)
# model.fit_generator(generator=image_generator,
#  validation_data=valid_generator,
#  use_multiprocessing=True,
#  workers=6)