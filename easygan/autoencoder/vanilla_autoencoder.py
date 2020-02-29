import tensorflow as tf 
from tensorflow.keras.layers import Conv2D, Dropout, BatchNormalization, LeakyReLU, Conv2DTranspose, Dense, Reshape, Flatten
from tensorflow.keras import Model
import numpy as np
from ..datasets.load_cifar10 import load_cifar10
from ..datasets.load_mnist import load_mnist
from ..datasets.load_custom_data import load_custom_data
from ..losses.mse_loss import mse_loss
import datetime

'''
vanilla_autoencoder imports from tensorflow Model class

Create an instance of the class and compile it by using the loss from ../losses/mse_loss and use an optimizer and metric of your choice

use the fit function to train the model. 

'''
class VanillaAutoencoder():

	def __init__(self):
    	'''
    	initialize the number of encoder and layers
    	'''
        super(VanillaAutoencoder, self).__init__()
    	self.model = tf.keras.Sequential()
        self.image_size = None


	def load_data(self, data_dir = None, use_mnist = False, 
        use_cifar10 = False, batch_size = 32, img_shape = (64,64)):

		'''
		choose the dataset, if None is provided returns an assertion error -> ../datasets/load_custom_data
		returns a tensorflow dataset loader
		'''

		if(use_mnist):

			train_data = load_mnist()
		
		elif(use_cifar10):

			train_data = load_cifar10()

		else:

			train_data = load_custom_data(data_dir, img_shape)

        self.image_size = train_data.shape[1:]

        train_data = train_data.reshape((-1, self.image_size[0]*self.image_size[1]*self.image_size[2])) / 255
        train_ds = tf.data.Dataset.from_tensor_slices(train_data).shuffle(10000).batch(batch_size)

		return train_ds


    def encoder(self, params):

        enc_units = params['enc_units'] if 'enc_units' in params else [256, 128]
        encoder_layers = params['encoder_layers'] if 'encoder_layers' in params else 2
        interm_dim = params['interm_dim'] if 'interm_dim' in params else 64
        activation = params['activation'] if 'activation' in params else 'relu'
        kernel_initializer = params['kernel_initializer'] if 'kernel_initializer' in params else 'glorot_uniform'
        kernel_regularizer = params['kernel_regularizer'] if 'kernel_regularizer' in params else None

        assert len(enc_units) == encoder_layers, "Dimension mismatch: length of enocoder units should match number of encoder layers"

        model = tf.keras.Sequential()

        model.add(Dense(enc_units[0]*2, activation= activation, kernel_initializer=kernel_initializer,
            kernel_regularizer=kernel_regularizer, input_dim = self.image_size[0]*self.image_size[1]*self.image_size[2]))

        for i in range(encoder_layers):
            model.add(Dense(enc_units[i], activation=activation, kernel_initializer=kernel_initializer, 
                kernel_regularizer=kernel_regularizer))

        model.add(Dense(interm_dim, activation='sigmoid'))

        return model


    def decoder(self, params):

        dec_units = params['dec_units'] if 'dec_units' in params else [128, 256]
        decoder_layers = params['decoder_layers'] if 'decoder_layers' in params else 2
        interm_dim = params['interm_dim'] if 'interm_dim' in params else 64
        activation = params['activation'] if 'activation' in params else 'relu'
        kernel_initializer = params['kernel_initializer'] if 'kernel_initializer' in params else 'glorot_uniform'
        kernel_regularizer = params['kernel_regularizer'] if 'kernel_regularizer' in params else None

        assert len(dec_units) == decoder_layers, "Dimension mismatch: length of decoder units should match number of decoder layers"

        model = tf.keras.Sequential()

        model.add(Dense(dec_units[0] // 2, activation=activation, kernel_initializer=kernel_initializer,
            kernel_regularizer = kernel_regularizer, input_dim = interm_dim))

        for i in range(decoder_layers):
            model.add(Dense(dec_units[i], activation=activation, kernel_initializer=kernel_initializer,
            kernel_regularizer = kernel_regularizer))

        model.add(Dense(self.image_size[0]*self.image_size[1]*self.image_size[2], activation='sigmoid'))

        return model

    '''
    call build_model to intialize the layers before you train the model
    '''
	def build_model(self, params = {'encoder_layers':2, 'decoder_layers':2, 'interm_dim':64, 
        'enc_units': [256, 128], 'dec_units':[128, 256], 'activation':'relu', 'kernel_initializer': 'glorot_uniform', 
        'kernel_regularizer': None}):

		self.model.add(self.encoder())
        self.model.add(self.decoder())


    def fit(self, train_ds = None, epochs = 100, optimizer = 'Adam', print_steps = 100, 
        learning_rate = 0.001, tensorboard = False, save_model = None):

        assert train_ds != None, 'Initialize training data through train_ds parameter'

        kwargs = {}
        kwargs['learning_rate'] = gen_learning_rate
        optimizer = getattr(tf.keras.optimizers, gen_optimizer)(**kwargs)

        if(tensorboard):
            current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            train_log_dir = 'logs/gradient_tape/' + current_time + '/train'
            train_summary_writer = tf.summary.create_file_writer(train_log_dir)

        steps = 0

        for epoch in range(epochs):

            for data in train_ds:

                with tf.GradientTape() as tape:
                    recon_data = self.model(data)
                    loss = mse_loss(data, recon_data)

                gradients = tape.gradient(loss, self.model.trainable_variables)
                optimizer.apply_gradients(zip(gradients, self.model.trainable_variables))

                if(steps % print_steps == 0):
                    print("Step:", steps+1, 'reconstruction loss', loss.numpy())

                steps += 1

                if(tensorboard):
                    with train_summary_writer.as_default():
                        tf.summary.scalar('loss', loss.numpy(), step=steps)


        if(save_model != None):

            assert type(save_model) == str, "Not a valid directory"
            if(save_model[-1] != '/'):
                self.model.save_weights(save_model + '/vanilla_autoencoder_checkpoint')
            else:
                self.model.save_weights(save_model + 'vanilla_autoencoder_checkpoint')