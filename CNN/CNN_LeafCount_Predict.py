"""
make predictions using trained model based on deep plant phenomics pakcage
"""
import numpy as np
from pathlib import Path
import deepplantphenomics as dpp
import os

class CornLeafRegressor(object):
    model = None
    # TODO: Convert images to 256 or convert these vars to the image dims?
    img_height = 256
    img_width = 256

    def __init__(self, model_dir, batch_size=2):
        """A network which predicts rosette leaf count via a convolutional neural net"""
        
        self.__dir_name = os.path.join(model_dir)
        self.model = dpp.DPPModel(debug=False, load_from_saved=self.__dir_name)
        # Define model hyperparameters
        self.model.set_batch_size(batch_size)
        self.model.set_number_of_threads(1)
        self.model.set_image_dimensions(self.img_height, self.img_width, 3)
        self.model.set_resize_images(True)
        self.model.set_problem_type('regression')
        self.model.set_augmentation_crop(True)
        # Define a model architecture
        self.model.add_input_layer()
        self.model.add_convolutional_layer(filter_dimension=[5, 5, 3, 32], stride_length=1, activation_function='tanh')
        self.model.add_pooling_layer(kernel_size=3, stride_length=2)
        self.model.add_convolutional_layer(filter_dimension=[5, 5, 32, 64], stride_length=1, activation_function='tanh')
        self.model.add_pooling_layer(kernel_size=3, stride_length=2)
        self.model.add_convolutional_layer(filter_dimension=[3, 3, 64, 64], stride_length=1, activation_function='tanh')
        self.model.add_pooling_layer(kernel_size=3, stride_length=2)
        self.model.add_convolutional_layer(filter_dimension=[3, 3, 64, 64], stride_length=1, activation_function='tanh')
        self.model.add_pooling_layer(kernel_size=3, stride_length=2)
        self.model.add_output_layer()

    def forward_pass(self, x):
        y = self.model.forward_pass_with_file_inputs(x)
        return y

    def shut_down(self):
        self.model.shut_down()

def predict(model_dir, test_dir):
    dir = os.path.join(test_dir)
    images = [os.path.join(dir, name) for name in os.listdir(dir) if
          os.path.isfile(os.path.join(dir, name)) & name.endswith('.seg.crp.png')]
    net = CornLeafRegressor(model_dir)
    leaf_counts = net.forward_pass(images)
    net.shut_down()
    for k,v in zip(images, leaf_counts):
        print ('%s: %d' % (k, v))

import sys
if len(sys.argv)==3:
    predict(*sys.argv[1:])
else:
    print('model_dir, testing_dir')
