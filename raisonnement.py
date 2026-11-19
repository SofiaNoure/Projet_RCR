
# Importation des connecteurs logiques de SymPy :
# And permet de regrouper plusieurs formules avec un ET logique.
# Not permet de construire la négation d'une formule.
from sympy import And, Not

# satisfiable() vérifie s'il existe au moins une affectation
# des variables qui rend une expression logique vraie.
# Elle retourne False si aucune affectation n'est possible.
from sympy.logic.inference import satisfiable

# Fonctions du fichier formules.py :
# lire_formule() : transforme un texte en objet logique SymPy.
# afficher_formule() : transforme un objet SymPy en texte lisible.
from formules import lire_formule, afficher_formule


# ---------------------------------------------------------
# Fonction 1 : vérifier la cohérence d'un ensemble de formules
# ---------------------------------------------------------

def est_coherent(formules):

    # *formules décompose la liste en arguments séparés.
    # Exemple : [P, Q] devient And(P, Q), soit P ∧ Q.
    # On vérifie ainsi si toutes les formules peuvent être vraies ensemble.
    ensemble = And(*formules)

    # Cherche au moins une affectation qui satisfait l'ensemble.
    # Exemple : P ∧ Q est satisfiable si P = Vrai et Q = Vrai.
    # En revanche, P ∧ ¬P est impossible à satisfaire.
    resultat = satisfiable(ensemble)

    # Si l'ensemble est insatisfaisable, resultat vaut False.
    # S'il est satisfiable, SymPy peut retourner un dictionnaire
    # contenant les valeurs des variables, et pas forcément True.
    # On retourne donc True pour un ensemble cohérent,
    # et False pour un ensemble incohérent.
    return resultat is not False


# ---------------------------------------------------------
# Fonction 2 : vérifier une conséquence logique
# ---------------------------------------------------------

def consequence(formules, formule):

    # formules : ensemble de connaissances W.
    # formule  : conclusion F que l'on souhaite vérifier.
    #
    # Principe de logique classique :
    # W implique F si et seulement si W ∧ ¬F est insatisfaisable.
    #
    # Exemple : W = {P, P -> Q}, et on veut tester Q.
    # On construit P ∧ (P -> Q) ∧ ¬Q.
    # On cherche si W peut être vrai alors que Q est faux.
    ensemble = And(*formules, Not(formule))

    # Si aucune affectation ne satisfait W ∧ ¬F,
    # alors F est nécessairement une conséquence de W.
    #
    # Attention :
    # satisfiable(ensemble) retourne False si c'est impossible.
    # La comparaison "is False" retourne alors True :
    # cela signifie que la conséquence logique est démontrée.
    return satisfiable(ensemble) is False


# ---------------------------------------------------------
# Fonction 3 : trouver un sous-ensemble incohérent minimal
# ---------------------------------------------------------

def sous_ensemble_incoherent(formules):

    # Si l'ensemble initial est cohérent, il n'existe
    # aucune contradiction à isoler : on retourne une liste vide.
    if est_coherent(formules):
        return []

    # On crée une copie de la liste pour ne pas modifier
    # l'ensemble de connaissances d'origine.
    sous_ensemble = list(formules)

    # Indice de la formule que l'on va essayer de retirer.
    i = 0

    # On examine les formules une par une.
    while i < len(sous_ensemble):

        # On construit un candidat sans la formule d'indice i.
        # [:i] récupère les éléments avant i.
        # [i + 1:] récupère les éléments après i.
        #
        # Exemple : [P, P -> Q, ¬Q, R], avec i = 3,
        # donne [P, P -> Q, ¬Q] : on a retiré R.
        candidat = sous_ensemble[:i] + sous_ensemble[i + 1:]

        # Si le candidat reste incohérent après la suppression,
        # la formule retirée n'était pas nécessaire
        # pour conserver cette contradiction.
        if not est_coherent(candidat):

            # On conserve le candidat sans la formule supprimée.
            sous_ensemble = candidat

            # On ne change pas i, car les éléments suivants
            # se sont décalés d'une position dans la liste.
        else:

            # Si le candidat devient cohérent, la formule retirée
            # était nécessaire à la contradiction.
            # On la conserve et on examine la suivante.
            i += 1

    # Retourne un sous-ensemble toujours incohérent,
    # dans lequel aucune formule ne peut être retirée
    # individuellement sans rétablir la cohérence.
    #
    # Il est minimal par inclusion, mais pas nécessairement
    # le plus petit possible en nombre de formules.
    return sous_ensemble


# ---------------------------------------------------------
# Tests : exécutés seulement si ce fichier est lancé directement
# ---------------------------------------------------------

if __name__ == "__main__":

    # TEST W : ensemble cohérent avec une implication.
    # lire_formule() convertit chaque texte en objet SymPy.
    W = [
        lire_formule("P"),
        lire_formule("P -> Q")
    ]

    # W = {P, P -> Q} est cohérent :
    # P = Vrai et Q = Vrai satisfont les deux formules.
    print("W est cohérent :", est_coherent(W))

    # Création des conclusions que l'on souhaite tester.
    Q = lire_formule("Q")
    R = lire_formule("R")

    # W implique Q, car P est vrai et P -> Q impose Q.
    # Résultat attendu : True.
    print("W implique Q :", consequence(W, Q))

    # W n'implique pas R, car R peut être faux sans contredire W.
    # Résultat attendu : False.
    print("W implique R :", consequence(W, R))

    # TEST W2 : ensemble contenant une contradiction indirecte.
    W2 = [
        lire_formule("P"),
        lire_formule("P -> Q"),
        lire_formule("~Q"),
        lire_formule("R")
    ]

    # W2 est incohérent :
    # P et P -> Q imposent Q, mais ~Q impose le contraire.
    # Résultat attendu : False.
    print("W2 est cohérent :", est_coherent(W2))

    # On recherche les formules nécessaires pour conserver
    # la contradiction. Ici, R peut être supprimé.
    incoherent = sous_ensemble_incoherent(W2)

    # Affichage des formules du sous-ensemble trouvé.
    # afficher_formule() convertit les objets SymPy
    # en expressions lisibles : P, (P → Q), ¬Q.
    print("Sous-ensemble incohérent :")
    for f in incoherent:
        print(afficher_formule(f))

    # TEST W3 : monde vide.
    W3 = []

    # Un ensemble vide est cohérent : il ne contient
    # aucune contradiction. Résultat attendu : True.
    print("Monde vide cohérent :", est_coherent(W3))

    # Un ensemble vide n'implique pas P :
    # aucune connaissance n'impose que P soit vrai.
    # Résultat attendu : False.
    print("Monde vide implique P :",
          consequence(W3, lire_formule("P")))

    # TEST W4 : contradiction directe.
    W4 = [
        lire_formule("P"),
        lire_formule("~P")
    ]

    # P et ¬P ne peuvent pas être vrais simultanément.
    # Résultat attendu : False.
    print("W4 est cohérent :", est_coherent(W4))

    # En logique classique, un ensemble incohérent implique
    # n'importe quelle formule : c'est le principe d'explosion.
    #
    # Ici, P ∧ ¬P ∧ ¬Q est insatisfaisable.
    # consequence(W4, Q) retourne donc True,
    # même si Q n'apparaît pas dans W4.
    print("W4 implique Q :",
          consequence(W4, lire_formule("Q")))
