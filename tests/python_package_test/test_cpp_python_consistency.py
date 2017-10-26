# coding: utf-8
# pylint: skip-file
import os
import unittest

import lightgbm as lgb
import numpy as np
from sklearn.datasets import load_svmlight_file


class FileLoader(object):

    def __init__(self, directory, prefix, config_file='train.conf'):
        directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), directory)
        self.directory = directory
        self.prefix = prefix
        self.params = {}
        with open(os.path.join(directory, config_file), 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = [token.strip() for token in line.split('=')]
                    if 'early_stopping' not in key:  # disable early_stopping
                        self.params[key] = value

    def load_dataset(self, suffix, is_sparse=False):
        filename = os.path.join(self.directory, self.prefix + suffix)
        if is_sparse:
            return load_svmlight_file(filename, dtype=np.float64), filename
        else:
            mat = np.loadtxt(filename, dtype=np.float64)
            return mat[:, 1:], mat[:, 0], filename

    def load_field(self, suffix):
        return np.loadtxt(os.path.join(self.directory, self.prefix + suffix))

    def load_cpp_result(self, result_file='LightGBM_predict_result.txt'):
        return np.loadtxt(os.path.join(self.directory, result_file))

    def train_predict_check(self, lgb_train, X_test, X_test_fn):
        gbm = lgb.train(self.params, lgb_train)
        y_pred = gbm.predict(X_test)
        cpp_pred = gbm.predict(X_test_fn)
        np.testing.assert_array_almost_equal(y_pred, cpp_pred, decimal=5)


class TestEngine(unittest.TestCase):

    def test_binary(self):
        fd = FileLoader('../../examples/binary_classification', 'binary')
        X_train, y_train, _ = fd.load_dataset('.train')
        X_test, _, X_test_fn = fd.load_dataset('.test')
        weight_train = fd.load_field('.train.weight')
        lgb_train = lgb.Dataset(X_train, y_train, params=fd.params, weight=weight_train)
        fd.train_predict_check(lgb_train, X_test, X_test_fn)

    def test_multiclass(self):
        fd = FileLoader('../../examples/multiclass_classification', 'multiclass')
        X_train, y_train, _ = fd.load_dataset('.train')
        X_test, _, X_test_fn = fd.load_dataset('.test')
        lgb_train = lgb.Dataset(X_train, y_train)
        fd.train_predict_check(lgb_train, X_test, X_test_fn)

    def test_regression(self):
        fd = FileLoader('../../examples/regression', 'regression')
        X_train, y_train, _ = fd.load_dataset('.train')
        X_test, _, X_test_fn = fd.load_dataset('.test')
        init_score_train = fd.load_field('.train.init')
        lgb_train = lgb.Dataset(X_train, y_train, init_score=init_score_train)
        fd.train_predict_check(lgb_train, X_test, X_test_fn)

    def test_lambdarank(self):
        fd = FileLoader('../../examples/lambdarank', 'rank')
        X_train, y_train, _ = fd.load_dataset('.train', is_sparse=True)
        X_test, _, X_test_fn= fd.load_dataset('.test', is_sparse=True)
        group_train = fd.load_field('.train.query')
        lgb_train = lgb.Dataset(X_train, y_train, group=group_train)
        fd.train_predict_check(lgb_train, X_test, X_test_fn)
