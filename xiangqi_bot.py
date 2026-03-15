#!/usr/bin/env python3
"""
象棋AI - 飞书集成的中国象棋对战系统
基于Pikafish UCI引擎
"""

import subprocess
import os
import re
import json
from pathlib import Path
from typing import Optional, Tuple

class XiangqiEngine:
    """UCI象棋引擎封装"""
    
    DIFFICULTY_LEVELS = {
        1: {"name": "入门", "depth": 5, "time": 1.0, "nodes": 50000},
        2: {"name": "业余", "depth": 8, "time": 2.0, "nodes": 200000},
        3: {"name": "高手", "depth": 12, "time": 5.0, "nodes": 1000000},
        4: {"name": "大师", "depth": 20, "time": 10.0, "nodes": 5000000},
    }
    
    def __init__(self, engine_path: str = None):
        self.engine_path = engine_path or self._find_engine()
        self.process: Optional[subprocess.Popen] = None
        self.difficulty = 2  # 默认业余级
        
    def _find_engine(self) -> str:
        """自动查找引擎可执行文件"""
        possible_paths = [
            "./pikafish",
            "./Pikafish/src/pikafish",
            "./fairy-stockfish",
            "/opt/homebrew/bin/fairy-stockfish",
            "/usr/local/bin/pikafish",
            "/usr/local/bin/fairy-stockfish",
        ]
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        raise FileNotFoundError("未找到象棋引擎，请先运行 setup.sh 安装")
    
    def start(self):
        """启动引擎"""
        if self.process:
            return
        self.process = subprocess.Popen(
            [self.engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self._uci_init()
    
    def _uci_init(self):
        """UCI协议初始化"""
        self._send("uci")
        while True:
            line = self._read()
            if "uciok" in line:
                break
        self._send("setoption name UCI_Variant value xiangqi")
        self._send("isready")
        while True:
            line = self._read()
            if "readyok" in line:
                break
    
    def _send(self, cmd: str):
        """发送命令到引擎"""
        if self.process:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
    
    def _read(self) -> str:
        """从引擎读取输出"""
        if self.process:
            return self.process.stdout.readline().strip()
        return ""
    
    def set_difficulty(self, level: int):
        """设置难度 1-4"""
        if level in self.DIFFICULTY_LEVELS:
            self.difficulty = level
            return True
        return False
    
    def get_difficulty_info(self) -> str:
        """获取当前难度信息"""
        d = self.DIFFICULTY_LEVELS[self.difficulty]
        return f"难度{self.difficulty} ({d['name']}): 深度{d['depth']}, 时限{d['time']}秒"
    
    def new_game(self):
        """开始新游戏"""
        self._send("ucinewgame")
        self._send("position startpos")
    
    def make_move(self, move: str) -> bool:
        """执行一步棋（UCI格式，如 h2e2）"""
        # 获取当前位置并添加移动
        self._send("position startpos moves " + move)
        return True
    
    def get_best_move(self) -> Tuple[str, str]:
        """获取引擎推荐走法，返回 (move, info)"""
        d = self.DIFFICULTY_LEVELS[self.difficulty]
        
        # 构建go命令
        go_cmd = f"go depth {d['depth']}"
        self._send(go_cmd)
        
        best_move = ""
        info = ""
        
        while True:
            line = self._read()
            if line.startswith("info"):
                # 提取深度、分数等信息
                if "depth" in line and "score" in line:
                    info = line
            elif line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    best_move = parts[1]
                break
        
        return best_move, info
    
    def stop(self):
        """停止引擎"""
        if self.process:
            self._send("quit")
            self.process.wait(timeout=2)
            self.process = None


class XiangqiGame:
    """象棋游戏管理"""
    
    def __init__(self):
        self.engine = XiangqiEngine()
        self.history = []  # 走棋历史
        self.is_active = False
        self.user_side = "red"  # 用户执红
        
    def start(self) -> str:
        """开始新游戏"""
        try:
            self.engine.start()
            self.engine.new_game()
            self.history = []
            self.is_active = True
            self.user_side = "red"
            
            info = self.engine.get_difficulty_info()
            return f"🎮 象棋对战开始！\n{info}\n你是红方（下方），请走第一步。\n格式: 象棋 [走法] 如 '象棋 h2e2'"
        except Exception as e:
            return f"❌ 启动失败: {e}"
    
    def set_difficulty(self, level: int) -> str:
        """设置难度"""
        if self.engine.set_difficulty(level):
            return f"✅ 已设置: {self.engine.get_difficulty_info()}"
        return "❌ 难度级别应为1-4"
    
    def parse_move(self, move_str: str) -> Optional[str]:
        """解析用户输入的走法"""
        move_str = move_str.strip().lower()
        
        # 支持UCI格式: h2e2 (从h2到e2)
        if re.match(r'^[a-i][0-9][a-i][0-9]$', move_str):
            return move_str
        
        # 支持中文格式: 炮二平五 -> 需要转换
        # 这里简化处理，提示用户使用UCI格式
        return None
    
    def user_move(self, move_str: str) -> str:
        """处理用户走棋"""
        if not self.is_active:
            return "❌ 游戏未开始，输入 '象棋 对战' 开始"
        
        move = self.parse_move(move_str)
        if not move:
            return "❌ 走法格式错误。请使用UCI格式: 如 h2e2 (从h2走到e2)\n列: a-i, 行: 0-9"
        
        # 记录用户走法
        self.history.append(("user", move))
        self.engine.make_move(" ".join([m for _, m in self.history]))
        
        # 引擎回应
        best_move, info = self.engine.get_best_move()
        if best_move and best_move != "(none)":
            self.history.append(("engine", best_move))
            return f"你走: {move}\nAI走: {best_move}"
        else:
            return f"你走: {move}\n🎉 游戏结束！"
    
    def show_board(self) -> str:
        """显示当前棋盘状态（简化文本表示）"""
        if not self.is_active:
            return "游戏未开始"
        
        moves = " ".join([m for _, m in self.history]) if self.history else "无"
        return f"当前局面\n走法历史: {moves}\n难度: {self.engine.get_difficulty_info()}"
    
    def resign(self) -> str:
        """认输"""
        self.is_active = False
        return "🏳️ 你认输了。输入 '象棋 对战' 重新开始"
    
    def end(self) -> str:
        """结束游戏"""
        self.is_active = False
        if self.engine:
            self.engine.stop()
        return "👋 游戏结束"


# 全局游戏实例
game = XiangqiGame()


def handle_message(text: str) -> str:
    """处理飞书消息"""
    text = text.strip().lower()
    
    # 帮助
    if text in ["象棋 帮助", "象棋 help"]:
        return """🎯 象棋AI命令列表:
• 象棋 对战 / 象棋 开始 - 开始新游戏
• 象棋 难度[1-4] - 设置难度 (1入门 2业余 3高手 4大师)
• 象棋 [走法] - 走棋，UCI格式如 h2e2
• 象棋 认输 - 认输
• 象棋 结束 - 结束游戏
• 象棋 帮助 - 显示此帮助

走法格式 (UCI):
• 列: a-i (从左到右)
• 行: 0-9 (红方0开始，黑方9开始)
• 示例: h2e2 = 从h2走到e2"""
    
    # 开始游戏
    if text in ["象棋 对战", "象棋 开始", "象棋 start", "象棋 new"]:
        return game.start()
    
    # 设置难度
    diff_match = re.match(r'象棋\s*难度\s*(\d)', text)
    if diff_match:
        level = int(diff_match.group(1))
        return game.set_difficulty(level)
    
    # 认输
    if text in ["象棋 认输", "象棋 resign"]:
        return game.resign()
    
    # 结束
    if text in ["象棋 结束", "象棋 quit", "象棋 exit"]:
        return game.end()
    
    # 走棋 (象棋 + 4个字符的UCI走法)
    move_match = re.match(r'象棋\s+([a-i][0-9][a-i][0-9])$', text)
    if move_match:
        return game.user_move(move_match.group(1))
    
    # 直接走棋格式 (如果已经在游戏中)
    if game.is_active and re.match(r'^([a-i][0-9][a-i][0-9])$', text):
        return game.user_move(text)
    
    return None  # 不处理的消息


if __name__ == "__main__":
    # 测试模式
    print(handle_message("象棋 帮助"))
