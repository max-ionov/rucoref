#!/usr/bin/python2
# -!- coding: utf-8 -!-

import argparse
import logging
import sys
import re
import codecs

from sklearn import cross_validation

# temporary measure while there is no package installation
sys.path.append('/media/max/Extension/Projects/Coreference/rucoref')

from anaphoralib.corpora import rueval
from anaphoralib.tagsets import multeast

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('texts', help='CoNLL-like file with tokenized RuCoref corpus')
    parser.add_argument('gs', help='CoNLL-like file with RuCoref annotations')
    parser.add_argument('--test-size', '-s',
                        default=0.3,
                        help='the proportion of a test subcorpus',
                        type=float)
    parser.add_argument('--random-state', help='random state for the pseudo-random number generation',
                        type=int,
                        default=None)
    parser.add_argument('-v', help='More output',
                        dest='verbose',
                        action='store_true')

    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG if args.verbose else logging.INFO)

    rucoref = rueval.RuCorefCorpus(multeast, rueval)
    logging.info(u'Loading RuCoref texts from {}, GS from {}'.format(args.texts, args.gs))
    logging.debug('Loading texts...')
    rucoref.load_texts(args.texts)
    logging.debug('Loading GS...')
    rucoref.load_gs(args.gs)

    doc_split = cross_validation.ShuffleSplit(len(rucoref.doc_ids),
                                              n_iter=1,
                                              test_size=args.test_size,
                                              random_state=args.random_state)
    train_set = [rucoref.doc_ids[i] for i in sorted(list(doc_split)[0][0])]
    test_set = [rucoref.doc_ids[i] for i in sorted(list(doc_split)[0][1])]

    logging.debug('Train set ({}): {}'.format(len(train_set), ', '.join(str(i) for i in train_set)))
    logging.debug('Test set ({}): {}'.format(len(test_set), ', '.join(str(i) for i in test_set)))

    rx_txt = re.compile('\\.txt$')

    end_suffix_test = '.test.txt'
    end_suffix_train = '.train.txt'

    out_texts_train = rx_txt.sub(end_suffix_train, args.texts)
    out_gs_train = rx_txt.sub(end_suffix_train, args.gs)

    out_texts_test = rx_txt.sub(end_suffix_test, args.texts)
    out_gs_test = rx_txt.sub(end_suffix_test, args.gs)

    filenames = (('texts', args.texts, out_texts_train, out_texts_test),
                 ('GS', args.gs, out_gs_train, out_gs_test))

    for name, inp_filename, out_filename_train, out_filename_test in filenames:
        logging.info('Saving train and test {}'.format(name))

        out_file_train = codecs.open(out_filename_train, 'w', encoding='utf-8')
        out_file_test = codecs.open(out_filename_test, 'w', encoding='utf-8')

        with codecs.open(inp_filename, encoding='utf-8') as inp_file:
            # writing headers
            line = inp_file.readline()
            out_file_test.write(line)
            out_file_train.write(line)

            for line in inp_file:
                doc_id = int(line.split('\t')[0])
                if doc_id in train_set:
                    out_file_train.write(line)
                else:
                    out_file_test.write(line)
