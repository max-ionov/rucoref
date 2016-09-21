import collections
import os
import codecs
import subprocess
import re

from .. import utils

class Corpus(object):
    def __init__(self, tagset, format):
        self.tagset = tagset
        self.format = format

        self.texts = []
        self.gs = []
        self.doc_ids = []

        self.groups = []
        self.mentions = []

        self.n_errors = collections.defaultdict(int)
        """Dict containing numbers of errors aroused while creating various indices"""

        self.texts_loaded_ = False
        self.gs_loaded_ = False
        self.groups_loaded_ = False

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
            self.groups_loaded_ = True


    def create_indices(self):
        """Creates indices that are not corpus-specific"""
        self.heads_index = []
        self.words_index = []
        self.mentions_index = []

        for i, text in enumerate(self.texts):
            self.heads_index.append({})
            self.words_index.append({text[j].offset: j for j in xrange(len(text))})

            if not self.groups_loaded_:
                self.mentions = [utils.find_mentions(text, self.tagset) for text in self.texts]
            self.mentions_index.append({self.mentions[i][j].offset: j for j in xrange(len(self.mentions[i]))})

            if self.groups_loaded_:
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

    def export_conll(self, filename, groups=None, chains=None):
        """Saves the corpus annotation in the CONLL-2012 shared task format"""
        self.create_indices() # just in case there are no words index yet
        if not groups:
            groups = [text['groups'] for text in self.gs]

        chains_index = self.chains_index if not chains else [{} for text in self.gs]

        with codecs.open(filename, 'w', encoding='utf-8') as out_file:
            for i_text, text in enumerate(self.texts):
                doc_name = 'Doc{}'.format(self.doc_ids[i_text])
                out_file.write('#begin document ({});\n'.format(doc_name))
                words_chains_index = collections.defaultdict(list)
                words_chains_starts = collections.defaultdict(set)
                words_chains_ends = collections.defaultdict(set)

                if chains:
                    for chain_id in chains[i_text]:
                        chain = chains[i_text][chain_id]
                        chains_index[i_text].update(dict((group_id, chain_id) for group_id in chain))

                group_shifts_index = set()

                for i_group, group_id in enumerate(groups[i_text]):
                    group = groups[i_text][group_id]
                    # CoNLL coreference scheme allows only one annotation for a coreference relation
                    # so we need to make sure there are no doubles (there are some in the corpus)
                    if tuple(group['tokens_shifts']) in group_shifts_index:
                        continue
                    group_shifts_index.add(tuple(group['tokens_shifts']))

                    words_chains_starts[self.words_index[i_text][group['tokens_shifts'][0]]].add(group_id)
                    words_chains_ends[self.words_index[i_text][group['tokens_shifts'][-1]]].add(group_id)
                    for word_offset in group['tokens_shifts']:
                        words_chains_index[self.words_index[i_text][word_offset]].append(group_id)

                for i_word, word in enumerate(self.texts[i_text]):
                    coref_mark = '-'
                    if i_word in words_chains_index:
                        group_ids = words_chains_index[i_word]
                        group_starts = [i_word in words_chains_starts and group_id in words_chains_starts[i_word]
                                        for group_id in group_ids]
                        group_ends = [i_word in words_chains_ends and group_id in words_chains_ends[i_word]
                                      for group_id in group_ids]

                        coref_mark = '|'.join('{}{}{}'.format('(' if group_starts[i] else '',
                                                              chains_index[i_text][group_id],
                                                              ')' if group_ends[i] else '')
                                              for i, group_id in enumerate(group_ids))
                    out_file.write(u'{}\t{}\t{}\n{}'.format(doc_name, i_text, coref_mark, '\n' if word.tag == 'SENT' else ''))
                out_file.write('#end document\n')



    def export_brat(self, path):
        """Saves the corpus text and annotation in the BRAT format in the provided path"""
        filename_template='{}.txt'

        if os.path.exists(path) and not os.path.isdir(path):
            raise AttributeError('Provided path ({}) is not a folder'.format(path))
        if not os.path.exists(path):
            os.mkdir(path)

        self.create_indices() # just in case there are no words index yet

        for i_text, text in enumerate(self.texts):
            filename = os.path.join(path, filename_template.format(i_text))
            attr_id = 0
            groups_annotations_ids = {}
            relations = []

            # saving text contents
            with codecs.open(filename, 'w', encoding='utf-8') as out_file:
                cur_offset = 0
                for i_word, word in enumerate(text):
                    n_spaces = word.offset - cur_offset
                    # trying to predict whether that was a new paragraph
                    spaces = ' ' * n_spaces if n_spaces < 3 else '\n' + ' ' * (n_spaces - 1)
                    cur_offset += word.length + n_spaces
                    out_file.write(spaces + ' '.join(word.wordform))

            with codecs.open(filename[:-4] + '.ann', 'w', encoding='utf-8') as out_file:
                mentions = self.get_mentions(i_text)

                for i_group, group in enumerate(mentions):
                    # there is a bug with tokenization of words with some unicode characters in a corpus:
                    # some were tokenized as several consecutive words. In this case we should glue
                    # them without spaces so that offsets are not broken
                    group_wf = u' '.join(group.wordform)
                    if len(group_wf) > group.length:
                        group_wf = ''.join(group.wordform)

                    out_file.write(u'T{ann_id}\tNP {offset} {end}\t{token}\n'.format(ann_id=i_group,
                                                                                     offset=group.offset,
                                                                                     end=group.offset+group.length,
                                                                                     token=group_wf))
                # saving relations
                for i_group, group_id in enumerate(self.gs[i_text]['groups']):
                    group = self.gs[i_text]['groups'][group_id]
                    ann_id = i_group + len(mentions)
                    group_shift = group['tokens_shifts'][0]
                    group_end = group_shift + group['length']
                    group_type = 'DiscNew' if group['parent'] == 0 else 'DiscOld'
                    group_text = self._get_group_text(i_text, group)

                    out_file.write(u'T{ann_id}\t{type} {offset} {end}\t{token}\n'.format(ann_id=ann_id,
                                                                                          offset=group_shift,
                                                                                          end=group_end,
                                                                                          type=group_type,
                                                                                          token=group_text))
                    for attr in group['attributes']:
                        attr_val = group['attributes'][attr] if group['attributes'][attr] else '?'
                        out_file.write(u'A{attr_id}\t{attr} T{ann_id} {val}\n'.format(attr_id=attr_id,
                                                                                     attr=attr,
                                                                                     ann_id=ann_id,
                                                                                     val=attr_val))
                        attr_id += 1

                    groups_annotations_ids[group_id] = ann_id
                    if group['parent'] != 0:
                        relations.append((group_id, group['parent']))

                for i_relation, relation in enumerate(relations):
                    if relation[0] not in groups_annotations_ids or relation[1] not in groups_annotations_ids:
                        self.n_errors['export'] += 1
                        continue

                    arg1 = groups_annotations_ids[relation[0]]
                    arg2 = groups_annotations_ids[relation[1]]
                    out_file.write(u'R{rel_id}\tCoreference Arg1:T{arg_1} Arg2:T{arg_2}\n'.format(rel_id=i_relation,
                                                                                                arg_1=arg1,
                                                                                                arg_2=arg2))

    def _get_group_text(self, i_text, group):
        group_words = [self.texts[i_text][self.words_index[i_text][offset]].wordform[0]
                       for offset in group['tokens_shifts']]
        start_offset = group['tokens_shifts'][0]
        group_text = u''
        for i_word, word in enumerate(group_words[:-1]):
            group_text += word + u' ' * (group['tokens_shifts'][i_word + 1] - group['tokens_shifts'][i_word] - len(word))

        return group_text + group_words[-1]

    def get_mentions(self, i_text):
        """
        Returns a list of NPs if groups are detected or just nouns and pronouns if not
        At this point those are all _possible_ mentions, including singletons and non-referential NPs
        :param i_text: index of a desired text in self.texts
        :return: a list of mentions
        """
        return utils.find_mentions(self.groups[i_text] if self.groups_loaded_ else self.mentions[i_text],
                                   self.tagset)

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

    def score_coreference(self, groups, chains, metric='all', scorer_path='scorer.pl', perl_path='perl'):
        tmp_file_gold = 'tmp_score_rucor_gold.txt'
        tmp_file_test = 'tmp_score_rucor_test.txt'

        rx_metric = re.compile('METRIC ([a-z]+):')
        rx_score = re.compile('([A-Za-z\- ]+): Recall:.* ([0-9\.]+)%\tPrecision:.* ([0-9\.]+)%\tF1:.* ([0-9\.]+)%')

        scorer_params = [perl_path,
                         scorer_path,
                         metric,
                         tmp_file_gold,
                         tmp_file_test,
                         'none']
        self.export_conll(tmp_file_gold)
        self.export_conll(tmp_file_test, groups=groups, chains=chains)

        output = subprocess.check_output(scorer_params).split('\n')

        os.remove(tmp_file_gold)
        os.remove(tmp_file_test)

        scores = collections.defaultdict(dict)
        for line in output:
            line = line.strip('\r\n')
            m = rx_metric.match(line)
            if m:
                metric = m.group(1)
            m = rx_score.match(line)
            if m:
                scores[metric][m.group(1)] = (m.group(2), m.group(3), m.group(4))

        return dict(scores)