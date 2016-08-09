import codecs
import collections
from .. import utils
from ..corpora import base

class RuCorefCorpus(base.Corpus):
    def __init__(self, tagset, format):
        super(RuCorefCorpus, self).__init__(tagset, format)
        self.doc_ids = None
        self.gs_doc_ids = None


    def load_texts(self, filename):
        self.texts = []
        self.doc_ids = []

        cur_doc = None

        with (codecs.open(filename, encoding='utf-8')) as inp_file:
            fields = inp_file.readline().strip('\r\n').split('\t')
            for line in inp_file:
                word = {pair[0]: pair[1] for pair in zip(fields, line.strip('\r\n').split('\t'))}
                if int(word['doc_id']) > cur_doc:
                    self.texts.append([])
                    cur_doc = int(word['doc_id'])
                    self.doc_ids.append(cur_doc)
                tag = word['gram']
                if len(tag) == 1:
                    tag += '-----'
                self.texts[-1].append(
                                  utils.Word(wordform=[word['token']],
                                             lemma=[word['lemma']],
                                             tag=tag,
                                             prob=1.0,
                                             offset=int(word['shift']),
                                             length=int(word['length'])))

        self.texts_loaded_ = True


    def load_gs(self, filename):
        self.gs = []
        self.gs_doc_ids = []

        cur_doc = None

        with (codecs.open(filename, encoding='utf-8')) as inp_file:
            fields = inp_file.readline().strip('\r\n').split('\t')
            for line in inp_file:
                word = {pair[0]: pair[1] for pair in zip(fields, line.strip('\r\n').split('\t'))}
                #if not word['variant'] == '1':
                #    continue

                doc_id = int(word['doc_id'])
                group_id = int(word['group_id'])
                chain_id = int(word['chain_id'])

                if doc_id > cur_doc:
                    cur_doc = doc_id
                    self.gs.append({'chains': collections.defaultdict(list), 'groups': collections.defaultdict(list)})
                    self.gs_doc_ids.append(doc_id)

                token_shifts = word['tk_shifts'].split(',')
                tokens = word['content'].split(' ')

                head_shifts = word['hd_shifts'].split(',') if word['hd_shifts'] else token_shifts
                head_tokens = word['head'].split(' ') if word['head'] else tokens

                self.gs[-1]['chains'][chain_id].append(group_id)
                self.gs[-1]['groups'][group_id] = {
                    'parent': int(word['link']),
                    'tokens_shifts': [int(sh) for sh in token_shifts],
                    'tokens_lengths': [len(tok) for tok in tokens],
                    'length': int(word['length']),
                    'attributes': {attr.split(':')[0]: attr.split(':')[1]
                                   for attr in word['attributes'].split('|') if attr},
                    'head_shift': [int(sh) for sh in head_shifts],
                    'head_lengths': [len(tok) for tok in head_tokens]
                }

        self.gs_loaded_ = True

    def create_indices(self):
        super(RuCorefCorpus, self).create_indices()

        self.gs_mapping = []
        self.gs_index = []
        self.chains_index = []

        self.n_errors['gs_mapping'] = 0

        for i, text in enumerate(self.texts):
            self.gs_mapping.append({})
            self.chains_index.append({})

            for chain_id in self.gs[i]['chains']:
                chain = self.gs[i]['chains'][chain_id]
                self.chains_index[-1].update(dict((group_id, chain_id) for group_id in chain))

                for group_id in chain:
                    group_heads = self.gs[i]['groups'][group_id]['head_shift']
                    mention_pairs = [self.mentions_index[i][shift] for shift in group_heads
                                     if shift in self.mentions_index[i]]
                    self.n_errors['gs_mapping'] += len(group_heads) - len(mention_pairs)

                    if len(mention_pairs):
                        self.gs_mapping[-1][group_id] = tuple(mention_pairs)

            self.gs_index.append({self.gs_mapping[i][key][0]: key for key in self.gs_mapping[i]})


def get_sentence_borders(text):
    edges = [0] + [i + 1 for i in range(len(text)) if text.tag == 'SENT']
    return [(edges[i - 1], edges[i]) for i in range(len(edges))]
