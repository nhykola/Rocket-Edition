# Audit et plan de localisation française

## 1. Périmètre audité et inventaire

Audit statique du dépôt historique complet, sans ROM. Il contient **1 247 scripts XSE `.rbc`** (62 584 lignes). **936 fichiers** possèdent au moins une définition de texte `= ...`, soit **3 634 chaînes sources** cataloguées dans `translation/dialogues_fr.csv`. Les 311 autres scripts sont de la logique ou des fragments sans chaîne. Ce chiffre est exact pour les sources présentes, mais **n'est pas le nombre total des textes de la ROM finale**.

| Emplacement | Texte joueur | Traitement |
|---|---|---|
| `scripts/**/*.rbc`, lignes `= ...` | Dialogues, narration, choix, messages, noms affichés écrits dans les scripts | À traduire via le catalogue |
| ROM de base (absente) | Menus, interface combat, Pokédex, espèces, capacités, objets et descriptions, classes/noms de Dresseurs, lieux, textes système | À extraire/inventorier depuis la ROM anglaise qualifiée |
| `graphics/title screen/main 2 final.png` | Logo « FireRed / Rocket edition / PRESS START » | Actif textuel à adapter puis réinsérer |
| `graphics/bootscreen/bootscreen redux.png` et données associées | Copyright/crédit/URL | Crédit à préserver ; décision éditoriale, probablement sans traduction |
| `graphics/end credits/Tileset64.bmp` + palette | Tuiles des crédits finaux | Inventaire visuel et tilemap/texte final à reconstituer depuis la ROM |
| `readme.md` | Crédits du projet, non nécessairement identique à l'écran | Source de contrôle des crédits, ne pas traduire comme dialogue |
| `doc/*.docx`, notes `.txt`, `offsets.txt`, `vars and flags.xlsx` | Documentation de conception/développement | Technique, jamais injectée ni traduite dans ce chantier |
| `asm/**/*.asm`, `tools/stdmoves.rbh` | Routines, symboles et constantes | Technique, ne jamais traduire |
| autres `graphics/**/*` | Sprites, palettes, décors ; aucun autre texte évident détecté statiquement | Contrôle visuel en jeu encore requis |

Les crédits doivent conserver tous les noms/contributions. Les noms personnalisés contenus dans les scripts sont des textes joueur ; ceux des tables de ROM ne sont pas auditables sans ROM. Les fichiers XSE ne représentent donc pas, à eux seuls, les menus et tables standard ou modifiés.

### Classification d'une ligne XSE

- **Traduisible :** uniquement le contenu humain après `= `, en conservant les éléments structurels.
- **Terminologie :** espèces, capacités, objets, lieux, personnages, grades, concepts ; appliquer `glossary_fr.csv` et les noms officiels vérifiés.
- **Dynamique/opaque :** `[player]`, `[buffer1]`, `[buffer2]`, `[buffer3]`, `[$]`, `[ME]`.
- **Contrôle :** `\\n`, `\\l`, `\\p`, `[.]`, couleurs `[blue_fr]`/`[black_fr]`, séquences `\\c`, `\\h`, `\\w` paramétrées. Les rares `\\I`, `\\a`, `\\y`, `\\F`, `\\G` et `\\\\` restent opaques jusqu'à validation de la table XSE.
- **Jamais traduisible :** tout le reste du script (`#dynamic`, `#include`, `#org`, labels `@...`, commandes, nombres/adresses, constantes, flags/variables, commentaires de maintenance).

Fréquences observées utiles à l'audit initial : `\\n` 6 466, `\\p` 4 828, `[.]` 2 839, `\\l` 2 076, `\\h` 1 276, `\\c` 1 249, `[player]` 446, `[$]` 116, `[buffer1]` 99, `[blue_fr]` 70, `[buffer2]` 36, `[buffer3]` 8, `[black_fr]` 6 et `[ME]` 1. Le validateur compare **la séquence ordonnée des contrôles techniques immuables**, paramètres inclus. Il exclut volontairement `\\n`, `\\l` et `\\p` de cette égalité afin que la mise en page française puisse être recomposée, puis valide séparément l'automate des pages/lignes et leur largeur.

### Encodage et police

Le dépôt mélange **850 fichiers UTF-8 et 397 fichiers Windows-1252**. Une lecture UTF-8 globale corrompt donc les sources. Les glyphes observés ne prouvent pas que tous les accents français soient encodables par XSE ou présents dans la police en ROM. La liste blanche du validateur est provisoire et restrictive ; avant traduction, il faut extraire la table de caractères utilisée par la version finale, mesurer les glyphes et réaliser une ROM-sonde. La mesure actuelle est une approximation par caractère avec seuil conservateur de 198 px, pas une métrique officielle.

## 2. Évaluation des méthodes de construction

### A — Recompiler tous les scripts historiques (non recommandé seul)

Le dépôt **n'est pas un projet de build complet** : aucune ROM/base redistribuable, aucun projet de cartes AdvanceMap, aucune table texte complète, aucune recette ordonnée, aucun binaire XSE et aucune preuve de correspondance source-offset avec la release. Les `#dynamic` demandent une allocation dans une image précise. Rejouer 1 247 compilations risquerait collisions, pointeurs différents et divergences avec les nombreuses modifications réalisées par éditeurs Windows. Cette voie peut servir ponctuellement après qualification d'un compilateur compatible, pas reproduire la ROM finale depuis ce dépôt.

### B — Extraire/repointer depuis une Rocket Edition anglaise (recommandée)

Prendre comme **entrée locale** une release anglaise propre et identifiée par SHA-256. Construire un manifeste des chaînes et pointeurs de la ROM, rapprocher les 3 634 sources par contenu et références, inventorier séparément toutes les tables absentes, puis allouer les textes français en espace libre vérifié et mettre à jour les pointeurs. Cette méthode conserve la logique et les modifications historiques réelles. Elle exige une table de caractères/une police française et une connaissance fiable des pointeurs ; toute écriture doit être bornée et vérifiée avant/après.

### C — Hybride reproductible (cible retenue)

1. `extract_dialogues.py` maintient un catalogue stable sans toucher aux `.rbc`.
2. Un futur analyseur ROM en lecture seule vérifiera le hash, les zones libres, tables et références, et produira un manifeste versionné **sans octets de ROM**.
3. Un injecteur déterministe partira de `--rom /chemin/RocketEdition.gba`, travaillera dans un dossier temporaire ignoré, injectera police/textes/graphismes et produira une ROM locale de test.
4. Tests automatisés, puis tests en émulateur sur dialogues, noms maximaux, choix et scènes.
5. `generate_patch.py` comparera ROM anglaise locale et ROM française locale et publiera uniquement un **BPS**. BPS inclut tailles et CRC, supporte les ROM GBA >16 Mio et ne contient pas une copie autonome exploitable de la ROM.

`build_fr.py` est volontairement un préflight : validation de l'en-tête GBA et affichage du SHA-256, puis arrêt sûr tant que l'injecteur n'est pas qualifié. Il ne prétend pas construire une ROM.

## 3. Arborescence et utilisation

- `translation/dialogues_fr.csv` : catalogue source/cible, label, fichier, encodage et état.
- `translation/canonical/canonical_fr_gen3.csv` : terminologie Pokémon canonique indexée par identifiant ; socle actuel de 4 espèces et 4 capacités explicitement fournies, autres catégories encore incomplètes.
- `translation/canonical/SOURCES.md` : provenance, couverture et protocole d'import vérifiable.
- `translation/glossary_fr.csv` : décisions éditoriales propres à Rocket Edition uniquement.
- `translation/characters_fr.md` : tutoiement, voix et registre.
- `translation/style_guide_fr.md` : règles éditoriales et techniques.
- `translation/progress.json`, `untranslated_report.txt`, `qa_report.md` : sorties reproductibles.
- `tools/localization_common.py`, `extract_dialogues.py`, `validate_dialogues.py`, `validate_terminology.py` : audit ROM-free.
- `tools/build_fr.py` : interface cible et garde-fou.
- `tools/generate_patch.py` : génération BPS locale.

Commandes :

```sh
python3 tools/extract_dialogues.py
python3 tools/validate_dialogues.py
python3 tools/validate_terminology.py
python3 tools/build_fr.py --rom /chemin/RocketEdition.gba
python3 tools/generate_patch.py --source-rom /chemin/english.gba --target-rom /chemin/fr.gba --output /hors/depot/rocket-fr.bps
```

## 4. Contrôles présents et prévus

Le validateur exige désormais l'ensemble **exact** des IDs sources (absents, étrangers et doublons refusés) et protège, dans l'ordre, les contrôles techniques sans absorber le texte adjacent. Les retours `\\n`, `\\l`, `\\p` sont librement réorganisables, mais leur automate impose une structure de boîte valide et la largeur de chaque ligne.

La QA terminologique suit obligatoirement `source EN → détection des IDs → cible FR → présence des équivalents canoniques → anglais résiduel → QA XSE`. **L'absence de terme anglais dans la cible ne suffit pas. Tout terme canonique identifié dans la source doit correspondre à son équivalent français canonique dans la cible.** Les correspondances les plus longues gagnent et ne se chevauchent pas (`Thunder Wave` avant `Thunder`). Les espèces et termes multi-mots sont certains. Une capacité anglaise d'un seul mot est `REVIEW_REQUIRED`, sauf annotation reproductible de la colonne `canonical_ids` (IDs séparés par `;`) ; après annotation, son français canonique exact est bloquant. La compilation XSE réelle et la largeur exacte exigent encore les données ROM/compilateur.

## 5. Blocages à lever avant toute traduction massive

1. Identifier légalement la release anglaise cible par taille et SHA-256 (l'utilisateur fournit son chemin ; aucun hash n'est supposé ici).
2. Obtenir/documenter la table de caractères XSE exacte, la police et les largeurs de glyphes de cette release ; décider comment ajouter les accents manquants.
3. Cartographier toutes les tables texte hors scripts et les chaînes uniquement présentes dans la ROM.
4. Établir la correspondance sûre entre labels sources, pointeurs ROM et chaînes finales, y compris doublons et textes modifiés après compilation.
5. Qualifier espaces libres, alignement, format de pointeur, limites de banques et éventuelle compression.
6. Identifier les outils modernes capables de compiler le dialecte XSE/JPAN, ou spécifier un injecteur dédié testé ; XSE historique seul n'est pas une chaîne reproductible moderne.
7. Reconstituer l'insertion du titre et des crédits (format, palette, tilemap, compression) sans modifier les crédits.
8. Ajouter tests sur émulateur/hardware : rendu des accents, débordements, variables longues, choix, sauvegardes et scènes clés.
9. Valider juridiquement et techniquement que le BPS distribué ne contient que les différences nécessaires ; ne jamais versionner ROM, dump ou sortie de build.

Tant que les points 1 à 5 ne sont pas résolus, l'injection automatique resterait spéculative : l'arrêt explicite du build est une protection, pas une fonctionnalité manquante masquée.
