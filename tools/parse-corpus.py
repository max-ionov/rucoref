#!/usr/bin/python2
# -!- coding: utf-8 -!-

import codecs
import argparse
import logging
import subprocess
import shlex

tmp_inp_file = 'tmp_inp_file.txt'
tmp_out_file = 'tmp_out_file.txt'
malt_template = 'java -jar {malt_name} -c {model_name} -i {inp_file} -o {out_file} -m parse'

# For now we will use the model trained on the same tags. But in the future we may need this


def convert_pos(pos):
    return pos


def convert_gram(gram):
    return gram


def parse_document(malt_command, doc_id, lines):
    logging.info('Parsing document {}...'.format(doc_id))
    with codecs.open(tmp_inp_file, 'w', encoding='utf-8') as out_file:
        for i, line in enumerate(lines):
            out_file.write(u'{n}\t{wform}\t{lemma}\t{POS}\t{POS}\t{gram}\n'.format(n=i,
                                                                                   wform=line['token'],
                                                                                   lemma=line['lemma'],
                                                                                   POS=convert_pos(line['gram'][0]),
                                                                                   gram=convert_gram(line['gram'])))
            if line['gram'] == 'SENT':
                out_file.write('\n')
    malt_output = subprocess.check_output(malt_command, stderr=subprocess.STDOUT)
    logging.debug(malt_output)
    logging.info('done!')

    cur_word_offset = 0
    n_words_in_sent = 0
    results = []
    with codecs.open(tmp_out_file, encoding='utf-8') as inp_file:
        for line in inp_file:
            line = line.strip('\r\n')

            if not line:
                cur_word_offset += n_words_in_sent
                n_words_in_sent = 0
                continue
            fields = line.split('\t')
            head = str(int(fields[-4]) + cur_word_offset) if fields[-4] != '0' else '0'
            rel = fields[-3]
            n_words_in_sent += 1

            results.append((head, rel))

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', help='a path to the MaltParser model file', required=True)
    parser.add_argument('-j', '--jar', help='a path to the MaltParser jar executable', required=True)
    parser.add_argument('texts', help='CoNLL-like file with tokenized RuCoref corpus')
    parser.add_argument('output', help='initial file with dependency parsing information')
    parser.add_argument('-v', help='More output', dest='verbose', action='store_true')

    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG if args.verbose else logging.INFO)

    cur_doc = None
    lines = []

    global_out_file = codecs.open(args.output, 'w', encoding='utf-8')
    malt_command = malt_template.format(malt_name=args.jar,
                                        model_name=args.model,
                                        inp_file=tmp_inp_file,
                                        out_file=tmp_out_file)
    malt_command = shlex.split(malt_command)

    with codecs.open(args.texts, encoding='utf-8') as inp_file:
        fields = inp_file.readline().strip('\n\r').split('\t')
        concatenated_output = lambda lines, parsed_output: (
            '\t'.join([line[field] for field in fields] + list(parsed_output[i])) for i, line in enumerate(lines))

        global_out_file.write(u'\t'.join(fields) + '\thead\trel\n')
        for line in inp_file:
            line = line.strip('\r\n')
            if not line:
                continue
            values = {pair[0]: pair[1] for pair in zip(fields, line.split('\t'))}
            if cur_doc != values['doc_id']:
                if lines:
                    global_out_file.write('\n'.join(concatenated_output(lines,
                                                                        parse_document(malt_command, cur_doc, lines))))
                    global_out_file.write('\n')

                # new document
                out_file = codecs.open(tmp_inp_file, 'w', encoding='utf-8')
                cur_doc = values['doc_id']
                lines = []

            lines.append(values)

        if lines:
            parses = parse_document(malt_command, cur_doc, lines)
            global_out_file.write('\n'.join(concatenated_output(lines,
                                                                parses)))
