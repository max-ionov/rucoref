
def same_grammemmes(name, words, tagset):

    feature_values = [tagset.extract_feature(name, word) for word in words]
    if None in feature_values:
        feature_values.remove(None)
    if '-' in feature_values:
        feature_values.remove('-')

    return len(set(feature_values)) == 1