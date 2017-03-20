from sklearn.feature_selection import SelectKBest, SelectPercentile, chi2
from sklearn import cross_validation
from sklearn import metrics

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


class BaseClassifier(object):
    """
    A base class for creating various classifiers like discourse-new or singleton classifiers
    """
    def __init__(self):
        self.fitted_ = False
        self.clf_ = None

        self.random_state = 0

        self.class_names_ = []
        self.feature_names_ = []

        self.cur_data_ = None

        self.stats = {}

        self.x_data = None
        self.y_data = None

        self.groups = None

    def clear_stats(self):
        self.stats = {stat: [] for stat in self.stats}

    def get_feature_vector(self, group, i_text, save_feature_names=False):
        return []

    def is_fitted(self):
        if not self.fitted_:
            print 'Classifier is not fitted. Use clf.fit() before calling this function'
        return self.fitted_

    def prepare_data(self, corpus, random_state=42, test_size=0.3):
        if random_state:
            self.random_state=random_state

        if self.x_data and self.y_data:
            tmp_x_data = [self.x_data[i] + [self.groups[i]] for i in xrange(len(self.x_data))]

            tmp_x_data_train,\
            tmp_x_data_test, \
            self.y_data_train, \
            self.y_data_test = cross_validation.train_test_split(tmp_x_data, self.y_data,
                                                                 test_size=test_size,
                                                                 random_state=self.random_state)
            self.x_data_train = [item[:-1] for item in tmp_x_data_train]
            self.x_data_test = [item[:-1] for item in tmp_x_data_test]
            self.groups_train = [item[-1] for item in tmp_x_data_train]
            self.groups_test = [item[-1] for item in tmp_x_data_test]


    def fit(self, clf, sampler=None):
        if not self.x_data:
            print 'Data is not loaded. Use prepare_data() before calling this function'

        if sampler:
            x_train, y_train = sampler.fit_sample(np.array(self.x_data_train), np.array(self.y_data_train))
        else:
            x_train, y_train = self.x_data_train, self.y_data_train

        self.clf_ = clf
        self.clf_.fit(x_train, y_train)

        self.fitted_ = True

    def predict(self, x_test=None):
        if not self.is_fitted():
            return None

        return self.clf_.predict(x_test if x_test else self.x_data_test)

    def test(self, x_test=None, y_test=None, y_pred=None, test_name='', errors=False):
        if x_test is None:
            x_test = self.x_data_test
        if y_test is None:
            y_test = self.y_data_test

        y_predicted = self.predict(x_test) if y_pred is None else y_pred
        cm = metrics.confusion_matrix(y_test, y_predicted)

        plt.figure(figsize=(3, 3))
        sns.heatmap(cm, annot=True,  fmt='', xticklabels=self.class_names_, yticklabels=self.class_names_)
        plt.title('Confusion Matrix {}'.format(test_name))
        plt.show()
        print('Report {}: {}'.format(test_name,
                                     metrics.classification_report(y_test,
                                                                   y_predicted,
                                                                   target_names=self.class_names_,
                                                                   digits=3)))

    def print_stats(self):
        if not self.clf_:
            print "Classifier is not loaded"
        else:
            print "Classifier {clf}: {is_fitted}fitted".format(clf=self.clf_.__class__,
                                                           is_fitted="" if self.fitted_ else "not ")
        if not self.x_data:
            print "Data is not loaded"
        else:
            print "Data: {} ({})\nTotal:\t{} samples".format(self.cur_data_,
                                                            ', '.join(self.class_names_),
                                                            len(self.x_data))
            for i, class_name in enumerate(self.class_names_):
                print "\t{n} {cls}".format(cls=class_name, n=sum(1 for item in self.y_data if item == i))


    def get_feature_importances(self):
        pass
