#!/usr/bin/python2
# -!- coding: utf-8 -!-

import argparse
import logging
import sys

# temporary measure while there is no package installation
sys.path.append('/media/max/Extension/Projects/Coreference/rucoref')

from anaphoralib.corpora import rueval
from anaphoralib.tagsets import multeast

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('texts', help='CoNLL-like file with tokenized RuCoref corpus')
    parser.add_argument('gs', help='CoNLL-like file with RuCoref annotations')
    parser.add_argument('output')
    parser.add_argument('-v', help='More output', dest='verbose', action='store_true')

    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG if args.verbose else logging.INFO)

    rucoref = rueval.RuCorefCorpus(multeast, rueval)

    logging.info(u'Loading RuCoref texts from {}, GS from {}'.format(args.texts, args.gs))
    logging.debug('Loading texts...')
    rucoref.load_texts(args.texts)
    logging.debug('Loading GS...')
    rucoref.load_gs(args.gs)

    logging.debug('Finding groups...')
    rucoref.find_groups()

    logging.info(u'Exporting to {}'.format(args.output))
    rucoref.export_conll(args.output)