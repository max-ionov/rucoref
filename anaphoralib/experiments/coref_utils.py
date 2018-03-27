from __future__ import print_function
from __future__ import unicode_literals

import codecs
from .. import utils


def print_chain(chain, groups):
    for elem_id in chain:
        elem = groups[elem_id]
        print (elem)


# TODO: Fixme
def print_chains_in_text(corpus, i_text, test_chains, gold_mentions):
    print('-- SYS --')
    for chain_id in test_chains[i_text]:
        print_chain(test_chains[i_text][chain_id], gold_mentions[i_text])
        print()

    print('\n\n-- GS --')
    for chain_id in corpus.gs[i_text]['chains'].keys():
        gs_mentions, gs_group_ids = get_gs_groups(corpus)
        cur_gs_chain = {key: [gs_group_ids[i_text].index(item) for item in val]
                        for key, val in corpus.gs[i_text]['chains'].items()}
        print_chain(cur_gs_chain[chain_id], gs_mentions[i_text])
        print()


def get_score_table(clf, corpus, mentions, groups, heads_only=False):
    print(r'\textsc{{{}}} & '.format(clf.__class__.__name__), end='')
    scores, _, _ = clf.score(corpus, mentions, groups, metrics=('muc', 'bcub', 'ceafm'), heads_only=heads_only)
    print('${:.2f}$'.format(float(scores['muc']['Identification of Mentions'][2])), end='')
    for metric in ('muc', 'bcub'):
        print(''.join(' & ${:.2f}$'.format(float(score)) for score in scores[metric]['Coreference']), end='')
    print(r' & ${:.2f}$ \\'.format(float(scores['ceafm']['Coreference'][2])))


def dump_groups(groups, filename):
    with codecs.open(filename, 'w', encoding='utf-8') as out_file:
        for i_text, text in enumerate(groups):
            for i_group, group in enumerate(text):
                out_file.write('\t'.join((str(i_text),
                                          str(i_group),
                                          u'|'.join(group.lemma),
                                          u'|'.join(group.wordform),
                                          group.tag,
                                          u'|'.join(group.tags),
                                          group.wordform[group.head],
                                          str(group.offset),
                                          str(group.length)
                                          )))
                out_file.write('\n')


def create_gs_group(group, words, head):
    # words = [text[corpus.words_index[i][shift]] for shift in group['tokens_shifts']]
    # head = text[corpus.words_index[i][group['head_shift'][0]]]
    return utils.Group(wordform=[word.wordform[0] for word in words],
                       lemma=[word.lemma[0] for word in words],
                       tag=head.tag,
                       tags=[word.tag for word in words],
                       prob=1.0,
                       head=words.index(head),
                       words=words,
                       offset=words[0].offset,
                       length=words[-1].offset + words[-1].length - words[0].offset,
                       type='group'
                       )


def get_gs_groups(corpus):
    groups = []
    group_ids = []

    for i, text in enumerate(corpus.texts):
        groups.append([])
        group_ids.append([])
        for group_id in sorted(corpus.gs[i]['groups'],
                               key=lambda g: (corpus.gs[i]['groups'][g]['head_shift'],
                                              len(corpus.gs[i]['groups'][g]['tokens_shifts']))):
            group = corpus.gs[i]['groups'][group_id]
            words = [text[corpus.words_index[i][shift]] for shift in group['tokens_shifts']]
            head = text[corpus.words_index[i][group['head_shift'][0]]]

            groups[-1].append(create_gs_group(group, words, head))
            group_ids[-1].append(group_id)

    return groups, group_ids


def get_pred_groups(corpus, group_ok=lambda g: True):
    groups = []
    group_ids = []

    for i, text in enumerate(corpus.texts):
        groups.append([mention for mention in utils.find_mentions(corpus.groups[i], corpus.tagset)
                       if group_ok(mention)])
        group_ids.append(range(1, len(groups[-1]) + 1))

    return groups, group_ids


def get_pred_groups_gold_boundaries(corpus, group_ok=lambda g: True):
    groups = []
    groups_id = []

    pred_groups, pred_group_ids = get_pred_groups(corpus, group_ok)
    gs_mentions, gs_group_ids = get_gs_groups(corpus)

    for i, text in enumerate(corpus.texts):
        groups.append([])
        groups_id.append([])

        while len(pred_groups[i]) and len(gs_mentions[i]):
            pred_group = pred_groups[i][0]
            gs_group = gs_mentions[i][0]

            # GS is ahead (current NP is before the current GS NP), let's take the predicted mention
            if pred_group.offset + pred_group.length <= gs_group.offset:
                groups[-1].append(pred_group)
                groups_id[-1].append(len(groups[-1]))
                pred_groups[i] = pred_groups[i][1:]
            # Pred is ahead, let's skip the GS
            elif pred_group.offset > gs_group.offset + gs_group.length:
                gs_mentions[i] = gs_mentions[i][1:]
            # there is some overlap, let's take the GS mention
            else:
                groups[-1].append(gs_group)
                groups_id[-1].append(len(groups[-1]))
                gs_mentions[i] = gs_mentions[i][1:]
                pred_groups[i] = pred_groups[i][1:]

        groups_id[-1].extend(range(len(groups[-1]) + 2, len(groups[-1]) + 2 + len(pred_groups[i])))
        groups[-1].extend(pred_groups[i])

    return groups, groups_id
