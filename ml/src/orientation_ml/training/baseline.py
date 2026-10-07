from sklearn.dummy import DummyClassifier


def make_baseline(random_state: int = 42):
    return DummyClassifier(strategy="prior", random_state=random_state)

