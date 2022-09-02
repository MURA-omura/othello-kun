RESET_WORDS = ['終了', '終わり', 'おわり', 'リセット']
HISTORY_WORDS = ['履歴', '過去', '一覧', '対戦履歴']

BOARD_SIZE = 8 # ボードサイズ
EMPTY = 0 # 空きマス
WHITE = 1 # 白石
BLACK = -WHITE # 黒石
WALL = 2 # 壁

NONE = 0
LEFT = 2 ** 0 # = 1 左方向にひっくり返せるか
UPPER_LEFT = 2 ** 1 # = 1 左上方向にひっくり返せるか
UPPER = 2 ** 2 # = 1 上方向にひっくり返せるか
UPPER_RIGHT = 2 ** 3 # = 1 右上方向にひっくり返せるか
RIGHT = 2 ** 4 # = 1 右方向にひっくり返せるか
LOWER_RIGHT = 2 ** 5 # = 1 右下方向にひっくり返せるか
LOWER = 2 ** 6 # = 1 下方向にひっくり返せるか
LOWER_LEFT = 2 ** 7 # = 1 左下方向にひっくり返せるか
