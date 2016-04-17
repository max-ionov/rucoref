import collections
from anaphoralib import utils

class Corpus(object):
    def __init__(self, tagset, format):
        self.tagset = tagset
        self.format = format

        self.texts = []
        self.gs = []

        self.groups = []
        self.mentions = []

        self.n_errors = collections.defaultdict(int)
        """Dict containing numbers of errors aroused while creating various indices"""

        self.texts_loaded_ = False
        self.gs_loaded_ = False

        # various indices
        self.heads_index = []
        """For each text contains a dictionary mapping each group head offset to its group"""

        self.words_index = []
        """For each text contains a dictionary mapping offset of each word to its index"""

        self.mentions_index = []
        """For each text contains a dictionary mapping offset of each mention to its index"""

        self.chains_index = []
        """For each text contains a dictionary mapping each group id (in GS) to its chain id (in GS)"""

        self.gs_mapping = []
        """For each text contains a dictionary mapping each group id (in GS) to a tuple of indices of mentions
        that are heads of this group"""

        self.gs_index = []
        """For each text contains a dictionary mapping each GS group index to text group index"""

    def load_texts(self, filename):
        pass

    def load_gs(self, filename):
        pass

    def find_groups(self):
        """Fills two class attributes: groups and mentions with lists of all groups and mentions
        (groups that are nouns or pronouns) in texts"""
        if self.texts_loaded():
            self.groups = [utils.find_groups(text, self.tagset) for text in self.texts]
            self.mentions = [utils.find_mentions(text, self.tagset) for text in self.texts]


    def create_indices(self):
        """Creates indices that are not corpus-specific"""
        self.heads_index = []
        self.words_index = []
        self.mentions_index = []

        for i, text in enumerate(self.texts):
            self.heads_index.append({})
            self.words_index.append({text[j].offset: j for j in xrange(len(text))})
            self.mentions_index.append({self.mentions[i][j].offset: j for j in xrange(len(self.mentions[i]))})

            for group in self.groups[i]:
                for g in group.iter_groups():
                    head_offset = g.head_offset()
                    if head_offset not in self.heads_index[-1] \
                            or len(g.lemma) > len(self.heads_index[-1][head_offset].lemma):
                        self.heads_index[-1][head_offset] = g

    def gs_loaded(self):
        return self.gs_loaded_

    def texts_loaded(self):
        return self.texts_loaded_

    def print_stats(self):
        if not (self.texts_loaded() and self.gs_loaded()):
            return

        n_chains = sum(len(text['chains']) for text in self.gs)
        n_words = sum(sum(len(text['chains'][chain]) for chain in text['chains']) for text in self.gs)

        print 'Number of texts: {n_texts}\n' \
              'Number of GS texts: {n_gs}\n' \
              'Number of chains in a corpus: {n_chains}\n' \
              'Number of words in all chains: {n_words}'.format(n_texts=len(self.texts),
                                                                n_gs=len(self.gs),
                                                                n_chains=n_chains,
                                                                n_words=n_words)

    def iterate_mentions(self, text_indices=None):
        """Yields every mention from every text which index is not in text_indices"""
        for i_text, text in enumerate(self.texts):
            if text_indices and i_text not in text_indices:
                continue
            for i_mention, mention in enumerate(self.mentions[i_text]):
                yield i_text, i_mention, self.mentions[i_text][i_mention]


    def are_coreferent(self, group1, group2):
        """Returns true if two groups are coreferent"""
        if not self.gs_loaded_:
            return False

