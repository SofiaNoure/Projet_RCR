
from sympy import And, Not
from sympy.logic.inference import satisfiable
from formules import lire_formule, afficher_formule


# Fonction 1 : vérifier la cohérence
def est_coherent(formules):
    ensemble = And(*formules)
    resultat = satisfiable(ensemble)

    return resultat is not False


# Fonction 2 : tester une conséquence logique
def consequence(formules, formule):
    ensemble = And(*formules, Not(formule))

    return satisfiable(ensemble) is False


# Fonction 3 : trouver un sous-ensemble incohérent minimal
def sous_ensemble_incoherent(formules):
    if est_coherent(formules):
        return []

    sous_ensemble = list(formules)
    i = 0

    while i < len(sous_ensemble):
        candidat = sous_ensemble[:i] + sous_ensemble[i + 1:]

        if not est_coherent(candidat):
            sous_ensemble = candidat
        else:
            i += 1

    return sous_ensemble


# Tests
if __name__ == "__main__":
    W = [
        lire_formule("P"),
        lire_formule("P -> Q")
    ]

    print("W est cohérent :", est_coherent(W))

    Q = lire_formule("Q")
    R = lire_formule("R")

    print("W implique Q :", consequence(W, Q))
    print("W implique R :", consequence(W, R))

    W2 = [
        lire_formule("P"),
        lire_formule("P -> Q"),
        lire_formule("~Q"),
        lire_formule("R")
    ]

    print("W2 est cohérent :", est_coherent(W2))

    incoherent = sous_ensemble_incoherent(W2)

    print("Sous-ensemble incohérent :")
    for f in incoherent:
        print(afficher_formule(f))

    # Test 1 : monde vide
    W3 = []

    print("Monde vide cohérent :", est_coherent(W3))
    print("Monde vide implique P :",
          consequence(W3, lire_formule("P")))

    # Test 2 : contradiction directe
    W4 = [
        lire_formule("P"),
        lire_formule("~P")
    ]

    print("W4 est cohérent :", est_coherent(W4))
    print("W4 implique Q :",
          consequence(W4, lire_formule("Q")))
