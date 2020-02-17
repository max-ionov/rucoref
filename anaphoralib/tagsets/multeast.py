# -!- coding: utf-8 -!-

"""
This is the recommended way to check against part of speech. Add a lambda-function for the desired POS
and use it in your code in the following way: pos_filters['desired_pos'](word), where word is a list
"""
pos_filters = {
    'noun': lambda x: x.tag.startswith('N') or x.tag.startswith('PP'),
    'adj': lambda x: x.tag.startswith('A'),# or x.tag.startswith('R'),
    'properNoun': lambda x: x.tag.startswith('Np'),
    'pronoun': lambda x: x.tag.startswith('P') and x.tag != 'P-----r',
    'coref_pronoun': lambda x: x.wordform[0].lower() in coref_pronouns and x.tag.startswith('P'),
    'comma': lambda x: x.tag.startswith(','),
    'prep': lambda x: x.tag.startswith('S'),
    'insideQuote': lambda x: x.tag.startswith('Fra') or x.tag.startswith('QuO'),
    'closeQuote': lambda x: x.tag.startswith('Frc'),
    #'firstName': lambda x: x.tag.startswith('N') and x.tag[6] == 'N',
    #'secondName': lambda x: (x.tag.startswith('N') and x.tag[6] in ['F', 'S']) or (
    #    x.tag.startswith('A') and x.tag[5] in ['F', 'S']),  # 'conj': lambda x: x.tag == 'C0' or x.tag == 'Fc'
    'conj': lambda x: x.tag.startswith('C'),
    'quant': lambda x: x.tag.startswith('M'),
    'verb': lambda x: x.tag.startswith('V'),
    'interjection': lambda x: x.tag.startswith('I'),
    'punctuation': lambda x: not x.tag[0].isalpha() or x.tag == 'SENT'
}

agreement_tests = {
    'A+N': lambda adj, noun: noun.tag == 'Nc' or (adj.tag[4] == noun.tag[3] and adj.tag[2] == 'p'),
    'Va+N': lambda verb, noun: verb.tag.startswith('Vmp') and
                               verb.tag[8] == 'f' and
                               (noun.tag == 'Nc' or verb.tag[5] == noun.tag[3]),
    'PradjNoun': lambda pronoun, noun: len(pronoun.tag) > 6 and pronoun.tag[6] == 'a' and pronoun.tag[4] == noun.tag[3],
    'Q+N': lambda quant, noun: quant.tag[1] == 'o' and
                               (quant.tag[3] == noun.tag[3]) or (len(quant.tag) > 3 and quant.tag[3] == '-'),
    'N+NGen': lambda noun, noun_gen: len(noun_gen.tag) > 4 and noun_gen.tag[4] == 'g',
    'QCard+NGen': lambda quant, noun_gen: quant.tag[1] == 'c' and (noun_gen.tag == 'Nc' or noun_gen.tag[4] == 'g'),
    'N+NProper': lambda noun, noun_prop: (noun.tag[1] == 'p' or noun_prop.tag[1] == 'p') and
                                         len(noun.tag) > 1 and len(noun_prop.tag) > 1 and
                                         noun.tag[2:5] == noun_prop.tag[2:5]
}

"""
This is the list of groups which we are trying to extract. To disable any of the groups, just comment it
"""
agreement_filters = {
    'adjNoun': lambda adj, noun: (noun.tag[:], len(adj.tags) + noun.head) if (
        pos_filters['adj'](adj) and
        pos_filters['noun'](noun) and
        agreement_tests['A+N'](adj, noun)) else None,
    'vadjNoun': lambda verb, noun: (noun.tag[:], len(verb.tags) + noun.head) if (
        pos_filters['verb'](verb) and
        pos_filters['noun'](noun) and
        agreement_tests['Va+N'](verb, noun)) else None,
    'pradjNoun': lambda pronoun, noun: (noun.tag[:], len(pronoun.tags) + noun.head) if (
        pos_filters['pronoun'](pronoun) and
        pos_filters['noun'](noun) and
        agreement_tests['PradjNoun'](pronoun, noun)) else None,
    'quantNoun': lambda quant, noun: (noun.tag[:], len(quant.tags) + noun.head) if (
        pos_filters['quant'](quant) and
        pos_filters['noun'](noun) and
        agreement_tests['Q+N'](quant, noun)) else None,
    'quantGen': lambda quant, noun_gen: ('N' + quant.tag[1:], quant.head) if (
        pos_filters['quant'](quant) and
        pos_filters['noun'](noun_gen) and
        agreement_tests['QCard+NGen'](quant, noun_gen)) else None,
    'nounGen': lambda noun, noun_gen: (noun.tag[:], noun.head) if (
        pos_filters['noun'](noun) and
        pos_filters['noun'](noun_gen) and
        agreement_tests['N+NGen'](noun, noun_gen)) else None,
    'nounNounProp': lambda noun, noun_prop: (noun_prop.tag[:], len(noun.tags) + noun_prop.head) if (
        pos_filters['noun'](noun) and
        pos_filters['noun'](noun_prop) and
        agreement_tests['N+NProper'](noun, noun_prop)) else None
}


np_conjunction = lambda word1, conj, word2: 'N{p}-p{c}{a}{c2}'.format(p=word1.tag[1],
                                                                      c=word1.tag[4],
                                                                      a=word1.tag[5],
                                                                      c2=word1.tag[6] if len(word1.tag) > 6 else '') if (
    pos_filters['noun'](word1)
    and pos_filters['noun'](word2)
    and (pos_filters['conj'](conj) or pos_filters['comma'](conj))) else None

features = {
    'N': ['proper', 'gender', 'number', 'case', 'animate', 'case2'],
    'V': ['aux', 'vform', 'tense', 'person', 'number', 'gender', 'voice', 'definiteness', 'aspect', 'case'],
    'A': ['type', 'degree', 'gender', 'number', 'case', 'definiteness'],
    'P': ['type', 'person', 'gender', 'number', 'case', 'synt_type', 'animate']
}


def extract_feature(name, word):
    pos = word.tag[0]
    return word.tag[features[pos].index(name) + 1] \
        if pos in features and name in features[pos] and features[pos].index(name) + 1 < len(word.tag) \
        else None


def is_np_dependency(w1, w2, rel):
    res = True

    # filtering participials
    res &= not pos_filters['verb'](w2)

    # filtering interjections and other useless parts of speech
    res &= not (pos_filters['interjection'](w1) or pos_filters['interjection'](w2))
    res &= not (pos_filters['conj'](w2) and rel in (u'сравнит', u'примыкат'))
    res &= not (w2.tag == 'Q' and rel in (u'огранич',))

    # filtering bad roles
    res &= not rel == u'предик'

    return res


def is_np_head(word):
    return word.tag.startswith('N') or (word.wordform[0].lower() in coref_pronouns and word.tag.startswith('P'))


coref_pronouns = {u"его", u"ее", u"её", u"ей", u"ему", u"ею", u"им", u"ими", u"их",
                  u"которая", u"которого", u"которое", u"которой", u"котором", u"которому", u"которую",
                  u"которые", u"который", u"которым", u"которыми", u"которых",
                  u"него", u"нее", u"неё", u"ней", u"нем", u"нём", u"нему", u"нею", u"ним", u"ними", u"них",
                  u"он", u"она", u"они", u"оно", u"я",
                  u"свое", u"своё", u"своего", u"своей", u"своем", u"своём", u"своему",
                  u"своею", u"свой", u"свои", u"своим", u"своими", u"своих", u"свою",
                  u"своя", u"себе", u"себя", u"собой", u"собою"}
