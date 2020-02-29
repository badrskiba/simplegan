import tensorflow as tf 
import numpy as np
import os
import cv2
import glob
from tqdm import tqdm

'''
returns datasets used in Pix2Pix paper and custom dataset

datasets used in paper are available at: https://people.eecs.berkeley.edu/~tinghuiz/projects/pix2pix/datasets/

The following code is inspired from: https://www.tensorflow.org/tutorials/generative/pix2pix#load_the_dataset

Note: 
-> if using custom dataset, ensure it is organized into train and test directory
-> The see how the custom image should be, load a dataset used in pix2pix and visualize it 
'''


class pix2pix_dataloader:

    def __init__(self, dataset_name = None, img_width = 256, img_height = 256, 
                datadir = None):
        
        self.dataset_name = dataset_name
        self.img_width = img_width
        self.img_height = img_height
        self.datadir = datadir
        self.channels = None
        

    def _load_path(self, dataset_name):

        URLs = {'cityscapes':'https://people.eecs.berkeley.edu/~tinghuiz/projects/pix2pix/datasets/cityscapes.tar.gz',
                'edges2handbags':'https://people.eecs.berkeley.edu/~tinghuiz/projects/pix2pix/datasets/edges2handbags.tar.gz',
                'edges2shoes':'https://people.eecs.berkeley.edu/~tinghuiz/projects/pix2pix/datasets/edges2shoes.tar.gz',
                'facades':'https://people.eecs.berkeley.edu/~tinghuiz/projects/pix2pix/datasets/facades.tar.gz',
                'maps':'https://people.eecs.berkeley.edu/~tinghuiz/projects/pix2pix/datasets/maps.tar.gz'}

        URL = URLs[dataset_name]

        filename = dataset_name + '.tar.gz'

        path = tf.keras.utils.get_file(filename, origin = URL, extract=True)
        return os.path.join(os.path.dirname(path), dataset_name)


    def _load_image(self, filename):

        image = tf.io.read_file(filename)
        image = tf.image.decode_jpeg(image)

        w = tf.shape(image)[1]
        w = w // 2

        real_image = image[:,:w, :]
        input_image = image[:, w:, :]

        self.channels = real_image.shape[-1]

        input_image = tf.cast(input_image, tf.float32)
        real_image = tf.cast(real_image, tf.float32)

        return input_image, real_image

    def __resize(self, input_image, real_image, height, width):

        input_image = tf.image.resize(input_image, [height, width],
                                method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

        real_image = tf.image.resize(real_image, [height, width],
                               method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

        return input_image, real_image

    def _random_crop(self, input_image, real_image):

        stacked_image = tf.stack([input_image, real_image], axis=0)
        cropped_image = tf.image.random_crop(stacked_image, size=[2, self.img_height, self.img_width, self.channels])

        return cropped_image[0], cropped_image[1]

    def _normalize_image(self, input_image, real_image):

        input_image = (input_image / 127.5) - 1
        real_image = (real_image / 127.5) - 1

        return input_image, real_image

    @tf.function
    def _random_jitter(self, input_image, real_image):

        input_image, real_image = self._resize(input_image, real_image, 286, 286)
        input_image, real_image = self._random_crop(input_image, real_image)

        if(tf.random.uniform(()) > 0.5):
            input_image = tf.image.flip_left_right(input_image)
            real_image = tf.image.flip_left_right(real_image)

        return input_image, real_image

    def _load_train_images(self, filename):

        input_image, real_image = self._load_image(filename)
        input_image, real_image = self._random_jitter(input_image, real_image)
        input_image, real_image = self._normalize_image(input_image, real_image)

        return input_image, real_image

    def _load_test_images(self, filename):

        input_image, real_image = self._load_image(filename)
        input_image, real_image = self._resize(input_image, real_image, self.img_height, self.img_width)
        input_image, real_image = self._normalize_image(input_image, real_image)

        return input_image, real_image

    def _load_pix2pix_data(self):

        train_data = tf.data.Dataset.list_files(self._load_path(self.dataset_name)+'/train/*.jpg')
        train_ds = train_data.map(self._load_train_images, 
                                        num_arallel_calls=tf.data.experimental.AUTOTUNE)

        test_data = tf.data.Dataset.list_files(self._load_path(self.dataset_name)+'/test/*.jpg')
        test_ds = test_data.map(self.__load_test_images)

        return train_ds, test_ds

    def _load_custom_data(self):

        assert os.path.exists(os.path.join(self.datadir, '/train')), "No such directory as train found"

        train_data = tf.data.Dataset.list_files(os.path.join(self.datadir, '/train/*.jpg'))
        train_ds = train_data.map(self._load_train_images, 
                                        num_parallel_calls=tf.data.experimental.AUTOTUNE)

        assert os.path.exists(os.path.join(self.datadir, '/test')), "No such directory as test found"

        test_data = tf.data.Dataset.list_files(os.path.join(self.datadir, '/test/*.jpg'))
        test_ds = test_data.Dataset.map(self._load_test_images)

        return train_ds, test_ds

    def load_dataset(self):

        assert self.dataset_name != None or self.datadir != None, "Enter directory to load custom data or choose from exisisting data to load from"

        if(self.dataset_name != None):
            train_ds, test_ds = self._load_pix2pix_data()

        else:
            train_ds, test_ds = self._load_custom_data()

        return train_ds, test_ds