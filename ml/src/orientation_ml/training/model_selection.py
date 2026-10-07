from sklearn.metrics import f1_score


def select_champion(models, validation_x, validation_y):
    if not models:
        raise ValueError("Aucun candidat entraîné")
    return max(models.items(), key=lambda item: f1_score(validation_y, item[1].predict(validation_x), average="macro"))[0]

