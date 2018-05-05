from __future__ import print_function

import os
import numpy as np
import tensorflow as tf

from abc import abstractmethod
from .dataset import *
from .ops import pixelwise_accuracy
from .networks import Generator, Discriminator
from .dataset import Places365Dataset, Cifar10Dataset


class BaseModel:
    def __init__(self, sess, options):
        self.sess = sess
        self.options = options
        self.name = 'COLGAN_' + options.dataset
        self.saver = tf.train.Saver()
        self.path = os.path.join(options.checkpoint_path, self.name)
        self.global_step = tf.Variable(0, name='global_step', trainable=False)

    def train(self):
        dataset = self.create_dataset(True)

        for epoch in range(self.options.epochs):
            counter = 0
            generator = dataset.generator(self.options.batch_size)

            for color_images in generator:
                counter += self.options.batch_size
                gray_images = rgb2gray(color_images)

                if self.options.color_space == COLORSPACE_LAB:
                    color_images = rgb2lab(color_images)

                self.sess.run([self.dis_train], feed_dict={})
                self.sess.run([self.gen_train], feed_dict={})

                errD_fake = self.dis_loss_fake.eval({})
                errD_real = self.dis_loss_real.eval({})
                errG = self.gen_loss.eval({})

            self.save()

    def test(self):
        dataset = self.create_dataset(False)

    def build(self):
        # create models
        gen = self.create_generator()
        dis = self.create_discriminator()
        sce = tf.nn.sigmoid_cross_entropy_with_logits

        self.gen = gen.create()
        self.dis = dis.create()
        self.gan = dis.create(gen_out, reuse_variables=True)
        self.sampler = gen.create(z_placeholder, reuse_variables=True)

        #tf.concat([color_inputs, grayscale_inputs], axis=3)

        self.gen_loss = tf.reduce_mean(sce(logits=self.gen, labels=tf.ones_like(self.gen)))
        self.dis_loss_real = tf.reduce_mean(sce(logits=self.dis, labels=tf.ones_like(self.dis) * 0.9))
        self.dis_loss_fake = tf.reduce_mean(sce(logits=self.gen, labels=tf.zeros_like(self.gen)))
        self.dis_loss = self.dis_loss_real + self.dis_loss_fake


        # generator optimizaer
        self.gen_train = tf.train.AdamOptimizer(
            learning_rate=self.options.lr,
            beta1=self.options.beta1
        ).minimize(self.gen_loss, var_list=gen.var_list)

        # discriminator optimizaer
        self.dis_train = tf.train.AdamOptimizer(
            learning_rate=self.options.lr,
            beta1=self.options.beta1
        ).minimize(self.dis_loss, var_list=dis.var_list)

    def load(self):
        print('loading model...\n')

        ckpt = tf.train.get_checkpoint_state(self.path)

        if ckpt and ckpt.model_checkpoint_path:
            self.saver.restore(self.sess, self.path)
            return True

        else:
            print("failed to find a checkpoint")
            return False

    def save(self):
        print('saving model...\n')
        self.saver.save(self.sess, self.path, global_step=self.global_step)

    @abstractmethod
    def create_generator(self):
        raise NotImplementedError

    @abstractmethod
    def create_discriminator(self):
        raise NotImplementedError

    @abstractmethod
    def create_dataset(self, training):
        raise NotImplementedError


class Cifar10Model(BaseModel):
    def __init__(self, sess, options):
        super(Cifar10Model, self).__init__(sess, options)

    def create_generator(self):
        kernels_gen_encoder = [
            (64, 1, 0),     # [batch, 32, 32, ch] => [batch, 32, 32, 64]
            (128, 2, 0),    # [batch, 32, 32, 64] => [batch, 16, 16, 128]
            (256, 2, 0),    # [batch, 16, 16, 128] => [batch, 8, 8, 256]
            (512, 2, 0),    # [batch, 8, 8, 256] => [batch, 4, 4, 512]
            (512, 2, 0)     # [batch, 4, 4, 512] => [batch, 2, 2, 512]
        ]

        kernels_gen_decoder = [
            (512, 2, 0.5),  # [batch, 2, 2, 512] => [batch, 4, 4, 512]
            (256, 2, 0),    # [batch, 4, 4, 512] => [batch, 8, 8, 256]
            (128, 2, 0),    # [batch, 8, 8, 256] => [batch, 16, 16, 128]
            (64, 2, 0)      # [batch, 16, 16, 128] => [batch, 32, 32, 512]
        ]

        return Generator('gen', kernels_gen_encoder, kernels_gen_decoder)

    def create_discriminator(self):
        kernels_dis = [
            (64, 2, 0),     # [batch, 32, 32, ch] => [batch, 16, 16, 64]
            (128, 2, 0),    # [batch, 16, 16, 64] => [batch, 8, 8, 128]
            (256, 2, 0),    # [batch, 8, 8, 128] => [batch, 4, 4, 256]
            (512, 1, 0)     # [batch, 4, 4, 256] => [batch, 4, 4, 512]
        ]

        return Discriminator('dis', kernels_dis)

    def create_dataset(self, training=True):
        return Cifar10Dataset(
            path=self.options.dataset_path,
            training=training,
            augment=self.options.augment)


class Places365Model(BaseModel):
    def __init__(self, sess, options):
        super(Places365Model, self).__init__(sess, options)

    def create_generator(self):
        kernels_gen_encoder = [
            (64, 1, 0),     # [batch, 256, 256, ch] => [batch, 256, 256, 64]
            (64, 2, 0),     # [batch, 256, 256, 64] => [batch, 128, 128, 64]
            (128, 2, 0),    # [batch, 128, 128, 64] => [batch, 64, 64, 128]
            (256, 2, 0),    # [batch, 64, 64, 128] => [batch, 32, 32, 256]
            (512, 2, 0),    # [batch, 32, 32, 256] => [batch, 16, 16, 512]
            (512, 2, 0),    # [batch, 16, 16, 512] => [batch, 8, 8, 512]
            (512, 2, 0),    # [batch, 8, 8, 512] => [batch, 4, 4, 512]
            (512, 2, 0)     # [batch, 4, 4, 512] => [batch, 2, 2, 512]
        ]

        kernels_gen_decoder = [
            (512, 2, 0.5),  # [batch, 2, 2, 512] => [batch, 4, 4, 512]
            (512, 2, 0.5),  # [batch, 4, 4, 512] => [batch, 8, 8, 512]
            (512, 2, 0.5),  # [batch, 8, 8, 512] => [batch, 16, 16, 512]
            (256, 2, 0),    # [batch, 16, 16, 512] => [batch, 32, 32, 256]
            (128, 2, 0),    # [batch, 32, 32, 256] => [batch, 64, 64, 128]
            (64, 2, 0),     # [batch, 64, 64, 128] => [batch, 128, 128, 64]
            (64, 2, 0)      # [batch, 128, 128, 64] => [batch, 256, 256, 64]
        ]

        return Generator('gen', kernels_gen_encoder, kernels_gen_decoder)

    def create_discriminator(self):
        kernels_dis = [
            (64, 2, 0),     # [batch, 256, 256, ch] => [batch, 128, 128, 64]
            (128, 2, 0),    # [batch, 128, 128, 64] => [batch, 64, 64, 128]
            (256, 2, 0),    # [batch, 64, 64, 128] => [batch, 32, 32, 256]
            (512, 2, 0),    # [batch, 32, 32, 256] => [batch, 16, 16, 512]
            (512, 2, 0),    # [batch, 16, 16, 512] => [batch, 8, 8, 512]
            (512, 2, 0)     # [batch, 8, 8, 512] => [batch, 4, 4, 512]
        ]

        return Discriminator('dis', kernels_dis)

    def create_dataset(self, training=True):
        return Places365Dataset(
            path=self.options.dataset_path,
            training=training,
            augment=self.options.augment)
