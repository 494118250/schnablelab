import numpy as np
import cv2
import os
from sys import argv

def main(hyp_dir):
    feature_vector_list = load_3d_image_matrix(hyp_dir)
    print("{} pixel vectors extracted".format(feature_vector_list[0]))
    return feature_vector_list


def load_3d_image_matrix(hyp_dir):
    '''
    Args:
        hyp_dir: string
            filepath of hyperspectral image data
    Returns:
        img_names: 1d array
            File names corresponding to each layer in the img_stack
        img_stack: 3d array
            x,y dims correspond to pixel coordinates for each image
            z dim corresponds to hyperspectral image wavelength.
    '''

    # constant
    discard_imgs = ['0_0_0.png', '1_0_0.png']

    # get dir list
    fname_list = [fname for fname in os.listdir(hyp_dir) if fname not in discard_imgs and fname.endswith('.png')]
    num_images = len(fname_list)

    # constants
    img_dims = (561, 320, num_images)

    # initialize image stack
    img_stack = np.empty(img_dims, dtype=np.dtype('uint8'))

    for i, fname in enumerate(fname_list):

        temp_img_obj = cv2.imread(os.path.join(hyp_dir, fname), cv2.IMREAD_GRAYSCALE)
        # temp_img_obj = cv2.bitwise_not(temp_img_obj)
        img_stack[:,:,i] = temp_img_obj

    return np.reshape(img_stack.shape[0] * img_stack.shape[1], img_stack.shape[2])


if __name__=='__main__':
    main(argv[1])
