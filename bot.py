#!/usr/bin/env python3
"""
象棋AI - 飞书集成版本
基于简化引擎（无需外部依赖）
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_engine import XiangqiEngineSimple
import re

class XiangqiBot:
    """飞书象棋机器人"""
    
    DIFFICULTY_NAMES = {
        1: "入门 😊",
        2: "业余 🤔", 
        3: "高手 😤",
        4: "大师 👑"
    }
    
    def __init__(self):
        self.engine = XiangqiEngineSimple()
        self.game_active = False
        self.user_side = True  # 用户执红
        
    def start_game(self) -> str:
        """开始新游戏"""
        self.engine = XiangqiEngineSimple()
        self.game_active = True
        self.user_side = True
        
        return f"""🎮 象棋对战开始！

{self.engine.display_board()}

你是红方（大写字母），请走第一步。
走法格式: 象棋 [起始][目标] 如 "象棋 h2e2"

当前难度: {self.get_difficulty_text()}
输入 "象棋 帮助" 查看全部命令"""
    
    def get_difficulty_text(self) -> str:
        d = self.engine.DIFFICULTY_LEVELS[self.engine.difficulty]
        name = self.DIFFICULTY_NAMES.get(self.engine.difficulty, d['name'])
        return f"难度{self.engine.difficulty} ({name}): 深度{d['depth']}"
    
    def set_difficulty(self, level: int) -> str:
        if not 1 <= level <= 4:
            return "❌ 难度级别应为1-4"
        
        self.engine.set_difficulty(level)
        
        if not self.game_active:
            return f"✅ 难度已设置为: {self.get_difficulty_text()}\n输入 \"象棋 对战\" 开始游戏"
        else:
            return f"✅ 难度已切换为: {self.get_difficulty_text()}"
    
    def parse_move(self, text: str) -> str:
        """解析走法"""
        text = text.strip().lower()
        
        # 移除"象棋"前缀
        if text.startswith("象棋"):
            text = text[2:].strip()
        
        # UCI格式: h2e2
        if re.match(r'^[a-i][0-9][a-i][0-9]$', text):
            return text
        
        return None
    
    def make_user_move(self, move_str: str) -> str:
        """处理用户走棋"""
        if not self.game_active:
            return "❌ 游戏未开始，输入 \"象棋 对战\" 开始"
        
        move = self.parse_move(move_str)
        if not move:
            return "❌ 走法格式错误。请使用格式: \"象棋 h2e2\" (从h2走到e2)"
        
        # 执行用户走法
        if not self.engine.apply_uci_move(move):
            return f"❌ 非法走法: {move}"
        
        # 检查游戏是否结束
        if self.check_game_over():
            return f"你走: {move}\n🎉 游戏结束！"
        
        # 引擎回应
        ai_move = self.engine.get_best_move()
        if ai_move:
            self.engine.apply_uci_move(ai_move)
            
            # 再次检查游戏结束
            if self.check_game_over():
                return f"你走: {move}\nAI走: {ai_move}\n🏁 游戏结束！"
            
            return f"""你走: {move}
AI走: {ai_move}

{self.engine.display_board()}

{self.get_difficulty_text()} | 输入走法继续..."""
        else:
            return f"你走: {move}\n🎉 恭喜获胜！"
    
    def check_game_over(self) -> bool:
        """检查游戏是否结束（简化版）"""
        # 检查是否还有将/帅
        red_king = False
        black_king = False
        for r in range(10):
            for c in range(9):
                p = self.engine.board[r][c]
                if p.piece_type.value == 1:  # KING
                    if p.is_red:
                        red_king = True
                    else:
                        black_king = True
        return not (red_king and black_king)
    
    def show_board(self) -> str:
        """显示棋盘"""
        if not self.game_active:
            return "游戏未开始，输入 \"象棋 对战\" 开始"
        return self.engine.display_board()
    
    def resign(self) -> str:
        """认输"""
        if not self.game_active:
            return "当前没有进行中的游戏"
        self.game_active = False
        return "🏳️ 你认输了。输入 \"象棋 对战\" 重新开始"
    
    def end_game(self) -> str:
        """结束游戏"""
        if not self.game_active:
            return "当前没有进行中的游戏"
        self.game_active = False
        return "👋 游戏已结束"
    
    def show_help(self) -> str:
        """显示帮助"""
        return """🎯 象棋AI命令列表

对局命令:
• 象棋 对战 / 象棋 开始 - 开始新游戏
• 象棋 [走法] - 走棋，如 "象棋 h2e2"
• 象棋 认输 - 认输
• 象棋 结束 - 结束游戏

难度设置:
• 象棋 难度1 - 入门 (深度2)
• 象棋 难度2 - 业余 (深度3)  
• 象棋 难度3 - 高手 (深度4)
• 象棋 难度4 - 大师 (深度5)

其他:
• 象棋 棋盘 - 显示当前棋盘
• 象棋 帮助 - 显示此帮助

走法说明:
• 列: a-i (从左到右，红方视角)
• 行: 0-9 (从上到下)
• 示例: "象棋 h2e2" = 炮从h2走到e2

棋盘表示:
• 大写字母 = 红方(你)
• 小写字母 = 黑方(AI)
• R/r = 车, N/n = 马, B/b = 象
• A/a = 士, K/k = 将/帅
• C/c = 炮, P/p = 兵/卒"""


# 全局机器人实例
_bot = None

def get_bot() -> XiangqiBot:
    global _bot
    if _bot is None:
        _bot = XiangqiBot()
    return _bot


def handle_message(text: str) -> str:
    """处理飞书消息，返回回复内容"""
    text_lower = text.strip().lower()
    bot = get_bot()
    
    # 必须以"象棋"开头（除非是帮助或特定命令）
    has_xiangqi_prefix = text_lower.startswith("象棋")
    
    # 帮助（不需要前缀）
    if "象棋帮助" in text_lower or "象棋 帮助" in text_lower:
        return bot.show_help()
    
    # 其他命令需要"象棋"前缀
    if not has_xiangqi_prefix:
        return None
    
    # 移除"象棋"前缀并清理
    content = text_lower[2:].strip()
    
    # 开始游戏
    if any(kw in content for kw in ["对战", "开始", "start", "new"]):
        return bot.start_game()
    
    # 设置难度
    diff_match = re.search(r'难度\s*(\d)', content)
    if diff_match:
        level = int(diff_match.group(1))
        return bot.set_difficulty(level)
    
    # 显示棋盘
    if "棋盘" in content or "board" in content:
        return bot.show_board()
    
    # 认输
    if "认输" in content or "resign" in content:
        return bot.resign()
    
    # 结束
    if "结束" in content or "quit" in content or "exit" in content:
        return bot.end_game()
    
    # 帮助
    if "帮助" in content or "help" in content:
        return bot.show_help()
    
    # 走棋 (4字符UCI格式)
    move_match = re.search(r'([a-i][0-9][a-i][0-9])', content)
    if move_match:
        return bot.make_user_move(move_match.group(1))
    
    # 默认帮助
    return "未知命令。输入 \"象棋 帮助\" 查看可用命令"


def main():
    """主函数 - 支持命令行调用"""
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 组合所有参数作为消息
        message = " ".join(sys.argv[1:])
        result = handle_message(message)
        if result:
            print(result)
    else:
        # 测试模式
        print("象棋AI测试模式")
        print("=" * 40)
        
        test_inputs = [
            "象棋 帮助",
            "象棋 对战",
            "象棋 难度3",
            "象棋 h2e2",
        ]
        
        for inp in test_inputs:
            print(f"\n输入: {inp}")
            print("-" * 40)
            result = handle_message(inp)
            if result:
                print(result)
            else:
                print("(无响应)")


if __name__ == "__main__":
    main()
