from __future__ import annotations

import random
from typing import List, Optional, Tuple

# Constantes
EMPTY = 0
SUPPORTED_SIZES = (3, 4)

# Directions : le déplacement est celui de la case VIDE.
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

Board = List[List[int]]
State = Tuple[Tuple[int, ...], ...]  # version immuable (hashable) pour l'IA


class Taquin:
    """Représente une partie de Taquin."""

    def __init__(self, size: int = 3, shuffle_moves: Optional[int] = None) -> None:
        """
        :param size: taille de la grille (3 ou 4).
        :param shuffle_moves: nombre de mouvements aléatoires pour mélanger
                              (par défaut : 100 pour 3x3, 200 pour 4x4).
        """
        if size not in SUPPORTED_SIZES:
            raise ValueError(f"Taille non supportée : {size}. Choisir parmi {SUPPORTED_SIZES}.")

        self.size: int = size
        self.shuffle_moves: int = shuffle_moves or (100 if size == 3 else 200)
        self.board: Board = []
        self.initial_board: Board = []
        self.moves: int = 0
        self._history: List[Tuple[Board, int]] = []
        self.new_game()

    # Création / initialisation
    def goal_board(self) -> Board:
        """Retourne la grille résolue."""
        n = self.size
        board = [[r * n + c + 1 for c in range(n)] for r in range(n)]
        board[n - 1][n - 1] = EMPTY
        return board

    def new_game(self, size: Optional[int] = None) -> None:
        """Démarre une nouvelle partie mélangée (taille éventuellement modifiée)."""
        if size is not None:
            if size not in SUPPORTED_SIZES:
                raise ValueError(f"Taille non supportée : {size}.")
            self.size = size
            self.shuffle_moves = 100 if size == 3 else 200

        self.board = self._shuffled_board()
        self.initial_board = [row[:] for row in self.board]
        self.moves = 0
        self._history.clear()

    def restart(self) -> None:
        """Recommence la partie en cours avec le même mélange."""
        self.board = [row[:] for row in self.initial_board]
        self.moves = 0
        self._history.clear()

    def _shuffled_board(self) -> Board:
        """
        Mélange la grille en effectuant des déplacements aléatoires valides à
        partir de l'état résolu. Cela garantit que la grille est TOUJOURS
        résoluble (un mélange complètement aléatoire ne l'est qu'une fois sur deux).
        """
        board = self.goal_board()
        empty = (self.size - 1, self.size - 1)
        previous: Optional[Tuple[int, int]] = None

        for _ in range(self.shuffle_moves):
            candidates = [
                (empty[0] + dr, empty[1] + dc)
                for dr, dc in DIRECTIONS
                if self._in_bounds(empty[0] + dr, empty[1] + dc)
            ]
            # On évite d'annuler immédiatement le coup précédent.
            if previous in candidates and len(candidates) > 1:
                candidates.remove(previous)

            target = random.choice(candidates)
            board[empty[0]][empty[1]] = board[target[0]][target[1]]
            board[target[0]][target[1]] = EMPTY
            previous, empty = empty, target

        # Sécurité : ne jamais renvoyer une grille déjà résolue.
        if board == self.goal_board():
            return self._shuffled_board()
        return board

    # Outils de position
    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def find_empty(self) -> Tuple[int, int]:
        """Retourne la position (ligne, colonne) de la case vide."""
        for r, row in enumerate(self.board):
            for c, value in enumerate(row):
                if value == EMPTY:
                    return r, c
        raise RuntimeError("Grille invalide : aucune case vide.")


    # Déplacements
    def can_move(self, row: int, col: int) -> bool:
        """
        Vérifie si la tuile en (row, col) peut être déplacée,
        c'est-à-dire si elle est adjacente à la case vide.
        """
        if not self._in_bounds(row, col) or self.board[row][col] == EMPTY:
            return False
        er, ec = self.find_empty()
        return abs(er - row) + abs(ec - col) == 1

    def move_tile(self, row: int, col: int) -> bool:
        """
        Déplace la tuile en (row, col) vers la case vide (clic du joueur).

        :return: True si le déplacement a eu lieu, False sinon.
        """
        if not self.can_move(row, col):
            return False
        er, ec = self.find_empty()
        self._history.append(([line[:] for line in self.board], self.moves))
        self.board[er][ec], self.board[row][col] = self.board[row][col], EMPTY
        self.moves += 1
        return True

    def undo_move(self) -> bool:
        """Annule le dernier déplacement valide, s'il y en a un."""
        if not self._history:
            return False
        self.board, self.moves = self._history.pop()
        return True

    def move_direction(self, direction: Tuple[int, int]) -> bool:
        """
        Déplace la case VIDE dans une direction (UP, DOWN, LEFT, RIGHT).
        Pratique pour le clavier (flèches) et pour l'IA.
        """
        er, ec = self.find_empty()
        return self.move_tile_at_offset(er, ec, direction)

    def move_tile_at_offset(self, er: int, ec: int, direction: Tuple[int, int]) -> bool:
        target_r, target_c = er + direction[0], ec + direction[1]
        return self.move_tile(target_r, target_c)

    def get_movable_tiles(self) -> List[Tuple[int, int]]:
        """Liste des positions des tuiles qui peuvent bouger (voisines du vide)."""
        er, ec = self.find_empty()
        return [
            (er + dr, ec + dc)
            for dr, dc in DIRECTIONS
            if self._in_bounds(er + dr, ec + dc)
        ]

    # Victoire
    def is_solved(self) -> bool:
        """Retourne True si la grille est dans l'état final."""
        return self.board == self.goal_board()

    # Interface avec le solveur (Personne 3)
    
    def get_state(self) -> State:
        """Etat courant sous forme immuable (tuple de tuples), utilisable dans un set/dict."""
        return tuple(tuple(row) for row in self.board)

    def get_goal_state(self) -> State:
        """Etat final sous forme immuable."""
        return tuple(tuple(row) for row in self.goal_board())

    def set_state(self, state: State) -> None:
        """Remplace la grille par un état donné (utile pour les tests et l'IA)."""
        board = [list(row) for row in state]
        if len(board) != self.size or any(len(r) != self.size for r in board):
            raise ValueError("Dimensions de l'état incompatibles avec la grille.")
        if sorted(v for row in board for v in row) != list(range(self.size ** 2)):
            raise ValueError("L'état doit contenir chaque valeur de 0 à size²-1 une seule fois.")
        self.board = board
        self._history.clear()

    @staticmethod
    def neighbors(state: State) -> List[State]:
        """
        Retourne tous les états atteignables en un coup depuis `state`.
        Fonction statique : le solveur n'a pas besoin d'une instance de jeu.
        """
        n = len(state)
        er, ec = next((r, c) for r in range(n) for c in range(n) if state[r][c] == EMPTY)
        result: List[State] = []
        for dr, dc in DIRECTIONS:
            nr, nc = er + dr, ec + dc
            if 0 <= nr < n and 0 <= nc < n:
                grid = [list(row) for row in state]
                grid[er][ec], grid[nr][nc] = grid[nr][nc], EMPTY
                result.append(tuple(tuple(row) for row in grid))
        return result

    @staticmethod
    def is_solvable(state: State) -> bool:
        """
        Teste si un état est résoluble (règle des inversions).
        - Grille de taille impaire : nombre d'inversions pair.
        - Grille de taille paire : dépend de la ligne de la case vide.
        """
        n = len(state)
        flat = [v for row in state for v in row if v != EMPTY]
        inversions = sum(
            1 for i in range(len(flat)) for j in range(i + 1, len(flat)) if flat[i] > flat[j]
        )
        if n % 2 == 1:
            return inversions % 2 == 0
        empty_row_from_bottom = n - next(r for r in range(n) if EMPTY in state[r])
        return (inversions + empty_row_from_bottom) % 2 == 1

    # Affichage
    def __str__(self) -> str:
        width = len(str(self.size ** 2 - 1))
        lines = []
        for row in self.board:
            lines.append(" ".join("." * width if v == EMPTY else str(v).rjust(width) for v in row))
        return "\n".join(lines)


# Petite démo en console : python game_logic.py
if __name__ == "__main__":
    jeu = Taquin(3)
    print("Grille initiale :")
    print(jeu)
    print("\nRésoluble :", Taquin.is_solvable(jeu.get_state()))

    while not jeu.is_solved():
        saisie = input(
            "\nLigne et colonne de la tuile (ex: 1 2), u pour annuler, q pour quitter : "
        ).strip()
        if saisie.lower() == "q":
            break
        if saisie.lower() == "u":
            if jeu.undo_move():
                print(f"\nMouvements : {jeu.moves}")
                print(jeu)
            else:
                print("Aucun déplacement à annuler.")
            continue
        try:
            r, c = map(int, saisie.split())
        except ValueError:
            print("Format invalide.")
            continue
        if jeu.move_tile(r, c):
            print(f"\nMouvements : {jeu.moves}")
            print(jeu)
        else:
            print("Déplacement impossible.")

    if jeu.is_solved():
        print(f"\nBravo ! Résolu en {jeu.moves} mouvements.")
