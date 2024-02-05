from sklearn.feature_extraction import DictVectorizer

v = DictVectorizer(sparse=False, sort=False)

print(v.fit_transform([
    {'a': False, 'b': False},
    {'a': True},
    {'b': True, 'a': False}
    ]))
