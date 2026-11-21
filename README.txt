Logique des défauts — Mini-projet RCR (USTHB, 4-ING-IA)
=====================================================

Mini_Projet_RCR est une application graphique qui permet de saisir le
monde W et les défauts D, de vérifier la cohérence de W et de calculer
les extensions d'une théorie. Elle teste si une formule est une
conséquence sceptique ou crédule. Les boutons « Enregistrer » et
« Ouvrir » permettent de sauvegarder et de recharger une théorie au
format JSON. Le fichier contient W, D et les extensions : elles sont
réaffichées à l'ouverture et effacées dès que W ou D est modifié.
Le menu « Exemples » propose des théories prêtes à tester.

Le calcul des extensions n’impose aucune limite fixe au nombre de défauts.
Toutefois, certaines théories comportant de nombreux choix contradictoires
peuvent entraîner une exploration exponentielle et prendre beaucoup de temps.

Fonctionnalité supplémentaire (étape 6) : le bouton « Expliquer »
détaille, pour chaque extension, pourquoi chaque défaut est appliqué
ou non (prérequis non démontré, justification contredite…).

Prérequis et installation
-------------------------

Python 3.9 ou plus récent, Tkinter pour l'interface graphique et SymPy
pour le raisonnement logique. Les commandes installent SymPy 1.14.0,
la version utilisée pour les vérifications du projet.

Décompresser le ZIP, puis ouvrir un terminal dans le dossier extrait
qui contient main.py. Créer un environnement Python pour le projet.

macOS et Linux
  python3 -m venv .venv
  .venv/bin/python -m pip install sympy==1.14.0
  .venv/bin/python -m tkinter

Windows
  py -3 -m venv .venv
  .\.venv\Scripts\python.exe -m pip install sympy==1.14.0
  .\.venv\Scripts\python.exe -m tkinter

La dernière commande doit ouvrir une petite fenêtre de test Tkinter.
La fermer avant de poursuivre. Sous Debian ou Ubuntu, si venv ou
Tkinter manque, exécuter « sudo apt install python3-venv python3-tk ».
Sous Windows ou macOS, si Tkinter manque, utiliser une installation
de Python avec Tcl/Tk, par exemple celle de python.org, puis recréer
l'environnement .venv avec cet interpréteur.

Lancer l'application
--------------------

Depuis le même dossier, exécuter la commande correspondant au système.

  macOS et Linux : .venv/bin/python main.py
  Windows       : .\.venv\Scripts\python.exe main.py

Dans PyCharm, ouvrir le dossier qui contient main.py. Dans les réglages
du projet, sélectionner l'interpréteur existant .venv/bin/python
(macOS/Linux) ou .venv\Scripts\python.exe (Windows). Après l'installation
ci-dessus, faire un clic droit sur main.py puis choisir « Run 'main' ».

Premier essai dans l'application
--------------------------------

1. Dans « MONDE W », saisir A dans « Formule » et cliquer sur
   « Ajouter formule ».
2. Dans « DÉFAUTS D », saisir les valeurs suivantes dans les trois
   champs, puis cliquer sur « Ajouter défaut » après chaque ligne.

   Défaut   Prérequis   Justifications   Conséquent
   d1       A           B                C
   d2       A           ~C               ~B

3. Cliquer sur « Générer les extensions ». La zone « RÉSULTATS »
   affiche deux extensions : E1 = Th({A, C}) avec d1 et
   E2 = Th({A, ¬B}) avec d2.
4. Saisir C dans le champ φ. Cliquer sur « Sceptique ? » (NON), puis
   sur « Crédule ? » (OUI). Seule E1 contient C.
5. Cliquer sur « Expliquer ». Pour E1, d1 est appliqué (prérequis A
   démontré, justification B cohérente) et d2 ne l'est pas (sa
   justification ¬C est contredite, car E1 démontre C). C'est l'inverse
   pour E2.

Pour la saisie au clavier, utiliser ~ (non), & (et), | (ou),
-> (implique), <-> (équivaut), true et false. Le prérequis d'un défaut
peut rester vide. Séparer les justifications multiples par des virgules.

Fichiers du projet
------------------

  main.py            Point d'entrée de l'application.
  interface.py       Fenêtre Tkinter et commandes utilisateur.
  formules.py        Lecture et affichage des formules.
  raisonnement.py    Cohérence, conséquence logique et conflits.
  defauts.py         Défauts, théories et sauvegarde ou lecture JSON.
  extensions.py      Calcul des extensions et réponses aux requêtes.
  test_*.py          Scripts de test des modules et de l'interface.
  theorie_test.json  Exemple de théorie sauvegardée.
