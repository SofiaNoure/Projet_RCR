LOGIQUE DES DEFAUTS - Mini-projet RCR (USTHB, 4-ING-IA)
=========================================================

Application Python (Tkinter) permettant de :
  1. saisir les formules du monde W et les defauts D ;
  2. generer toutes les extensions de la theorie (W, D) ;
  3. tester si une formule est consequence sceptique ou credule ;
  4. sauvegarder / recharger une theorie (JSON).

INSTALLATION
------------
Prerequis : Python 3.9 ou plus recent.

  pip install sympy

Tkinter est fourni avec Python sous Windows et macOS.
Sous Linux (Debian/Ubuntu) :  sudo apt install python3-tk

LANCEMENT
---------
Depuis le dossier du projet :

  python main.py          (ou python3 main.py)

SYNTAXE DES FORMULES
--------------------
  Connecteur   non   et   ou   implique   equivaut   vrai / faux
  Saisie       ~     &    |    ->         <->        true / false

Propositions et predicats : mots commencant par une majuscule (P, Q, Oiseau(x)).
Variables / constantes (arguments de predicat) : mots en minuscules (x, karim).
Exemple : (P & Q) -> ~R        Oiseau(tweety) -> Vole(tweety)

SAISIE D'UN DEFAUT
------------------
Trois champs : Prerequis, Justifications, Consequent.
 - Les justifications sont separees par des virgules (ex : A, ~B).
 - Le prerequis peut etre vide (defaut sans prerequis  : x / x).
 - Une justification incoherente (ex : x & ~x) donne un avertissement.

UTILISATION
-----------
 - Ajouter formule / defaut : ajoute a la theorie (message d'erreur si syntaxe incorrecte).
 - Supprimer : supprime l'element selectionne dans la liste.
 - Verifier la coherence de W : surligne en rouge un sous-ensemble incoherent.
 - Generer les extensions : affiche chaque extension E1, E2... avec ses litteraux
   et les defauts appliques.
 - Sceptique ? / Credule ? : saisir une formule dans le champ "phi", puis cliquer.
 - Nouveau / Ouvrir / Enregistrer : gestion des fichiers JSON.
 - Exemples : charge des theories pretes a l'emploi (enonce, cours, Tweety, Nixon...).

STRUCTURE DU PROJET
-------------------
  formules.py       lecture / affichage des formules
  raisonnement.py   coherence, consequence logique, sous-ensemble incoherent
  defauts.py        classes Defaut et Theorie, sauvegarde / chargement JSON
  extensions.py     calcul des extensions, consequences sceptiques et credules
  interface.py      interface graphique (aucun calcul logique)
  main.py           point d'entree
  test_raisonnement.py  tests de raisonnement.py
  test_extensions.py    tests de extensions.py
  test_interface.py     test automatique de l'interface

TESTS
-----
  python test_raisonnement.py   tests de la coherence et de la consequence
  python test_extensions.py     tests des extensions, sceptique, credule
  python test_interface.py      test de l'interface (ouvre brievement une fenetre)
Chaque test affiche PASS ou FAIL.
