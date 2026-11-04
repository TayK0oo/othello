# Explication du projet Othello

## Structure
- `engine.py` : moteur de jeu (règles, bitboards, Zobrist, perft).
- `evals.py` : stratégies d'évaluation + `make_evaluator`.
- `agent.py` : IA (Min-Max/Alpha-Bêta, TT, time-out, itératif).
- `human.py` : joueur humain.
- `harness.py` : `play_game`, export CSV/TXT.
- `cli.py` : partie humain vs IA en terminal.
- `web/` : interface web légère (serveur stdlib + HTML/JS).
- `tests.py` : perft, symétrie, hash.

## Lancer
```bash
python tests.py
python cli.py mixed 1000
python web/server.py 8000   # puis http://localhost:8000
```

## Contrat
Voir `CONTRACT.md` (v1.1). Source de vérité unique entre modules A et B.

## Évaluations
- positionnelle : poids statiques du plateau.
- absolue : différence de pions.
- mobilité : coups possibles + coins.
- mixte : positionnelle (début) -> mobilité (milieu) -> absolue (fin).

## Recherche
Alpha-Bêta avec table de transposition (Zobrist), approfondissement itératif, respect du budget temps, réutilisation du meilleur coup précédent. Deux agents = deux caches distincts.

## Tests de conformité
- perft 1..6 : 4, 12, 56, 244, 1396, 8200.
- antisymétrie des évaluations.
- bornes |eval| < 1000.
- hash incrémental.
- respect du temps (<= 1.10 * budget).