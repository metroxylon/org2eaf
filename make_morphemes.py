import re


def make_morphemes(word):
    # the list replacements contains all the regular expressions for
    # splitting words into morphemes correctly (language specific)
    replacements = [('^ba-', 'ba- '),
                    ('^mə-', 'mə- '),
                    ('=la', ' =la'),
                    ('ʤi=', 'ʤi= '),
                    ('-(\S)', ' -\g<1>'),
                    ('=(\S)', ' =\g<1>')
    ]
    morphs = word
    for rep in replacements:
        morphs = re.sub(rep[0], rep[1], morphs)
    morph_list = morphs.split()
    return morph_list


test_suit = [('mə-ʦaʔ', 'mə- ʦaʔ'),
             ('guu-mə', 'guu -mə'),
             ('ba-dɛN', 'ba- dɛN'),
             ('ʤi=la', 'ʤi =la'),
             ('ʤi=hɛN', 'ʤi= hɛN')
]

for x in test_suit:
    result = make_morphemes(x[0])
    #print(result)

    

def make_same_morpheme_separators(splitted_mb, splitted_gl_or_id, label):
    # returns second list with same separators as first:
    with_separators = []
    if len(splitted_mb) != len(splitted_gl_or_id):
        print("Unequal length in " + label)
    else:
        for morph, annot in zip(splitted_mb, splitted_gl_or_id):
            if morph[0] == '-':
                with_separators.append("-" + annot)
            elif morph[0] == '=':
                with_separators.append("=" + annot)
            elif morph[-1] == '-':
                with_separators.append(annot + "-")
            elif morph[-1] == '=':
                with_separators.append(annot + "=")
            else:
                with_separators.append(annot)
    return with_separators


test_suit = [(['mə-', 'ʦaʔ'], ['NMLZ', 'do'], "SOME00:12"),
             (['ʤi=', 'priN', '-hɛN'], ['ANA', 'human', 'pl'], "SOME00:12")
]

for test in test_suit:
    result = make_same_morpheme_separators(test[0], test[1], test[2])
    #print(result)
    
