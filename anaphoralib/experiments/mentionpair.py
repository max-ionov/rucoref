


class MentionPairClassifier(object):
    """
    A base classifier for mention-pair coreference resolution models
    Child classifiers may be ML-based, rule-based or even hybrid
    """
    def __init__(self):
        pass

    def _find_mention_pairs(self, mentions):
        for i_mention, ment_1 in enumerate(mentions):
            for j_mention, ment_2 in enumerate(mentions[:i_mention]):
                yield (j_mention+1, i_mention+1)

    def find_coreferent_pairs(self, mentions):
        """
        Generates pairs of coreferent mentions using self.are_coreferent method
        :param mentions:
        :return:
        """
        return filter(lambda pair: self.pair_coreferent((mentions[pair[0]-1], mentions[pair[1]-1])),
                      self._find_mention_pairs(mentions))

    def find_coreferent_chains(self, coref_pairs):
        """
        Using generated coreferent pairs generates chains
        :return:
        """
        chains = {}

        for pair in coref_pairs:
            chains_with_elem = [chains[chain] for chain in chains if pair[1] in chains[chain] or pair[0] in chains[chain]]
            if len(chains_with_elem) == 0:
                chains[len(chains) + 1] = set()
                chains_with_elem.append(chains[len(chains)])
            chains_with_elem[0].update(pair)

        return {chain_id: sorted(chains[chain_id]) for chain_id in chains}

    def _convert_chains_to_groups(self, coref_chains, mentions):
        groups = {}

        for i_chain in sorted(coref_chains):
            for i_group, group_id in enumerate(coref_chains[i_chain]):
                parent = coref_chains[i_chain][i_group - 1] if i_group > 0 else 0
                group = mentions[group_id-1]
                tokens_offsets = [w.offset for w in group.words] if group.type != 'word' else [group.offset]
                groups[group_id] = {'parent': parent, 'tokens_shifts': tokens_offsets}

        return groups

    def resolve(self, mentions):
        """
        A main entry point for the classifier. Takes a list of mentions and returns clusters of coreference clusters
        :param mentions: A list of mentions
        :return: two dicts: a dict with chains and dict with groups (mentions that are involved in coreference)
        Those dicts and a list of mentions are sufficient to export results in CoNLL or BRAT formats
        """
        coref_pairs = self.find_coreferent_pairs(mentions)
        coref_chains = self.find_coreferent_chains(coref_pairs)
        coref_groups = self._convert_chains_to_groups(coref_chains, mentions)

        # TODO: return as ResultSet (a child of corpora.base.Corpus)
        return coref_chains, coref_groups

    def pair_coreferent(self, pair):
        """
        This is the deciding function that should be overridden in child classes
        :param pair: a tuple consisting of two mentions (anaphoralib.utils.Group or anaphoralib.utils.Word)
        :return: True if mentions are coreferent, False otherwise
        """
        return False
