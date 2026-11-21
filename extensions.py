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
def generer_extensions(theorie, maximum_defauts=12):
    # Le nombre de défauts est limité pour éviter une exploration trop coûteuse.
    if len(theorie.D) > maximum_defauts:
        raise ValueError("Trop de défauts pour cette version.")

    extensions = []  # Extensions valides trouvées jusqu'à présent.

    def explorer(base, appliques):
        """Explorer récursivement les choix possibles depuis une base."""

        # Étape 1 : chercher les défauts non encore utilisés et applicables.
        choix = []
        for numero, defaut in enumerate(theorie.D, start=1):
            if numero not in appliques and applicable(defaut, base):
                choix.append(numero)

        # Étape 2 : si plusieurs défauts sont possibles, essayer chaque choix.
        # Cela explore plusieurs ordres d'application, sans en privilégier un.
        if choix:
            for numero in choix:
                defaut = theorie.D[numero - 1]  # Indices de liste dès 0.
                nouvelle_base = list(base)      # Copie pour ce chemin.

                # Le conséquent n'est ajouté que s'il apporte une nouvelle
                # conséquence logique à la base de ce chemin.
                if not consequence(nouvelle_base, defaut.consequent):
                    nouvelle_base.append(defaut.consequent)

                # Continuer en conservant le numéro du défaut utilisé.
                explorer(nouvelle_base, appliques + [numero])

            # Tous les chemins issus de cette étape ont été explorés.
            return

        # Étape 3 : aucun autre défaut n'est actuellement applicable.
        # Vérifier que les justifications des défauts déjà utilisés restent
        # compatibles avec la base FINALE (elles ont pu être contredites après).
        for numero in appliques:
            defaut = theorie.D[numero - 1]
            if not all(
                est_coherent(base + [j])
                for j in defaut.justifications
            ):
                return  # Chemin invalide : on rejette ce candidat.

        # Étape 4 : vérifier le point fixe de Reiter : Γ(E) = E.
        # La fonction retourne aussi les défauts retenus ; '_' ignore ce retour.
        fermeture, _ = fermeture_relative(theorie, base)

        # On compare les CONSÉQUENCES LOGIQUES, pas les listes mot pour mot.
        if not equivalentes(fermeture, base):
            return  # Ce candidat n'est pas une extension valide.

        # Étape 5 : ne pas conserver deux extensions logiquement équivalentes.
        if not any(equivalentes(base, e.base) for e in extensions):
            extensions.append(
                Extension(
                    base=list(base),
                    defauts_appliques=list(appliques)
                )
            )

    # Départ : uniquement les connaissances certaines W.
    # La base finie W représente initialement Th(W) par ses conséquences.
    explorer(list(theorie.W), [])

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
