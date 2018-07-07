from keras.models import load_model

def Pred(model_name, pred_data):
    """
    using your trained model to make predictions.
    The pred_data is a numpy array object which has the same number of columns as the training data.
    """

    my_model = load_model('...')

    pre_prob = my_model.predict(pred_data)
    predictions = pre_prob.argmax(axis=1)

    print("You can load the dict back using pickle.load(open('*.p', 'rb'))"%(count_hid_lyr, lr))
    
