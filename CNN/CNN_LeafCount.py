"""
use deep plant phenomics method on leaf counting project
"""
from glob import glob
import numpy as np
import pickle
import deepplantphenomics as dpp
from pathlib import Path


def train(train_dir,  epoch, tensor_flow_dir):
    img_dir = Path(train_dir)
    model = dpp.DPPModel(debug=True, save_checkpoints=True, report_rate=20, tensorboard_dir=tensor_flow_dir)
    model.set_batch_size(30)
    model.set_number_of_threads(90)
    model.set_image_dimensions(256, 256, 3)
    model.set_resize_images(True)
    model.set_problem_type('regression')
    model.set_num_regression_outputs(1)
    model.set_train_test_split(0.8)
    model.set_learning_rate(0.0001)
    model.set_weight_initializer('xavier')
    #model.set_maximum_training_epochs(1)
    model.set_maximum_training_epochs(int(epoch))

    # Augmentation options
    model.set_augmentation_brightness_and_contrast(True)
    model.set_augmentation_flip_horizontal(True)
    model.set_augmentation_flip_vertical(True)
    model.set_augmentation_crop(True)
    
    # Load all data for IPPN leaf counting dataset
# ALTERNATIVELY - Load labels and images
    model.load_multiple_labels_from_csv(img_dir / 'my_labels.csv', id_column=0)
    model.load_images_with_ids_from_directory(img_dir)


    # Define a model architecture
    model.add_input_layer()
    model.add_convolutional_layer(filter_dimension=[5, 5, 3, 32], stride_length=1, activation_function='tanh')

    model.add_pooling_layer(kernel_size=3, stride_length=2)
    model.add_convolutional_layer(filter_dimension=[5, 5, 32, 64], stride_length=1, activation_function='tanh')

    model.add_pooling_layer(kernel_size=3, stride_length=2)
    model.add_convolutional_layer(filter_dimension=[3, 3, 64, 64], stride_length=1, activation_function='tanh')
    model.add_pooling_layer(kernel_size=3, stride_length=2)
    model.add_convolutional_layer(filter_dimension=[3, 3, 64, 64], stride_length=1, activation_function='tanh')
    model.add_pooling_layer(kernel_size=3, stride_length=2)
    model.add_output_layer()
    # Begin training the regression model
    model.begin_training()


import sys
if len(sys.argv)==4:
    train(*sys.argv[1:])
else:
    print('train_dir', 'epoches', 'tensorflow_dir')
