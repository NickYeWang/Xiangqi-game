#!/usr/bin/env python3
"""
轻量级中国象棋引擎 - Python实现
基于Minimax + Alpha-Beta剪枝
作为Pikafish的备选方案
"""

import random
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class PieceType(Enum):
    EMPTY = 0
    KING = 1      # 将/帅
    ADVISOR = 2   # 士/仕
    ELEPHANT = 3  # 象/相
    HORSE = 4     # 马
    ROOK = 5      # 车
    CANNON = 6    # 炮
    PAWN = 7      # 卒/兵

@dataclass
class Piece:
    piece_type: PieceType
    is_red: bool  # True=红方(下方), False=黑方(上方)
    
    def __str__(self):
        chars = {
            PieceType.KING: 'K' if self.is_red else 'k',
            PieceType.ADVISOR: 'A' if self.is_red else 'a',
            PieceType.ELEPHANT: 'B' if self.is_red else 'b',
            PieceType.HORSE: 'N' if self.is_red else 'n',
            PieceType.ROOK: 'R' if self.is_red else 'r',
            PieceType.CANNON: 'C' if self.is_red else 'c',
            PieceType.PAWN: 'P' if self.is_red else 'p',
            PieceType.EMPTY: '.'
        }
        return chars[self.piece_type]

class XiangqiEngineSimple:
    """简化版中国象棋引擎"""
    
    # 棋子基础价值
    PIECE_VALUES = {
        PieceType.KING: 10000,
        PieceType.ROOK: 900,
        PieceType.HORSE: 400,
        PieceType.CANNON: 450,
        PieceType.ELEPHANT: 200,
        PieceType.ADVISOR: 200,
        PieceType.PAWN: 100,
        PieceType.EMPTY: 0
    }
    
    # 位置加成（简化版）
    PAWN_POS_BONUS = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [10, 10, 10, 20, 20, 20, 10, 10, 10],  # 过河后价值提升
        [20, 20, 20, 30, 30, 30, 20, 20, 20],
        [30, 30, 30, 40, 40, 40, 30, 30, 30],
        [40, 40, 40, 50, 50, 50, 40, 40, 40],
        [50, 50, 50, 60, 60, 60, 50, 50, 50],
        [60, 60, 60, 70, 70, 70, 60, 60, 60],
        [70, 70, 70, 80, 80, 80, 70, 70, 70],
    ]
    
    DIFFICULTY_LEVELS = {
        1: {"name": "入门", "depth": 2, "randomness": 0.3},
        2: {"name": "业余", "depth": 3, "randomness": 0.1},
        3: {"name": "高手", "depth": 4, "randomness": 0},
        4: {"name": "大师", "depth": 5, "randomness": 0},
    }
    
    def __init__(self):
        self.board = [[Piece(PieceType.EMPTY, True) for _ in range(9)] for _ in range(10)]
        self.difficulty = 2
        self.move_history = []
        self.init_board()
    
    def init_board(self):
        """初始化棋盘"""
        # 黑方（上方）
        self.board[0] = [
            Piece(PieceType.ROOK, False), Piece(PieceType.HORSE, False),
            Piece(PieceType.ELEPHANT, False), Piece(PieceType.ADVISOR, False),
            Piece(PieceType.KING, False), Piece(PieceType.ADVISOR, False),
            Piece(PieceType.ELEPHANT, False), Piece(PieceType.HORSE, False),
            Piece(PieceType.ROOK, False)
        ]
        self.board[2][1] = Piece(PieceType.CANNON, False)
        self.board[2][7] = Piece(PieceType.CANNON, False)
        for i in [0, 2, 4, 6, 8]:
            self.board[3][i] = Piece(PieceType.PAWN, False)
        
        # 红方（下方）
        self.board[9] = [
            Piece(PieceType.ROOK, True), Piece(PieceType.HORSE, True),
            Piece(PieceType.ELEPHANT, True), Piece(PieceType.ADVISOR, True),
            Piece(PieceType.KING, True), Piece(PieceType.ADVISOR, True),
            Piece(PieceType.ELEPHANT, True), Piece(PieceType.HORSE, True),
            Piece(PieceType.ROOK, True)
        ]
        self.board[7][1] = Piece(PieceType.CANNON, True)
        self.board[7][7] = Piece(PieceType.CANNON, True)
        for i in [0, 2, 4, 6, 8]:
            self.board[6][i] = Piece(PieceType.PAWN, True)
    
    def set_difficulty(self, level: int) -> bool:
        if level in self.DIFFICULTY_LEVELS:
            self.difficulty = level
            return True
        return False
    
    def get_difficulty_info(self) -> str:
        d = self.DIFFICULTY_LEVELS[self.difficulty]
        return f"难度{self.difficulty} ({d['name']}): 深度{d['depth']}"
    
    def is_valid_pos(self, r: int, c: int) -> bool:
        return 0 <= r < 10 and 0 <= c < 9
    
    def get_moves(self, r: int, c: int) -> List[Tuple[int, int]]:
        """获取指定位置的所有合法走法"""
        piece = self.board[r][c]
        if piece.piece_type == PieceType.EMPTY:
            return []
        
        moves = []
        is_red = piece.is_red
        
        if piece.piece_type == PieceType.ROOK:
            # 车：直线移动
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                while self.is_valid_pos(nr, nc):
                    if self.board[nr][nc].piece_type == PieceType.EMPTY:
                        moves.append((nr, nc))
                    else:
                        if self.board[nr][nc].is_red != is_red:
                            moves.append((nr, nc))
                        break
                    nr += dr
                    nc += dc
        
        elif piece.piece_type == PieceType.HORSE:
            # 马：日字
            for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                nr, nc = r + dr, c + dc
                if self.is_valid_pos(nr, nc):
                    # 检查绊马腿
                    block_r, block_c = r + dr//2, c + dc//2
                    if abs(dr) == 2:
                        block_c = c
                    else:
                        block_r = r
                    if self.board[block_r][block_c].piece_type == PieceType.EMPTY:
                        if self.board[nr][nc].piece_type == PieceType.EMPTY or self.board[nr][nc].is_red != is_red:
                            moves.append((nr, nc))
        
        elif piece.piece_type == PieceType.ELEPHANT:
            # 象：田字，不能过河
            river_limit = 4 if is_red else 5
            for dr, dc in [(-2,-2), (-2,2), (2,-2), (2,2)]:
                nr, nc = r + dr, c + dc
                if self.is_valid_pos(nr, nc):
                    # 不能过河
                    if is_red and nr < 5:
                        continue
                    if not is_red and nr > 4:
                        continue
                    # 检查象眼
                    block_r, block_c = r + dr//2, c + dc//2
                    if self.board[block_r][block_c].piece_type == PieceType.EMPTY:
                        if self.board[nr][nc].piece_type == PieceType.EMPTY or self.board[nr][nc].is_red != is_red:
                            moves.append((nr, nc))
        
        elif piece.piece_type == PieceType.ADVISOR:
            # 士：斜线，九宫格内
            palace_r = [7, 8, 9] if is_red else [0, 1, 2]
            palace_c = [3, 4, 5]
            for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                nr, nc = r + dr, c + dc
                if nr in palace_r and nc in palace_c:
                    if self.board[nr][nc].piece_type == PieceType.EMPTY or self.board[nr][nc].is_red != is_red:
                        moves.append((nr, nc))
        
        elif piece.piece_type == PieceType.KING:
            # 将/帅：直线，九宫格内
            palace_r = [7, 8, 9] if is_red else [0, 1, 2]
            palace_c = [3, 4, 5]
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if nr in palace_r and nc in palace_c:
                    if self.board[nr][nc].piece_type == PieceType.EMPTY or self.board[nr][nc].is_red != is_red:
                        moves.append((nr, nc))
            # 将帅对面
            kr, kc = self.find_king(not is_red)
            if kc == c:
                blocked = False
                for i in range(min(r, kr)+1, max(r, kr)):
                    if self.board[i][c].piece_type != PieceType.EMPTY:
                        blocked = True
                        break
                if not blocked:
                    moves.append((kr, kc))
        
        elif piece.piece_type == PieceType.CANNON:
            # 炮：直线，跳吃
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                jumped = False
                while self.is_valid_pos(nr, nc):
                    if not jumped:
                        if self.board[nr][nc].piece_type == PieceType.EMPTY:
                            moves.append((nr, nc))
                        else:
                            jumped = True
                    else:
                        if self.board[nr][nc].piece_type != PieceType.EMPTY:
                            if self.board[nr][nc].is_red != is_red:
                                moves.append((nr, nc))
                            break
                    nr += dr
                    nc += dc
        
        elif piece.piece_type == PieceType.PAWN:
            # 兵/卒
            direction = -1 if is_red else 1  # 红方向上(行号减小)，黑方向下
            
            # 向前
            nr, nc = r + direction, c
            if self.is_valid_pos(nr, nc):
                if self.board[nr][nc].piece_type == PieceType.EMPTY or self.board[nr][nc].is_red != is_red:
                    moves.append((nr, nc))
            
            # 过河后可以左右移动
            crossed = (is_red and r <= 4) or (not is_red and r >= 5)
            if crossed:
                for dc in [-1, 1]:
                    nr, nc = r, c + dc
                    if self.is_valid_pos(nr, nc):
                        if self.board[nr][nc].piece_type == PieceType.EMPTY or self.board[nr][nc].is_red != is_red:
                            moves.append((nr, nc))
        
        return moves
    
    def find_king(self, is_red: bool) -> Tuple[int, int]:
        """查找指定方的将/帅位置"""
        for r in range(10):
            for c in range(9):
                piece = self.board[r][c]
                if piece.piece_type == PieceType.KING and piece.is_red == is_red:
                    return (r, c)
        return (-1, -1)
    
    def evaluate(self) -> int:
        """评估局面（从红方角度）"""
        score = 0
        for r in range(10):
            for c in range(9):
                piece = self.board[r][c]
                if piece.piece_type != PieceType.EMPTY:
                    value = self.PIECE_VALUES[piece.piece_type]
                    
                    # 位置加成
                    if piece.piece_type == PieceType.PAWN:
                        if piece.is_red:
                            value += self.PAWN_POS_BONUS[r][c]
                        else:
                            value += self.PAWN_POS_BONUS[9-r][c]
                    
                    if piece.is_red:
                        score += value
                    else:
                        score -= value
        return score
    
    def make_move(self, from_r: int, from_c: int, to_r: int, to_c: int):
        """执行走法"""
        self.board[to_r][to_c] = self.board[from_r][from_c]
        self.board[from_r][from_c] = Piece(PieceType.EMPTY, True)
        self.move_history.append((from_r, from_c, to_r, to_c))
    
    def undo_move(self, from_r: int, from_c: int, to_r: int, to_c: int, captured: Piece):
        """撤销走法"""
        self.board[from_r][from_c] = self.board[to_r][to_c]
        self.board[to_r][to_c] = captured
        self.move_history.pop()
    
    def get_all_moves(self, is_red: bool) -> List[Tuple[int, int, int, int]]:
        """获取指定方的所有合法走法"""
        all_moves = []
        for r in range(10):
            for c in range(9):
                piece = self.board[r][c]
                if piece.piece_type != PieceType.EMPTY and piece.is_red == is_red:
                    for nr, nc in self.get_moves(r, c):
                        all_moves.append((r, c, nr, nc))
        return all_moves
    
    def minimax(self, depth: int, alpha: int, beta: int, is_red_turn: bool) -> Tuple[int, Optional[Tuple]]:
        """Minimax算法带Alpha-Beta剪枝"""
        if depth == 0:
            return self.evaluate(), None
        
        moves = self.get_all_moves(is_red_turn)
        if not moves:
            return (-100000 if is_red_turn else 100000), None
        
        best_move = None
        
        if is_red_turn:
            max_eval = -float('inf')
            for r, c, nr, nc in moves:
                captured = self.board[nr][nc]
                self.make_move(r, c, nr, nc)
                eval_score, _ = self.minimax(depth - 1, alpha, beta, False)
                self.undo_move(r, c, nr, nc, captured)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (r, c, nr, nc)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for r, c, nr, nc in moves:
                captured = self.board[nr][nc]
                self.make_move(r, c, nr, nc)
                eval_score, _ = self.minimax(depth - 1, alpha, beta, True)
                self.undo_move(r, c, nr, nc, captured)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (r, c, nr, nc)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    def get_best_move(self) -> Optional[str]:
        """获取引擎推荐走法（UCI格式）"""
        d = self.DIFFICULTY_LEVELS[self.difficulty]
        _, best_move = self.minimax(d['depth'], -float('inf'), float('inf'), False)
        
        if best_move is None:
            return None
        
        r, c, nr, nc = best_move
        
        # 添加随机性（低难度）
        if d['randomness'] > 0 and random.random() < d['randomness']:
            moves = self.get_all_moves(False)
            if moves:
                r, c, nr, nc = random.choice(moves)
        
        # 转换为UCI格式 (列a-i, 行0-9)
        cols = 'abcdefghi'
        return f"{cols[c]}{r}{cols[nc]}{nr}"
    
    def apply_uci_move(self, move: str) -> bool:
        """应用UCI格式的走法"""
        if len(move) != 4:
            return False
        
        cols = 'abcdefghi'
        try:
            from_c = cols.index(move[0])
            from_r = int(move[1])
            to_c = cols.index(move[2])
            to_r = int(move[3])
            
            # 验证走法合法性
            moves = self.get_moves(from_r, from_c)
            if (to_r, to_c) in moves:
                self.make_move(from_r, from_c, to_r, to_c)
                return True
            return False
        except (ValueError, IndexError):
            return False
    
    def display_board(self) -> str:
        """显示棋盘（简化文本）"""
        lines = []
        lines.append("  a b c d e f g h i")
        for r in range(10):
            row_str = f"{r} "
            for c in range(9):
                row_str += str(self.board[r][c]) + " "
            lines.append(row_str)
        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    engine = XiangqiEngineSimple()
    print("象棋引擎测试")
    print(engine.display_board())
    print(f"\n当前难度: {engine.get_difficulty_info()}")
    
    # 测试引擎走法
    best = engine.get_best_move()
    print(f"\n引擎推荐走法: {best}")
