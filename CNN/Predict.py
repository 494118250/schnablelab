# 7/16/18
# chenyong 
# prediction

"""
make predictions using trained model
"""
import os
import os.path as op
import sys
import numpy as np
import pickle
import matplotlib.pyplot as plt
import matplotlib as mpl
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob
from JamesLab.apps.header import Slurm_header
from JamesLab.apps.natsort import natsorted

def main():
    actions = (
        ('Pred', 'using trained model to make prediction'),
        ('Plot', 'plot training model history'),
        ('Convert3dImageMatrix', 'convert hyperspectral images under a dir to a numpy array object'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def Convert3dImageMatrix(hyp_dir):
    '''
    %prog hyp_dir(filepath of hyperspectral image data) 
    Returns: numpy array object with shape [x*y, z].
        x,y dims correspond to pixel coordinates for each image
        z dim corresponds to hyperspectral image wavelength.
    '''
    import cv2
    p = OptionParser(Convert3dImageMatrix.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    
    discard_imgs = ['0_0_0.png', '1_0_0.png']
    fname_list = [fname for fname in os.listdir(mydir) if fname not in ['0_0_0.png', '1_0_0.png'] and fname.endswith('.png')]
    num_images = len(fname_list)
    print('%s wavelengths'%num_images)
    img_dims = (561, 320, num_images)
    # initialize image stack
    img_stack = np.empty(img_dims, dtype=np.dtype('uint8'))
    for i, fname in enumerate(fname_list):
        temp_img_obj = cv2.imread(op.join(mydir, fname), cv2.IMREAD_GRAYSCALE)
        img_stack[:,:,i] = temp_img_obj
    npj = np.reshape(img_stack.shape[0] * img_stack.shape[1], img_stack.shape[2])
    np.save('%s.npy'%mydir)


def Pred(args):
    """
    %prog model_name predict_data
    using your trained model to make predictions.
    The pred_data is a numpy array object which has the same number of columns as the training data.
    """
    from keras.models import load_model
    p = OptionParser(Pred.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    model, pred_data, = args

    my_model = load_model(model)
    pre_prob = my_model.predict(pred_data)
    predictions = pre_prob.argmax(axis=1)


def Plot(args): 
    """
    %prog dir
    plot training process
    You can load the dict back using pickle.load(open('*.p', 'rb'))
    """

    p = OptionParser(Plot.__doc__)
    p.add_option("--pattern", default="History_*.p",
                 help="specify the patter of your pickle object file, remember to add quotes [default: %default]")
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    mydir, = args
    pickles = glob('%s/%s'%(mydir, opts.pattern)) 
    print('total %s pickle objects.'%len(pickles))
    #print(pickles)
    for p in pickles:
        fs, es = opts.pattern.split('*')
        fn = p.split(fs)[-1].split(es)[0]
        myp = pickle.load(open(p, 'rb'))
        
        mpl.rcParams['figure.figsize']=[7.5, 3.25]
        fig, axes = plt.subplots(nrows=1, ncols=2)
        
        # summarize history for accuracy
        ax1 = axes[0]
        ax1.plot(myp['acc'])
        ax1.plot(myp['val_acc'])
        ax1.set_title('model accuracy')
        ax1.set_ylabel('accuracy')
        ax1.set_xlabel('epoch')
        ax1.set_ylim(0,1.01)
        ax1.legend(['train', 'validation'], loc='lower right')
        max_acc = max(myp['val_acc'])
	# summarize history for loss
        ax2 = axes[1]
        ax2.plot(myp['loss'])
        ax2.plot(myp['val_loss'])
        ax2.set_title('model loss')
        ax2.set_ylabel('loss')
        ax2.set_xlabel('epoch')
        ax2.legend(['train', 'validation'], loc='upper right')
        plt.tight_layout()
        plt.savefig('%s_%s.png'%(max_acc,fn))    
        plt.clf()

if __name__ == "__main__":
    main()
