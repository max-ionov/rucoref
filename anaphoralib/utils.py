#!/usr/bin/python2.7
# -!- coding: utf-8 -!-

class Word(object):
    def __init__(self, wordform, lemma, tag, prob, offset, length):
        self.wordform = wordform if isinstance(wordform, list) else [wordform]
        self.lemma = lemma if isinstance(lemma, list) else [lemma]
        self.tag = tag
        self.tags = [tag]
        self.prob = prob
        self.offset = offset
        self.length = length
        self.head = 0
        self.type = 'word'

    def head_offset(self):
        return self.offset


    def __str__(self):
        return u'{wordform}:{lemma}({tag}, {offset})'.format(lemma=' '.join(self.lemma),
                                                             wordform=' '.join(self.wordform),
                                                             tag=self.tag,
                                                             type=self.type,
                                                             offset=self.offset).encode('utf-8')

    def __repr__(self):
        return u'{wordform}({tag}, {offset})'.format(lemma=' '.join(self.lemma),
                                                     wordform=' '.join(self.wordform),
                                                     tag=self.tag,
                                                     type=self.type,
                                                     offset=self.offset).encode('utf-8')

    def iter_groups(self):
        yield self #(self.offset, self.length, self.tag, True)

class Group(Word):
    def __init__(self, wordform, lemma, tag, tags, prob, offset, length, head, type, words):
        super(Group, self).__init__(wordform, lemma, tag, prob, offset, length)
        self.type = type
        self.tags = tags[:]
        self.words = words[:]
        self.head = head

    def iter_groups(self):
        yield self #(self.offset, self.length, self.tag, True)

        for group in self.words:
            for g in group.iter_groups():
                yield g #g[:-1] + (False,)

    def head_offset(self):
        return self.words[self.head].offset

def try_group(word1, word2, tagset):
    group = None
    head = None
    for agr in tagset.agreement_filters:
        try:
            res = tagset.agreement_filters[agr](word1, word2)
        except IndexError:
            print word1, word2
            raise
        if res:
            group, head = res
            break

    return Group(wordform=word1.wordform + word2.wordform,
                 lemma=word1.lemma + word2.lemma,
                 tag=group,
                 tags=word1.tags + word2.tags,
                 prob=1.0,
                 offset=word1.offset,
                 length=(word2.offset + word2.length) - word1.offset,
                 words=(word1.words if word1.type != 'word' else [word1]) +
                       (word2.words if word2.type != 'word' else [word2]),
                 head=head,
                 type='agr')\
        if group else None


def try_conjunction(word1, conj, word2, tagset):
    tag = tagset.np_conjunction(word1, conj, word2)
    return Group(wordform=word1.wordform + conj.wordform + word2.wordform,
                 lemma=word1.lemma + conj.lemma + word2.lemma,
                 tag=tag,
                 tags=word1.tags + conj.tags + word2.tags,
                 prob=1.0,
                 offset=word1.offset,
                 length=(word2.offset + word2.length) - word1.offset,
                 words=(word1.words if word1.type != 'word' else [word1]) +
                       (conj.words if conj.type != 'word' else [conj]) +
                       (word2.words if word2.type != 'word' else [word2]),
                 head=len(word1.tags),
                 type='conj')\
        if tag else None


def find_groups(text, tagset):
    groups = text[:]
    was_merge = True

    while was_merge:
        was_merge = False
        for i in range(1, len(groups)):
            group = try_group(groups[i - 1], groups[i], tagset)
            if group:
                was_merge = True
                groups.pop(i - 1)
                groups.pop(i - 1)
                groups.insert(i - 1, group)

                break

    #    for i in range(2, len(groups)):
    #        group =  try_conjunction(groups[i-2], groups[i-1], groups[i], tagset)
    #        if group:
    #            was_merge = True
    #            groups.pop(i - 2)
    #            groups.pop(i - 2)
    #            groups.pop(i - 2)
    #            groups.insert(i - 2, group)
    #
    #            break

    return [group for group in groups if group.tag[0].isalpha()]

def find_mentions(text, tagset):
    return [word for word in text
            if tagset.pos_filters['noun'](word)
            or tagset.pos_filters['pronoun'](word)]

def intersects(group1, group2):
    right1 = group1.offset + group1.length
    right2 = group2.offset + group2.length
    return group1.offset <= group2.offset and right1 >= right2 \
        or group2.offset <= group1.offset and right2 >= right1