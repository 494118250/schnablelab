# 7/6/18
# Chenyong Miao
# design the model
"""
the linear neural network model to segment sorghum components
"""
import numpy as np
from numpy.random import uniform
from keras.utils import to_categorical
from keras.layers import Dense, Dropout, Flatten
from keras.models import Sequential
from keras.optimizers import Adam, SGD
from keras.callbacks import EarlyStopping
from keras.callbacks import History
import pickle

def load_data(predict, target):
    '''
    load numpy array object files .npy
    '''
    try:
        predictors = np.load() # 8000*243
    except IOError:
        print('numpy array object file %s does not exist.'%x)
    try:
        target = np.load() # 8000*1
    except IOError:
        print('numpy array object file %s does not exist.'%y)
    target = to_categorical(target)
    return(predictors,target)

def get_model(num_hiden_layers, num_units, ActivFunc='relu'):
    '''
    design the model structure.
    can also try different activation functions for hidden layers: 
        ReLU(Leaky), ELU(Exponential), or Maxout. 
    For relu, caution on the dying neuron problem
    '''
    n_cols = predictors.shape[1]
    model = Sequential()
    model.add(Dense(100, activation=ActivFunc, input_shape=(n_cols,))) # dense layer
    for i in range(int(num_hiden_layers)-1):
        model.add(Dense(100, activation=ActivFunc))
    model.add(Dense(4, activation='softmax')) # output layer
    model.summary()
    return(model)

def train(x,y,lyr,unit,lr):
    predictors,target = load_data(x,y)
    model = get_model(lyr, unit)
    my_optimizer = SGD(lr=lr)
    model.compile(optimizer=my_optimizer, loss='categorical_crossentropy', metrics=['accuracy']) 
    early_stopping_monitor = EarlyStopping(patience=3)
    model_history = model.fit(predictors, target, validation_split=0.2, epochs=50, callbacks=[early_stopping_monitor])
    model.save('model_%s_%s_%s.h5'%(lyr,unit,lr)) # save model
    pickle.dump(model_history.history, open( "History_%s_%s_%s.p"%(lyr,unit,lr), "wb" ) ) # save training history
