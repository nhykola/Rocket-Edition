# Guide de localisation française

## Principes éditoriaux

- Employer un français de France naturel et idiomatique. Ne jamais choisir une traduction littérale qui sonne artificielle.
- Conserver fidèlement le sens, l'humour, le sarcasme, les sous-entendus et la personnalité de chacun.
- Rocket Edition a un ton plus adulte et cynique qu'un jeu Pokémon officiel : ne pas l'édulcorer, mais ne jamais ajouter une vulgarité absente de l'original.
- La qualité du français prime sur le mot-à-mot.
- Employer systématiquement les noms français officiels des Pokémon, capacités, objets, lieux, personnages et concepts lorsqu'ils existent. Ne jamais inventer un nom officiel : inscrire `À VÉRIFIER` dans le glossaire en cas de doute.
- Respecter absolument le tutoiement, le vouvoiement et le registre définis dans `characters_fr.md`.

## Contraintes techniques

- Préserver **à l'identique**, dans le même ordre et avec la même casse, chaque variable, placeholder et commande XSE.
- Sont notamment intouchables : `\\n` (nouvelle ligne), `\\l` (ligne suivante/défilement), `\\p` (nouvelle page), `[.]` (temporisation), `[player]`, `[buffer1]`, `[buffer2]`, `[buffer3]`, `[$]`, `[ME]`, les couleurs `[blue_fr]`/`[black_fr]`, ainsi que les séquences paramétrées `\\c`, `\\h`, `\\w` et leurs octets suivants.
- Les rares séquences observées `\\I`, `\\a`, `\\y`, `\\F`, `\\G` et `\\\\` sont à considérer comme opaques tant que leur encodage n'a pas été vérifié : ne pas les corriger visuellement.
- Ne modifier ni labels `#org`, commandes, constantes, adresses, flags, variables, commentaires techniques, ni logique de jeu.
- Ne saisir aucun caractère non confirmé par la table de caractères réelle de la ROM. Les accents français ne seront généralisés qu'après vérification de la police, de la table XSE et du rendu en émulateur.
- Adapter intelligemment la syntaxe aux fenêtres. Cible provisoire : 198 pixels par ligne ; contrôler le rendu réel, les noms dynamiques et les pages.
- Ne pas introduire de retour à la ligne physique dans une définition `= ...` XSE : utiliser les contrôles existants.

## Processus

1. Traduire uniquement la colonne `fr` du catalogue UTF-8 et passer le statut à `traduit`.
2. Exécuter `python3 tools/validate_dialogues.py` ; aucune erreur de token n'est acceptable.
3. Faire relire narration, terminologie et registre ; passer à `relu`, puis `validé` après test en jeu.
4. Ajouter toute décision réutilisable au glossaire ou à la fiche des personnages.

La mesure de largeur actuelle est une approximation conservatrice. Elle ne remplace pas l'extraction des métriques de la police FireRed/Rocket Edition.
