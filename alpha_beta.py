from copy import deepcopy
import logging
import numpy as np
from board import Board
from constant import BOARD_SIZE


# ログの設定
format = "%(asctime)s: %(levelname)s: %(pathname)s: line %(lineno)s: %(message)s"
logging.basicConfig(filename='/var/log/intern3/flask.log', level=logging.DEBUG, format=format, datefmt='%Y-%m-%d %H:%M:%S')


def alpha_beta(board: Board, x: int, y: int, color: int, first_color: int, depth: int, alpha, beta) -> int:
    copy_board = deepcopy(board)
    copy_board.init_movable()
    copy_board.put_disc(x, y) # ここでcopy_board.current_colorが反転

    if depth <= 0:
        board_point = np.array([
            [-120, -120, -120, -120, -120, -120, -120, -120, -120, -120],
            [-120,  120,  -20,   20,    5,    5,   20,  -20,  120, -120],
            [-120,  -20,  -40,   -5,   -5,   -5,   -5,  -40,  -20, -120],
            [-120,   20,   -5,   15,    3,    3,   15,   -5,   20, -120],
            [-120,    5,   -5,    3,    3,    3,    3,   -5,    5, -120],
            [-120,    5,   -5,    3,    3,    3,    3,   -5,    5, -120],
            [-120,   20,   -5,   15,    3,    3,   15,   -5,   20, -120],
            [-120,  -20,  -40,   -5,   -5,   -5,   -5,  -40,  -20, -120],
            [-120,  120,  -20,   20,    5,    5,   20,  -20,  120, -120],
            [-120, -120, -120, -120, -120, -120, -120, -120, -120, -120]
        ], dtype=np.int8)
        score = (board_point * (copy_board.board == first_color)).sum() - (board_point * (copy_board.board == -first_color)).sum()
        #print(score)
        return score

    else:
        copy_board.init_movable()
        if depth >= 2:
            logging.debug(f'探索する数：{np.count_nonzero(copy_board.movable_pos > 0)}')
        for i in range(1, BOARD_SIZE + 1):
            for j in range(1, BOARD_SIZE + 1):
                if copy_board.movable_pos[i, j] > 0:
                    score = alpha_beta(copy_board, i, j, copy_board.current_color, first_color, depth - 1, alpha, beta)
                    #print(score)
                    if color == first_color and score > alpha:
                        alpha = score
                    elif color == -first_color and score < beta:
                        beta = score
                    #print(f'color:{color:2} node:{depth:1} α:{alpha:5} β:{beta:5}')
                    if alpha >= beta:
                        #print(f'{alpha} >= {beta}')
                        return alpha if color == first_color else beta
        #print(f'color:{color} node:{depth} α:{alpha} β:{beta}')
        return alpha if color == first_color else beta


def act_alpha_beta(board: Board) -> None:
    INIT_VALUE = 10000
    best_score = -INIT_VALUE
    best_pos = (-1, -1)
    searchable_num = np.count_nonzero(board.movable_pos > 0)
    logging.debug(f'探索する数：{np.count_nonzero(board.movable_pos > 0)}')
    for x in range(1, BOARD_SIZE + 1):
        for y in range(1, BOARD_SIZE + 1):
            if board.movable_pos[x, y] > 0:
                score = alpha_beta(board, x, y, board.current_color, board.current_color, min(searchable_num - 1, 3), -INIT_VALUE, INIT_VALUE)
                if score > best_score:
                    best_score = score
                    best_pos = (x, y)
    board.put_disc(*best_pos) # 決定した座標に実際に置く


if __name__ == '__main__':
    board = Board()
    board.put_max_pos()
    best_pos = act_alpha_beta(board)
    print(best_pos)
