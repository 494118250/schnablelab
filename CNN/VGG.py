"""
implement a simplified VGG to detect sorghum flowering time
"""
from glob import glob
import numpy as np
import pickle
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense
from keras.callbacks import EarlyStopping
from keras.callbacks import History
from keras.optimizers import Adam
from keras.optimizers import SGD

ts = (224,224)
def preprocess(img_dir):
    imgs = []
    all_imgs = glob(img_dir + '/*/*png')
    n = 0
    for i in all_imgs:
        print(n)
        n+=1
        img = load_img(i, target_size = ts)
        img_array = img_to_array(img)
        imgs.append(img_array)
    imgs = np.array(imgs)
    print(imgs.shape)
    print('the demension of image array: %s'%(','.join([str(i) for i in imgs.shape]))) 
    return imgs

def train(train_dir, val_dir, lr, epc, model_name):
    train_imgs =  preprocess(train_dir)
    val_imgs =  preprocess(val_dir)

    train_datagen =  ImageDataGenerator(
      rescale = 1./255,
      featurewise_center=True,
      rotation_range=20,
      width_shift_range=0.2,
      height_shift_range=0.2
      )
    train_datagen.fit(train_imgs)
    train_generator = train_datagen.flow_from_directory(
      train_dir,
      target_size=ts,
      batch_size=30, 
      shuffle=True
      #save_to_dir = '%s_augmented_train_imgs'%model_name,
      #save_prefix = 'aug_train'
      ) 

    val_datagen =  ImageDataGenerator(
      rescale = 1./255,
      featurewise_center=True,
      rotation_range=20,
      width_shift_range=0.2,
      height_shift_range=0.2
      )
    val_datagen.fit(val_imgs)
    val_generator = val_datagen.flow_from_directory(
      val_dir,
      target_size=ts,
      batch_size=30, 
      shuffle=True
      #save_to_dir = '%s_augmented_val_imgs'%model_name,
      #save_prefix = 'aug_val'
      ) 

    model = Sequential([
      Conv2D(64, (3, 3), input_shape=(224, 224, 3), padding='same', activation='relu'),
      Conv2D(64, (3, 3), activation='relu', padding='same'),
      MaxPooling2D(pool_size=(2, 2), strides=(2, 2)),
      #Dropout(0.2),
      Conv2D(128, (3, 3), activation='relu', padding='same'),
      Conv2D(128, (3, 3), activation='relu', padding='same',),
      MaxPooling2D(pool_size=(2, 2), strides=(2, 2)),
      #Dropout(0.2),
      Conv2D(256, (3, 3), activation='relu', padding='same',),
      Conv2D(256, (3, 3), activation='relu', padding='same',),
      Conv2D(256, (3, 3), activation='relu', padding='same',),
      MaxPooling2D(pool_size=(2, 2), strides=(2, 2)),
      #Dropout(0.2),
      Conv2D(512, (3, 3), activation='relu', padding='same',),
      Conv2D(512, (3, 3), activation='relu', padding='same',),
      Conv2D(512, (3, 3), activation='relu', padding='same',),
      MaxPooling2D(pool_size=(2, 2), strides=(2, 2)),
      #Dropout(0.25),
      #Conv2D(512, (3, 3), activation='relu', padding='same',),
      #Conv2D(512, (3, 3), activation='relu', padding='same',),
      #Conv2D(512, (3, 3), activation='relu', padding='same',),
      #MaxPooling2D(pool_size=(2, 2), strides=(2, 2)),
      #Dropout(0.25),
      Flatten(),
      Dense(500, activation='relu'),
      Dropout(0.5),
      Dense(5, activation='softmax')
      ])

    model.summary()
    model.compile(
      loss='categorical_crossentropy',
      #optimizer=Adam(lr=float(lr)), 
      optimizer=SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True), 
      metrics=['accuracy']
      )

    model_history = model.fit_generator(
      train_generator, 
      epochs=int(epc), 
      validation_data=val_generator
      )

    model.save('%s.h5'%model_name)
    print('model has been saved to %s.h5'%model_name)

    pickle.dump(model_history.history, open( "%s_history.p"%model_name, "wb" ) )
    print("model history as a dictionary has been saved pickle \
object %s_history.p. You can load the dict back using \
pickle.load(open('save.p', 'rb'))"%model_name)

import sys
if len(sys.argv)==6:
    train(*sys.argv[1:])
else:
    print('train_dir', 'val_dir', 'lr', 'epoches', 'model_name')
