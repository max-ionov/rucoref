#!/usr/bin/python2.7
# -!- coding: utf-8 -!-
# usage: anaphoramllib.py

from __future__ import unicode_literals

import os
import random
import cPickle as pickle
import numpy as np

from ..tagsets import utils

class AnaphoraResolutor(object):
    """
    Base class for Anaphora resolution
    """
    def __init__(self, tagset):
        self.tagset = tagset

    def is_anaphor(self, group):
        pronouns = {
            u'он', u'она', u'оно', u'они',
            u'его', u'ее', u'её', u'их',
            u'себя', u'свой'
        }

        return group.lemma in pronouns

    def get_antecedent(self, group, groups):
        return None

    def group_fits(self, group, target_group):
        return True

    def iterate_possible_antecedents(self, target_group, groups):
        return sorted([group for group in groups
                       if -10 < groups.index(target_group) - groups.index(group) < 25 and
                             group.offset != target_group.offset and
                              (self.tagset.pos_filters['noun'](group) or self.tagset.pos_filters['pronoun'](group))
                             and self.group_fits(group, target_group)],
                             key=lambda x: x.offset, reverse=True)

# Base class for ML-based approaches
# To create non-abstract resolutor class, one could only override get_feature_vector function
# (See BasicAnaphoraMLResolutor as an example)
# For more elaborate implementations, iterate_possible_antecedents could also be overridden to filter more precisely

class AnaphoraMLResolutor(AnaphoraResolutor):
    def __init__(self, tagset):
        super(AnaphoraMLResolutor, self).__init__(tagset)
        self.model = None
        self.trained = False

    def train_model(self, clf_object, data):
        """
        Fits a classifier clf_object using vectors generated from training data and stores it in self.model
        :param data: Data should be a list of tuples: [(index_of_antecedent, indices_of_candidates,
        index_of_anaphora, all_groups)]
        :return:
        """
        self.model = clf_object

        train_x = []
        train_y = []
        for position in data:
            n_antecedent, candidates, n_anaphora, groups = position

            candidates = random.sample(xrange(len(candidates)), len(candidates) / 2)
            if not n_antecedent in candidates:
                candidates.append(n_antecedent)

            y_data = [1 if i==n_antecedent else 0 for i in candidates]

            train_x.extend(self.get_feature_vector(i, n_anaphora, groups) for i in candidates)
            train_y.extend(y_data)

        self.model.fit(np.asarray(train_x), np.asarray(train_y))
        self.trained = True


    def load_model(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as inp_file:
                self.model = pickle.load(inp_file)
            self.trained = True

    def save_model(self, filename):
        if self.model:
            with(open(filename, 'wb')) as inp_file:
                pickle.dump(self.model, inp_file)

    def get_feature_vector(self, n_antecedent, n_anaphora, groups):
        return []

    def get_antecedent(self, target_group, groups):
        if self.model and self.trained:
            for group in self.iterate_possible_antecedents(target_group, groups):
                if self.model.predict(self.get_feature_vector(groups.index(group), groups.index(target_group), groups))[0]:
                    return group

        return None

class BasicAnaphoraMLResolutor(AnaphoraMLResolutor):
    def get_feature_vector(self, n_antecedent, n_anaphora, groups):
        return [groups[n_anaphora].offset - groups[n_antecedent].offset]

# Dummy resolutors for using as a baseline
class AnaphoraDummyResolutor(AnaphoraResolutor):
    def group_fits(self, potential_antecedent, anaphor):
        return True

    def get_antecedent(self, target_group, groups):
        antecedents = self.iterate_possible_antecedents(target_group, groups)
        return antecedents[0] if len(antecedents) > 0 else None

class AnaphoraAgrResolutor(AnaphoraDummyResolutor):
    def group_fits(self, potential_antecedent, anaphor):
        return utils.same_grammemmes('gender', (potential_antecedent, anaphor), self.tagset) and \
                utils.same_grammemmes('number', (potential_antecedent, anaphor), self.tagset)
