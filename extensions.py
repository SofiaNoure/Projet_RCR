"""Calcul, interrogation et affichage des extensions d'une théorie de défauts.

Une extension est représentée par une BASE FINIE de formules SymPy.
Mathématiquement, elle correspond à la fermeture déductive Th(base).
"""

from dataclasses import dataclass
from sympy import Symbol, Not, true

from raisonnement import est_coherent, consequence
from defauts import Theorie
from formules import lire_formule, afficher_formule, variables


# -----------------------------------------------------------------------------
# 1. Représentation d'une extension
# -----------------------------------------------------------------------------
@dataclass
class Extension:
    base: list              # Formules qui représentent l'extension
    defauts_appliques: list  # Numéros des défauts utilisés pour l'obtenir


# -----------------------------------------------------------------------------
# 2. Vérifier si un défaut est applicable à la base ACTUELLE
# -----------------------------------------------------------------------------
def applicable(defaut, base):
    # Le prérequis doit être une conséquence logique de la base.
    # Il n'a pas besoin d'être écrit explicitement dans la liste.
    prerequis_ok = consequence(base, defaut.prerequis)

    # Chaque justification doit rester compatible avec la base actuelle.
    # Exemple : si la justification est Q, la base ne doit pas démontrer ¬Q.
    justifications_ok = all(
        est_coherent(base + [j])
        for j in defaut.justifications
    )

    # Les deux conditions doivent être vraies pour appliquer le défaut.
    return prerequis_ok and justifications_ok


# -----------------------------------------------------------------------------
# 3. Comparer deux bases par leurs conséquences logiques
# -----------------------------------------------------------------------------
def equivalentes(base1, base2):
    # Une même extension peut être représentée par des listes différentes.
    # Exemple : [P, P -> Q] et [P, P -> Q, Q] ont les mêmes conséquences.
    return (
        # Toutes les formules de base2 doivent être déductibles de base1.
        all(consequence(base1, f) for f in base2)
        # Et inversement : toutes celles de base1 doivent suivre de base2.
        and all(consequence(base2, f) for f in base1)
    )


# -----------------------------------------------------------------------------
# 4. Calculer Γ(E), l'opérateur de Reiter, pour un candidat E donné
# -----------------------------------------------------------------------------
def fermeture_relative(theorie, candidat):
    # On REPART de W pour reconstruire les conséquences autorisées par E.
    # Attention : 'base' évolue ; 'candidat' reste fixe pendant le calcul.
    base = list(theorie.W)
    appliques = []
    changement = True

    # Plusieurs passages peuvent être nécessaires : le conséquent d'un défaut
    # peut rendre le prérequis d'un autre défaut démontrable.
    while changement:
        changement = False

        # Les défauts sont numérotés à partir de 1 pour l'affichage.
        for numero, defaut in enumerate(theorie.D, start=1):
            # Le prérequis se vérifie sur la base reconstruite, qui évolue.
            prerequis_ok = consequence(base, defaut.prerequis)

            # DIFFÉRENCE avec applicable() : on vérifie les justifications
            # par rapport au candidat FINAL E, et non à la base provisoire.
            justifications_ok = all(
                est_coherent(candidat + [j])
                for j in defaut.justifications
            )

            if prerequis_ok and justifications_ok:
                # Mémoriser le numéro du défaut s'il n'y figure pas encore.
                if numero not in appliques:
                    appliques.append(numero)

                # Ajouter son conséquent seulement s'il n'est pas déjà
                # déductible de la base reconstruite.
                if not consequence(base, defaut.consequent):
                    base.append(defaut.consequent)
                    changement = True  # Un autre passage peut être utile.

    # 'base' représente Γ(E) ; 'appliques' contient les défauts retenus.
    return base, appliques


# -----------------------------------------------------------------------------
# 5. Construire puis valider les extensions
# -----------------------------------------------------------------------------
def generer_extensions(theorie):
    """Trouver toutes les extensions, sans limite artificielle de défauts.

    Une théorie complexe peut néanmoins nécessiter un temps de calcul élevé :
    le nombre de chemins possibles est potentiellement exponentiel.
    """
    extensions = []

    # Optimisation sûre : repérer les défauts dont les justifications
    # resteraient cohérentes même si TOUS les conséquents étaient ajoutés.
    # Ces défauts ne pourront pas être bloqués par des applications futures.
    # Si tous les conséquents sont contradictoires entre eux, on n'utilise
    # pas cette optimisation ; l'exploration normale reste correcte.
    tous_les_consequents = list(theorie.W) + [
        d.consequent for d in theorie.D
    ]
    defauts_stables = set()
    if est_coherent(tous_les_consequents):
        for numero, defaut in enumerate(theorie.D, start=1):
            if all(
                est_coherent(tous_les_consequents + [j])
                for j in defaut.justifications
            ):
                defauts_stables.add(numero)

    # Pile explicite : même exploration que la fonction récursive explorer(),
    # mais sans atteindre la limite de récursion de Python.
    # Chaque état contient la base provisoire et les numéros déjà appliqués.
    pile = [(list(theorie.W), [])]
    etats_visites = set()

    while pile:
        base, appliques = pile.pop()
        ensemble_appliques = frozenset(appliques)

        # Appliquer les mêmes défauts dans un autre ordre donne les mêmes
        # conséquences logiques : inutile de réexplorer ce même état.
        if ensemble_appliques in etats_visites:
            continue
        etats_visites.add(ensemble_appliques)

        # Rechercher les défauts applicables à la base actuelle.
        choix = [
            numero
            for numero, defaut in enumerate(theorie.D, start=1)
            if numero not in ensemble_appliques and applicable(defaut, base)
        ]

        # Les défauts "stables" actuellement applicables peuvent être
        # ajoutés ensemble : aucun conséquent futur ne contredira leurs
        # justifications. On évite ainsi d'explorer toutes leurs permutations.
        garantis = [numero for numero in choix if numero in defauts_stables]
        if garantis:
            nouvelle_base = list(base)
            for numero in garantis:
                consequent = theorie.D[numero - 1].consequent
                if not consequence(nouvelle_base, consequent):
                    nouvelle_base.append(consequent)

            pile.append((nouvelle_base, appliques + garantis))
            continue

        if choix:
            # Pour les défauts qui peuvent être bloqués ultérieurement,
            # essayer séparément chaque choix : l'ordre peut être important.
            # reversed() conserve l'ordre habituel d'exploration (d1 d'abord).
            for numero in reversed(choix):
                defaut = theorie.D[numero - 1]
                nouvelle_base = list(base)
                if not consequence(nouvelle_base, defaut.consequent):
                    nouvelle_base.append(defaut.consequent)
                pile.append((nouvelle_base, appliques + [numero]))
            continue

        # Aucun autre défaut applicable : contrôler les justifications
        # des défauts utilisés face à la base FINALE.
        if any(
            not all(
                est_coherent(base + [j])
                for j in theorie.D[numero - 1].justifications
            )
            for numero in appliques
        ):
            continue

        # Condition formelle de Reiter : le candidat doit être un point fixe.
        fermeture, _ = fermeture_relative(theorie, base)
        if not equivalentes(fermeture, base):
            continue

        # Conserver une seule fois les extensions logiquement équivalentes.
        if not any(equivalentes(base, e.base) for e in extensions):
            extensions.append(
                Extension(base=list(base), defauts_appliques=list(appliques))
            )

    return extensions


# -----------------------------------------------------------------------------
# 6. Raisonnements sceptique et crédule
# -----------------------------------------------------------------------------
def sceptique(extensions, formule):
    # Cas spécial : aucune extension trouvée.
    if not extensions:
        return None

    # Sceptique : la formule doit être déductible de TOUTES les extensions.
    return all(
        consequence(e.base, formule)
        for e in extensions
    )


def credule(extensions, formule):
    if not extensions:
        return None

    # Crédule : il suffit d'AU MOINS UNE extension qui démontre la formule.
    return any(
        consequence(e.base, formule)
        for e in extensions
    )


# -----------------------------------------------------------------------------
# 7.  les explications des défauts
# -----------------------------------------------------------------------------
@dataclass
class ExplicationDefaut:
    numero: int     # Numéro du défaut, à partir de 1.
    defaut: object  # Objet Defaut associé.
    applique: bool  # Vrai si le défaut figure parmi ceux de l'extension.
    raisons: list   # Messages expliquant son application ou son blocage.


def expliquer_extension(theorie, extension, nom="E"):
    """Expliquer les défauts dans une extension DÉJÀ calculée.

    Ne construit pas l'extension et n'applique aucun nouveau défaut.
    """
    base = extension.base
    explications = []

    # Parcourir tous les défauts, qu'ils aient été utilisés ou non.
    for numero, defaut in enumerate(theorie.D, start=1):
        prerequis = afficher_formule(defaut.prerequis)

        # Comparaison logique avec 'true' (plus robuste qu'un test de texte).
        sans_prerequis = defaut.prerequis == true

        consequent = afficher_formule(defaut.consequent)
        raisons = []  # Repartir d'une liste vide pour chaque défaut.

        # CAS 1 : ce défaut figure déjà dans les défauts appliqués.
        if numero in extension.defauts_appliques:
            if sans_prerequis:
                raisons.append("pas de prérequis")
            else:
                raisons.append(f"prérequis {prerequis} démontré dans {nom}")

            # Réunir les justifications en un texte séparé par des virgules.
            justifs = ", ".join(
                afficher_formule(j) for j in defaut.justifications
            )
            raisons.append(
                f"justification(s) {justifs} cohérente(s) avec {nom}"
            )

            # Indiquer si le conséquent était déjà déductible de W.
            if consequence(theorie.W, defaut.consequent):
                raisons.append(
                    f"le conséquent {consequent} était déjà conséquence de W"
                )
            else:
                # Cette phrase décrit le résultat, sans prouver que la formule
                # a été physiquement ajoutée à la liste au moment de ce défaut.
                raisons.append(
                    f"le conséquent {consequent} est obtenu dans {nom}"
                )

            explications.append(
                ExplicationDefaut(numero, defaut, True, raisons)
            )
            continue  # Passer au défaut suivant.

        # CAS 2 : défaut non appliqué ; identifier les raisons de son blocage.
        # Le prérequis peut être absent de la liste mais déductible :
        # c'est pour cela qu'on utilise consequence(), pas 'in'.
        if not consequence(base, defaut.prerequis):
            raisons.append(f"prérequis {prerequis} non démontré dans {nom}")

        for j in defaut.justifications:
            texte = afficher_formule(j)

            # Justification contradictoire même prise toute seule.
            if not est_coherent([j]):
                raisons.append(
                    f"justification {texte} incohérente : "
                    f"ce défaut ne peut jamais être appliqué"
                )

            # Justification cohérente seule, mais contredite par l'extension.
            elif not est_coherent(base + [j]):
                contraire = afficher_formule(Not(j))
                raisons.append(
                    f"justification {texte} contredite : "
                    f"{nom} démontre {contraire}"
                )

        # Message de secours (par exemple si les informations sont incomplètes).
        if not raisons:
            raisons.append("conditions d'application non remplies")

        explications.append(
            ExplicationDefaut(numero, defaut, False, raisons)
        )

    return explications


# -----------------------------------------------------------------------------
# 8. Transformer les extensions pour la sauvegarde / le chargement JSON
# -----------------------------------------------------------------------------
def extensions_vers_donnees(extensions):
    # Objets Extension + formules SymPy -> listes et dictionnaires simples.
    # On transforme chaque formule en texte ASCII lisible par lire_formule().
    return [
        {
            "base": [
                afficher_formule(f, mode="sauvegarde")
                for f in e.base
            ],
            "defauts_appliques": list(e.defauts_appliques)
        }
        for e in extensions
    ]


def extensions_depuis_donnees(donnees):
    # Opération inverse : données du JSON -> objets Extension.
    resultat = []

    for element in donnees:
        # Contrôler la structure minimale attendue dans le fichier.
        if (
            not isinstance(element, dict)
            or not isinstance(element.get("base"), list)
            or not isinstance(element.get("defauts_appliques"), list)
        ):
            raise ValueError("Extension invalide dans le fichier.")

        # Les numéros de défauts sont des entiers positifs (pas des booléens).
        if not all(
            type(n) is int and n >= 1
            for n in element["defauts_appliques"]
        ):
            raise ValueError("Défauts appliqués invalides dans le fichier.")

        # Reconvertir chaque texte en formule SymPy avec lire_formule().
        resultat.append(
            Extension(
                [lire_formule(texte) for texte in element["base"]],
                list(element["defauts_appliques"])
            )
        )

    return resultat


# -----------------------------------------------------------------------------
# 9. Retrouver les littéraux démontrables dans une extension
# -----------------------------------------------------------------------------
def litteraux(extension):
    base = extension.base

    # Une base incohérente démontrerait toutes les formules classiques ;
    # on évite donc d'en extraire une liste trompeuse de littéraux.
    if not est_coherent(base):
        return []

    resultat = []

    # Chercher toutes les variables présentes dans les formules de la base.
    for nom in variables(base):
        symbole = Symbol(nom)  # Exemple : la chaîne "P" devient le symbole P.

        # Essayer d'abord le littéral positif P.
        if consequence(base, symbole):
            resultat.append(afficher_formule(symbole))

        # Sinon, essayer le littéral négatif ¬P.
        elif consequence(base, ~symbole):
            resultat.append(afficher_formule(~symbole))

        # Si ni P ni ¬P ne sont démontrables, on n'ajoute rien.
    return resultat


# -----------------------------------------------------------------------------
# 10. Savoir QUELLES extensions démontrent une formule
# -----------------------------------------------------------------------------
def extensions_contenant(extensions, formule):
    # Renvoie leurs numéros : ex. [1, 3] pour une formule déduite de E1 et E3.
    # N'affiche rien automatiquement ; utiliser print() pour voir le résultat.
    return [
        i for i, e in enumerate(extensions, start=1)
        if consequence(e.base, formule)
    ]


# -----------------------------------------------------------------------------
# 11. Calculer ET afficher les extensions d'une théorie
# -----------------------------------------------------------------------------
def afficher_extensions(theorie):
    # Cette fonction appelle le véritable moteur de calcul.
    resultat = generer_extensions(theorie)

    print("Nombre d'extensions :", len(resultat))

    for i, extension in enumerate(resultat, start=1):
        # Afficher la base finie de Ei (et non toutes ses conséquences).
        print(
            f"E{i} :",
            [afficher_formule(f) for f in extension.base]
        )

        # Afficher les numéros des défauts utilisés pour Ei.
        print(
            "Défauts appliqués :",
            extension.defauts_appliques
        )

    # Retourner aussi les objets pour sceptique(), credule(), etc.
    return resultat


# -----------------------------------------------------------------------------
# 12. Exemples de test 
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Exemple de la diapositive 18.
    print("=== EXEMPLE SLIDE 18 ===")

    theorie1 = Theorie()
    theorie1.ajouter_formule("A")
    theorie1.ajouter_defaut("A : B / C")
    theorie1.ajouter_defaut("A : ~C / ~B")

    resultat1 = afficher_extensions(theorie1)

    print(
        "C sceptique :",
        sceptique(resultat1, lire_formule("C"))
    )
    print(
        "C crédule :",
        credule(resultat1, lire_formule("C"))
    )

    # Exemple de la diapositive 21.
    print("\n=== EXEMPLE SLIDE 21 ===")

    theorie2 = Theorie()
    theorie2.ajouter_defaut(": A / B")
    theorie2.ajouter_defaut(": C / ~A")

    resultat2 = afficher_extensions(theorie2)

    print(
        "B sceptique :",
        sceptique(resultat2, lire_formule("B"))
    )
