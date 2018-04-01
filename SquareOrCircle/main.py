#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : main.py
# @Author: Huangqinjian
# @Date  : 2018/3/31
# @Desc  :

import tensorflow as tf
import pandas as pd
import numpy as np


def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)


def conv2d(x, W):
    # stride [1, x_movement, y_movement, 1]
    # Must have strides[0] = strides[3] = 1
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')


def max_pool_2x2(x):
    # stride [1, x_movement, y_movement, 1]
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')


def loadTrainData(TrainInputFile):
    data = pd.read_csv(TrainInputFile)
    X_trainList = []
    Y_trainList = []
    data_len = len(data)
    data_col = data.shape[1]
    for row in range(0, data_len):
        tmpList = []
        for col in range(1, data_col - 1):
            tmpList.append(data.iloc[row][col])
        X_trainList.append(tmpList)
        Y_trainList.append(data.iloc[row][data_col - 1])
    return X_trainList, Y_trainList


def loadTestData(TestInputFile):
    data = pd.read_csv(TestInputFile)
    X_testList = []
    data_len = len(data)
    for row in range(0, data_len):
        tmpList = []
        for col in range(1, data.shape[1]):
            tmpList.append(data.iloc[row][col])
        X_testList.append(tmpList)
    return X_testList


# 对标签进行独热编码
def getLabelOnHot(labelList):
    class_num = 2
    b = tf.one_hot(labelList, class_num, 1, 0)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        label = sess.run(b)
    return label


X_train, Y_train = loadTrainData('data/train.csv')
X_test = loadTestData('data/test.csv')
Y_train = getLabelOnHot(Y_train)
# 1600=40*40  输入的图片大小为40*40
xs = tf.placeholder(tf.float32, [None, 1600])
# 类别数目，因为本题目只有两个分类，所以为2
ys = tf.placeholder(tf.float32, [None, 2])
keep_prob = tf.placeholder(tf.float32)
x_image = tf.reshape(xs, [-1, 40, 40, 1])

## conv1 layer ##
W_conv1 = weight_variable([5, 5, 1, 32])  # patch 5x5, in size 1, out size 32
b_conv1 = bias_variable([32])
h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)  # out 40x40x32
print('第一层卷积层大小为：{0}'.format(h_conv1.shape))
h_pool1 = max_pool_2x2(h_conv1)
print('第一层池化层层大小为：{0}'.format(h_pool1.shape))  # out 20x20x32

## conv2 layer ##
W_conv2 = weight_variable([5, 5, 32, 64])  # patch 5x5, in size 32, out size 64
b_conv2 = bias_variable([64])
h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
print('第二层卷积层大小为：{0}'.format(h_conv2.shape))  # out 20x20x64
h_pool2 = max_pool_2x2(h_conv2)
print('第二层池化层大小为：{0}'.format(h_pool2.shape))  # out 10x10x64

## full_connect layer 全连接层 ##
W_fc1 = weight_variable([10 * 10 * 64, 1024])
b_fc1 = bias_variable([1024])

h_pool2_flat = tf.reshape(h_pool2, [-1, 10 * 10 * 64])
h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)
print('全连接层大小为：{0}'.format(h_fc1.shape))  # out 1024
h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

## output layer  输出层 ##
W_fc2 = weight_variable([1024, 2])
b_fc2 = bias_variable([2])
prediction = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)
print('输出层大小为：{0}'.format(prediction.shape))

# the error between prediction and real data
# cross_entropy = tf.reduce_mean(-tf.reduce_sum(ys * tf.log(prediction),
#                                               reduction_indices=[1]))  # loss
# ! Notice:returns nan when predict class has probability zero,don't use it
cross_entropy = -tf.reduce_mean(ys * tf.log(tf.clip_by_value(prediction, 1e-10, 1.0)))

# tf.clip_by_value(t, clip_value_min, clip_value_max, name=None)
# 基于定义的min与max对tesor数据进行截断操作，目的是为了应对梯度爆发或者梯度消失的情况。这样通过tf.clip_by_value（）函数就可以保证在进行log运算时，不会出现log0这样的错误或者大于1的概率。

train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

sess = tf.Session()
# important step
sess.run(tf.global_variables_initializer())

sess.run(train_step, feed_dict={xs: X_train, ys: Y_train, keep_prob: 0.5})

y_pre = sess.run(prediction, feed_dict={xs: X_test, keep_prob: 1})
print("输出的预测值的大小是:{0}".format(y_pre.shape))
print("输出的预测值是:{0}".format(y_pre))
# axis=0表示竖直方向最大的数所在的下标；axis=1表示水平方向最大的数所在的下标。
resultList = sess.run(tf.argmax(y_pre, 1))
print("输出的预测结果是:{0}".format(resultList))
result_len = len(resultList)
id_list = np.arange(4000, 7550)
data_arr = []
for row in range(0, result_len):
    data_arr.append([int(id_list[row]), resultList[row]])
np_data = np.array(data_arr)

# 写入文件
pd_data = pd.DataFrame(np_data, columns=['id', 'y'])
# print(pd_data)
pd_data.to_csv('submit.csv', index=None)
