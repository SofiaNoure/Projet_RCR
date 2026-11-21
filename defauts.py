import json
from dataclasses import dataclass, field
from sympy import true
from formules import lire_formule, afficher_formule
from raisonnement import est_coherent


# ---------------------------------------------------------
# Fonction 1 : séparer les justifications d'un défaut
# ---------------------------------------------------------

# Séparer les justifications sans couper les arguments de P(x,y).
# Exemple : "P(x,y), ~Q" -> ["P(x,y)", "~Q"].
def separer_justifications(texte):

    # Liste dans laquelle on stocke les justifications séparées.
    morceaux = []

    # Indice du début de la justification en cours.
    debut = 0

    # Nombre de parenthèses ouvertes non encore fermées.
    profondeur = 0

    # enumerate() parcourt le texte caractère par caractère
    # et fournit à chaque tour l'indice i et le caractère.
    for i, caractere in enumerate(texte):

        # Une parenthèse ouvrante augmente la profondeur.
        if caractere == "(":
            profondeur += 1

        # Une parenthèse fermante diminue la profondeur.
        elif caractere == ")":
            profondeur -= 1

            # Une profondeur négative signifie qu'une parenthèse
            # a été fermée sans avoir été ouverte.
            if profondeur < 0:
                raise ValueError("Parenthèse fermante inattendue.")

        # On découpe uniquement si la virgule se trouve
        # en dehors des parenthèses (profondeur == 0).
        #
        # Dans P(x,y), la virgule ne sépare pas les justifications.
        # Dans P(x,y), ~Q, la deuxième virgule les sépare.
        elif caractere == "," and profondeur == 0:

            # [:i] récupère le texte entre debut et i (exclu).
            # strip() enlève les espaces inutiles.
            morceaux.append(texte[debut:i].strip())

            # La justification suivante commence après la virgule.
            debut = i + 1

    # À la fin, toutes les parenthèses doivent être fermées.
    if profondeur != 0:
        raise ValueError("Parenthèse non fermée.")

    # Ajouter le dernier morceau, car il n'est pas nécessairement
    # suivi d'une virgule.
    morceaux.append(texte[debut:].strip())

    # Retourner la liste des justifications sous forme de textes.
    return morceaux


# ---------------------------------------------------------
# Classe 1 : représentation d'un défaut
# ---------------------------------------------------------

# Une règle par défaut possède trois parties :
# prérequis : justifications / conséquent.
#
# Exemple : P : Q, R / S.
#
# Le prérequis doit être démontré.
# Les justifications doivent rester compatibles.
# Le conséquent pourra être déduit si le défaut est applicable.

# dataclass génère automatiquement le constructeur de la classe.
@dataclass
class Defaut:

    # Objet SymPy représentant le prérequis.
    prerequis: object

    # Liste d'objets SymPy représentant les justifications.
    # On utilise une liste car un défaut peut en avoir plusieurs.
    justifications: list

    # Objet SymPy représentant le conséquent.
    consequent: object

    # Méthode spéciale appelée automatiquement par str() ou print().
    # Elle transforme l'objet Defaut en texte au format :
    # "prérequis : justification1, justification2 / conséquent".
    def __str__(self):

        # Si le prérequis est la constante true, il est représenté
        # par une chaîne vide : le défaut n'a pas de prérequis explicite.
        #
        # Sinon, on convertit le prérequis en texte réutilisable.
        # Exemple : P devient "P".
        pre = (
            "" if self.prerequis is true
            else afficher_formule(self.prerequis, mode="sauvegarde")
        )

        # On parcourt les justifications et on les convertit en texte.
        # join() rassemble ces textes en les séparant par ", ".
        #
        # Exemple : [Q, Not(R)] -> "Q, ~(R)".
        just = ", ".join(
            afficher_formule(j, mode="sauvegarde")
            for j in self.justifications
        )

        # Convertir le conséquent en texte réutilisable.
        cons = afficher_formule(
            self.consequent, mode="sauvegarde"
        )

        # f-string : rassemble les trois parties du défaut.
        # Exemple : "P : Q, R / S".
        #
        # Si le prérequis est true, pre vaut "".
        return f"{pre} : {just} / {cons}"


# ---------------------------------------------------------
# Fonction 2 : lire un défaut saisi par l'utilisateur
# ---------------------------------------------------------

# Cette fonction fait l'inverse de __str__().
# Elle reçoit un texte et construit un objet Defaut.
#
# Exemple : "P : Q, R / S" -> Defaut(P, [Q, R], S).
def lire_defaut(texte):

    # Vérifier qu'il existe exactement un ":" et un "/".
    # Sinon, le texte ne respecte pas le format attendu.
    if texte.count(":") != 1 or texte.count("/") != 1:
        raise ValueError(
            "Un défaut doit contenir exactement ':' et '/'."
        )

    # Première séparation au niveau de ":".
    # Exemple :
    # pre = "P "
    # reste = " Q, R / S"
    #
    # Le 1 signifie qu'on effectue une seule séparation.
    pre, reste = texte.split(":", 1)

    # Deuxième séparation au niveau de "/".
    # Exemple :
    # just = " Q, R "
    # cons = " S"
    just, cons = reste.split("/", 1)

    # Les justifications et le conséquent sont obligatoires.
    # strip() supprime les espaces pour vérifier qu'ils
    # ne contiennent pas uniquement des espaces.
    if not just.strip() or not cons.strip():
        raise ValueError(
            "Justification et conséquent obligatoires."
        )

    # Séparer les justifications en préservant les virgules
    # présentes dans les arguments de prédicats.
    #
    # Exemple : "Q, R" -> ["Q", "R"].
    justifs = separer_justifications(just)

    # any() vérifie si au moins une justification est vide.
    # Exemple : "Q,,R" produit une justification vide.
    if any(not x for x in justifs):
        raise ValueError("Une justification est vide.")

    # Construire et retourner un objet Defaut.
    #
    # 1. Le prérequis est converti en objet SymPy.
    #    S'il est vide, on utilise la constante true.
    #
    # 2. Chaque justification est convertie en objet SymPy.
    #
    # 3. Le conséquent est converti en objet SymPy.
    return Defaut(
        lire_formule(pre) if pre.strip() else true,
        [lire_formule(x) for x in justifs],
        lire_formule(cons)
    )


# ---------------------------------------------------------
# Fonction 3 : vérifier les justifications d'un défaut
# ---------------------------------------------------------

# Détecter les justifications contradictoires en elles-mêmes.
# Exemple : Q & ~Q est incohérente.
#
# Attention : cette fonction ne vérifie pas si le défaut
# est applicable par rapport aux connaissances W.
def avertissements_defaut(defaut):

    # Compréhension de liste :
    # - parcourir les justifications ;
    # - vérifier chacune avec est_coherent([j]) ;
    # - produire un message uniquement si elle est incohérente.
    #
    # [j] est utilisé car est_coherent() attend une liste.
    # not inverse le résultat : True devient False et inversement.
    #
    # Si toutes les justifications sont cohérentes,
    # la fonction retourne une liste vide [].
    return [
        f"Justification incohérente : {afficher_formule(j)}"
        for j in defaut.justifications
        if not est_coherent([j])
    ]


# ---------------------------------------------------------
# Classe 2 : représentation d'une théorie T = (W, D)
# ---------------------------------------------------------

# W : ensemble des connaissances initiales (objets SymPy).
# D : ensemble des règles par défaut (objets Defaut).
#
# La classe permet d'ajouter des éléments, de les sauvegarder
# dans un fichier JSON et de les recharger.

@dataclass
class Theorie:

    # default_factory=list crée une nouvelle liste vide
    # pour chaque nouvelle théorie.
    #
    # Ainsi, les listes de deux théories différentes
    # ne sont pas partagées.
    W: list = field(default_factory=list)
    D: list = field(default_factory=list)

    # Données d'extensions éventuellement récupérées du JSON.
    # None signifie qu'aucune donnée d'extension n'a été chargée.
    #
    # Leur reconstruction en objets Extension est gérée
    # par extensions.py.
    extensions_sauvegardees: list = None

    # -----------------------------------------------------
    # Méthode 1 : ajouter une connaissance dans W
    # -----------------------------------------------------

    def ajouter_formule(self, texte):

        # Transformer le texte en objet logique SymPy.
        # Exemple : "P -> Q" -> Implies(P, Q).
        formule = lire_formule(texte)

        # Ajouter l'objet SymPy dans W.
        self.W.append(formule)

        # Retourner la formule qui vient d'être ajoutée.
        return formule

    # -----------------------------------------------------
    # Méthode 2 : ajouter une règle par défaut dans D
    # -----------------------------------------------------

    def ajouter_defaut(self, texte):

        # Transformer le texte en objet Defaut.
        # Exemple : "P : Q / R" -> Defaut(P, [Q], R).
        defaut = lire_defaut(texte)

        # Ajouter l'objet Defaut dans D.
        # Cela ne signifie pas que le défaut est déjà appliqué.
        self.D.append(defaut)

        # Retourner le défaut qui vient d'être ajouté.
        return defaut

    # -----------------------------------------------------
    # Méthode 3 : sauvegarder la théorie dans un fichier JSON
    # -----------------------------------------------------

    def enregistrer(self, chemin, extensions=None):

        # Construire un dictionnaire Python contenant W et D.
        #
        # Les objets SymPy ne sont pas directement enregistrés
        # dans le JSON : il faut d'abord les convertir en textes.
        donnees = {
            # Convertir les formules de W en textes compatibles
            # avec lire_formule().
            "W": [
                afficher_formule(f, mode="sauvegarde")
                for f in self.W
            ],

            # str(d) appelle automatiquement la méthode
            # __str__() de chaque objet Defaut.
            "D": [str(d) for d in self.D]
        }

        # Si des données d'extensions ont été fournies,
        # les ajouter également au dictionnaire.
        if extensions is not None:
            donnees["extensions"] = extensions

        # Ouvrir le fichier en mode écriture ("w").
        # Le fichier est créé ou remplacé s'il existe déjà.
        # with le ferme automatiquement après l'écriture.
        with open(chemin, "w", encoding="utf-8") as fichier:

            # json.dump() écrit le dictionnaire dans le fichier.
            # indent=2 : mise en forme avec indentation.
            # ensure_ascii=False : conserve les caractères Unicode.
            json.dump(
                donnees, fichier,
                indent=2, ensure_ascii=False
            )

    # -----------------------------------------------------
    # Méthode 4 : recharger une théorie depuis un fichier JSON
    # -----------------------------------------------------

    # @classmethod permet d'appeler directement :
    # Theorie.charger("theorie_test.json").
    #
    # cls représente la classe Theorie, contrairement à self
    # qui représente une instance de cette classe.
    @classmethod
    def charger(cls, chemin):

        # Ouvrir le fichier en mode lecture ("r").
        # json.load() transforme le contenu JSON
        # en données Python, généralement un dictionnaire.
        with open(chemin, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)

        # Vérifier la structure du fichier :
        # - donnees doit être un dictionnaire ;
        # - W doit être une liste ;
        # - D doit être une liste.
        #
        # isinstance() vérifie le type d'une valeur.
        # get() récupère une clé ou retourne None si elle manque.
        if (
            not isinstance(donnees, dict)
            or not isinstance(donnees.get("W"), list)
            or not isinstance(donnees.get("D"), list)
        ):
            raise ValueError("Fichier de théorie invalide.")

        # Récupérer les éventuelles extensions sauvegardées.
        # Si la clé "extensions" n'existe pas, get() retourne None.
        extensions = donnees.get("extensions")

        # Si les extensions sont présentes, elles doivent
        # être représentées par une liste.
        if extensions is not None and not isinstance(extensions, list):
            raise ValueError("Fichier de théorie invalide (extensions).")

        # cls() crée un nouvel objet Theorie avec W et D vides.
        # Dans notre cas, cls() équivaut à Theorie().
        theorie = cls()

        # Conserver les éventuelles données d'extensions.
        theorie.extensions_sauvegardees = extensions

        # Parcourir les textes sauvegardés dans W.
        #
        # ajouter_formule() appelle lire_formule() pour
        # reconstruire chaque objet SymPy avant de l'ajouter.
        for texte in donnees["W"]:
            theorie.ajouter_formule(texte)

        # Parcourir les textes sauvegardés dans D.
        #
        # ajouter_defaut() appelle lire_defaut() pour
        # reconstruire chaque objet Defaut avant de l'ajouter.
        for texte in donnees["D"]:
            theorie.ajouter_defaut(texte)

        # Retourner la nouvelle théorie entièrement reconstruite.
        return theorie


# ---------------------------------------------------------
# Tests : exécutés uniquement si defauts.py est lancé directement
# ---------------------------------------------------------

if __name__ == "__main__":

    # Créer une théorie vide : W = [] et D = [].
    theorie = Theorie()

    # Ajouter deux connaissances initiales dans W.
    # Chaque texte est transformé en objet SymPy.
    theorie.ajouter_formule("P")
    theorie.ajouter_formule("P -> Q")

    # Ajouter deux défauts dans D.
    #
    # d1 : prérequis Q, justification R, conséquent R.
    d1 = theorie.ajouter_defaut("Q : R / R")

    # d2 : aucun prérequis explicite (true),
    # justifications P(x,y) et ~Q, conséquent R.
    #
    # La virgule de P(x,y) ne doit pas provoquer
    # une séparation incorrecte des justifications.
    d2 = theorie.ajouter_defaut(": P(x,y), ~Q / R")

    # Afficher les connaissances W sous forme de textes
    # compatibles avec l'analyseur.
    print("Monde W :", [
        afficher_formule(f, mode="sauvegarde")
        for f in theorie.W
    ])

    # print() appelle automatiquement __str__() pour les défauts.
    print("Défaut 1 :", d1)
    print("Défaut 2 :", d2)

    # Vérifier la cohérence individuelle des justifications de d1.
    # Ici, R est cohérente : aucun avertissement attendu.
    print("Avertissements :", avertissements_defaut(d1))

    # Enregistrer W et D dans un fichier JSON.
    theorie.enregistrer("theorie_test.json")

    # Lire ce fichier et reconstruire une nouvelle théorie.
    copie = Theorie.charger("theorie_test.json")

    # Vérifier que les deux formules et les deux défauts
    # ont bien été rechargés.
    print(
        "Rechargement réussi :",
        len(copie.W), "formules et",
        len(copie.D), "défauts"
    )