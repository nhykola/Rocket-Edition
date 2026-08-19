# Sources de terminologie canonique

## Corpus actif

Le fichier `canonical_fr_gen3.csv` est un **socle minimal**, pas encore le corpus exhaustif. Ses huit valeurs sont celles imposées explicitement par le cahier des charges utilisateur du 19 août 2026 ; elles portent donc la source `user_requirement_2026-08-19`. Aucune autre correspondance n'a été complétée de mémoire ou par traduction automatique.

Couverture actuelle : **4 espèces, 4 capacités, 0 objet, 0 type, 0 talent, 0 lieu, 0 personnage, 0 classe de Dresseur et 0 terme système**. Toutes les catégories autres que ces huit entrées sont incomplètes. Une localisation générale reste interdite jusqu'à l'import et la revue du corpus exhaustif.

## Source structurée prévue

La référence technique retenue est [`eonlynx/pokefirered-multilanguage`](https://github.com/eonlynx/pokefirered-multilanguage). Un import futur doit :

1. utiliser un checkout local dont le commit SHA est consigné ;
2. extraire les tableaux français indexés par constantes `SPECIES_*`, `MOVE_*`, `ITEM_*`, etc. ;
3. conserver pour chaque ligne le dépôt, le SHA, le chemin et l'identifiant interne ;
4. comparer les huit valeurs amorces et refuser toute divergence ;
5. ne jamais importer les dialogues ou le scénario du projet tiers.

L'environnement de cet audit ne permettait pas d'accéder à GitHub (proxy HTTP 403). Le corpus n'a donc **pas** été artificiellement présenté comme une copie de ce dépôt. Cette limite doit être levée avant le pilote de traduction.

## Vérification par ROM française locale

Un futur extracteur acceptera `--reference-rom-fr /chemin/PokemonRougeFeu.gba`, vérifiera son SHA-256 puis comparera ses tables par ID. La ROM restera locale, ne sera ni copiée ni commitée. `rom_display_fr` est volontairement distinct de `french_canonical` : le premier pourra contenir la casse/encodage GBA (`FATAL-FOUDRE`, par exemple), sans supprimer les accents du français sémantique ou narratif.
