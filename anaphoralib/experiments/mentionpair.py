class DisjointSet(object):
    def __init__(self):
        self.leader = {} # maps a member to the group's leader
        self.group = {} # maps a group leader to the group (which is a set)

    def add(self, a, b):
        leadera = self.leader.get(a)
        leaderb = self.leader.get(b)
        if leadera is not None:
            if leaderb is not None:
                if leadera == leaderb: return # nothing to do
                groupa = self.group[leadera]
                groupb = self.group[leaderb]
                if len(groupa) < len(groupb):
                    a, leadera, groupa, b, leaderb, groupb = b, leaderb, groupb, a, leadera, groupa
                groupa |= groupb
                del self.group[leaderb]
                for k in groupb:
                    self.leader[k] = leadera
            else:
                self.group[leadera].add(b)
                self.leader[b] = leadera
        else:
            if leaderb is not None:
                self.group[leaderb].add(a)
                self.leader[a] = leaderb
            else:
                self.leader[a] = self.leader[b] = a
                self.group[a] = {a, b}

# class MentionPairClassifier(object):
#     """
#     A base classifier for mention-pair coreference resolution models
#     Child classifiers may be ML-based, rule-based or even hybrid
#     """
#     def __init__(self):
#         pass
#
#     def _find_mention_pairs(self, mentions):
#         for i_mention, ment_1 in enumerate(mentions):
#             for j_mention, ment_2 in enumerate(mentions[:i_mention]):
#                 yield (j_mention+1, i_mention+1)
#
#     def find_coreferent_pairs(self, mentions):
#         """
#         Generates pairs of coreferent mentions using self.are_coreferent method
#         :param mentions:
#         :return:
#         """
#         return filter(lambda pair: self.pair_coreferent((mentions[pair[0]-1], mentions[pair[1]-1])),
#                       self._find_mention_pairs(mentions))
#
#     def find_coreferent_chains(self, coref_pairs):
#         """
#         Using generated coreferent pairs generates chains
#         :return:
#         """
#         chains = {}
#
#         for pair in coref_pairs:
#             chains_with_elem = [chains[chain] for chain in chains
#                                 if pair[1] in chains[chain] or pair[0] in chains[chain]]
#             if len(chains_with_elem) == 0:
#                 chains[len(chains) + 1] = set()
#                 chains_with_elem.append(chains[len(chains)])
#             chains_with_elem[0].update(pair)
#
#         return {chain_id: sorted(chains[chain_id]) for chain_id in chains}
#
#     def _convert_chains_to_groups(self, coref_chains, mentions):
#         groups = {}
#
#         for i_chain in sorted(coref_chains):
#             for i_group, group_id in enumerate(coref_chains[i_chain]):
#                 parent = coref_chains[i_chain][i_group - 1] if i_group > 0 else 0
#                 group = mentions[group_id-1]
#                 tokens_offsets = [w.offset for w in group.words] if group.type != 'word' else [group.offset]
#                 groups[group_id] = {'parent': parent, 'tokens_shifts': tokens_offsets}
#
#         return groups
#
#     def resolve(self, mentions):
#         """
#         A main entry point for the classifier. Takes a list of mentions and returns clusters of coreference clusters
#         :param mentions: A list of mentions
#         :return: two dicts: a dict with chains and dict with groups (mentions that are involved in coreference)
#         Those dicts and a list of mentions are sufficient to export results in CoNLL or BRAT formats
#         """
#         coref_pairs = self.find_coreferent_pairs(mentions)
#         coref_chains = self.find_coreferent_chains(coref_pairs)
#         coref_groups = self._convert_chains_to_groups(coref_chains, mentions)
#
#         # TODO: return as ResultSet (a child of corpora.base.Corpus)
#         return coref_chains, coref_groups
#
#     def pair_coreferent(self, pair, return_prob=False):
#         """
#         This is the decision function that should be overridden in child classes
#         :param pair: a tuple consisting of two mentions (anaphoralib.utils.Group or anaphoralib.utils.Word)
#         :return: True if mentions are coreferent, False otherwise.
#         If return_prob is True, returns the probability of being coreferent
#         """
#         return False


class MentionPairClassifier(object):
    NEEDS_TRAINING = False

    def __init__(self, scorer_path=None):
        self.scorer_path = scorer_path

    def predict_pairs(self, mentions, groups, words, parse, i_text):
        pairs = []
        discarded_pairs = []
        used_antecedents = set()

        rev_mentions = mentions[::-1]

        for i_mention, mention in enumerate(mentions[1:]):
            for antecedent in rev_mentions[len(rev_mentions) - i_mention - 1:]:
                if antecedent in used_antecedents:
                    continue

                if self.pair_coreferent((antecedent, mention), groups, words, parse):
                    pairs.append((antecedent, mention))
                    used_antecedents.add(antecedent)
                    break
                else:
                    discarded_pairs.append((antecedent, mention))
        return pairs, discarded_pairs

    def convert_chains_to_groups(self, coref_chains, mentions, heads_only=False):
        groups = {}

        for i_chain in sorted(coref_chains.keys()):
            for i_group, group_id in enumerate(coref_chains[i_chain]):
                parent = coref_chains[i_chain][i_group - 1] if i_group > 0 else 0
                group = mentions[group_id]

                if heads_only:
                    tokens_offsets = [group.words[group.head].offset if group.type != 'word' else group.offset]
                else:
                    tokens_offsets = [w.offset for w in group.words] if group.type != 'word' else [group.offset]
                groups[group_id] = {'parent': parent, 'tokens_shifts': tokens_offsets}
        for group_id, group in enumerate(mentions):
            if group_id not in groups:
                if heads_only:
                    tokens_offsets = [group.words[group.head].offset if group.type != 'word' else group.offset]
                else:
                    tokens_offsets = [w.offset for w in group.words] if group.type != 'word' else [group.offset]
                groups[group_id] = {'parent': 0, 'tokens_shifts': tokens_offsets}
                coref_chains['999{}'.format(group_id)] = [group_id]

        return groups

    def resolve(self, mentions, groups, words, parse, i_text, return_heads_only=False):
        pairs, _ = self.predict_pairs(mentions, groups, words, parse, i_text)

        chains_set = DisjointSet()
        chains = {}

        for pair in pairs:
            chains_set.add(mentions.index(pair[0]), mentions.index(pair[1]))
        for i_chain, chain in enumerate(list(chains_set.group.values())):
            chains[i_chain + 1] = sorted(chain)
        groups = self.convert_chains_to_groups(chains, mentions, return_heads_only)

        return chains, groups

    def score(self, corpus, mentions, groups, metrics=('muc',), heads_only=False):
        if not self.scorer_path:
            return {}, [], []

        coref_chains = []
        coref_groups = []

        for i, text in enumerate(corpus.texts):
            text_chains, text_groups = self.resolve(mentions[i], groups[i], corpus.texts[i],
                                                    corpus.parses[i] if corpus.parses else None, i,
                                                    return_heads_only=heads_only)
            coref_chains.append(text_chains)
            coref_groups.append(text_groups)

        scores_dict = {}

        for metric in metrics:
            scores = corpus.score_coreference(coref_groups, coref_chains,
                                              scorer_path=self.scorer_path,
                                              heads_only=heads_only,
                                              metric=metric)[metric]
            scores_dict[metric] = {score: (scores[score][1], scores[score][0], scores[score][2]) for score in scores}

        return scores_dict, coref_groups, coref_chains

    def pair_coreferent(self, pair, groups, words, parse):
        return False
