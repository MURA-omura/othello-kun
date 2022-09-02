# オセロの盤面クラス

from typing import Union
import datetime
import logging
import random

import numpy as np
import cv2

from env import IMAGE_DIR
from constant import BOARD_SIZE, EMPTY, WHITE, BLACK, WALL, LEFT, UPPER_LEFT, UPPER, UPPER_RIGHT, RIGHT, LOWER_RIGHT, LOWER, LOWER_LEFT


class Board:
    def __init__(self, turn: Union[int, None] = None, color: Union[int, None] = None, board: Union[bytes, None] = None) -> None:
        format = "%(asctime)s: %(levelname)s: %(pathname)s: line %(lineno)s: %(message)s"
        logging.basicConfig(filename='/var/log/intern3/flask.log', level=logging.DEBUG, format=format, datefmt='%Y-%m-%d %H:%M:%S')

        # 途中の対戦データがなければ盤面を初期化する
        if turn is None or color is None or board is None:
            self.board = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=np.int8)
        
            self.board[0, :] = WALL
            self.board[:, 0] = WALL
            self.board[BOARD_SIZE + 1, :] = WALL
            self.board[:, BOARD_SIZE + 1] = WALL

            self.board[4, 4] = WHITE
            self.board[5, 5] = WHITE
            self.board[4, 5] = BLACK
            self.board[5, 4] = BLACK

            self.turn = 0
            self.current_color = WHITE if random.randint(0, 1000) % 2 == 0 else BLACK
        # 途中の対戦データがあれば反映する
        else:
            self.board = np.frombuffer(board, dtype=np.int8).copy()
            self.board = np.reshape(self.board, (BOARD_SIZE + 2, BOARD_SIZE + 2))
            self.turn = turn
            self.current_color = color

        self.movable_pos = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=np.bool_)
        self.movable_dir = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=np.uint8)
        self.movable_cnt = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=np.uint8)
        self.init_movable()

    def init_movable(self) -> None:
        self.movable_pos[:, :] = False
        self.movable_cnt[:, :] = 0
        for x in range(1, BOARD_SIZE + 1):
            for y in range(1, BOARD_SIZE + 1):
                dir = self.check_mobility(x, y, self.current_color)
                self.movable_dir[x, y] = dir
                if dir > 0:
                    self.movable_pos[x, y] = True
                    self.movable_cnt[x, y] = self.flip_discs(x, y, flip=False)

    def check_mobility(self, x: int, y: int, color: int) -> int:
        # 注目しているマスの裏返せる方向の情報が入る
        dir = 0
 
        # 既に石がある場合はダメ
        if(self.board[x, y] != EMPTY):
            return dir
 
        ## 左
        if(self.board[x - 1, y] == - color): # 直上に相手の石があるか
            x_tmp = x - 2
            y_tmp = y
            # 相手の石が続いているだけループ
            while self.board[x_tmp, y_tmp] == - color:
                x_tmp -= 1
            # 相手の石を挟んで自分の石があればdirを更新
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | LEFT
 
        ## 左上
        if(self.board[x - 1, y - 1] == - color):
            x_tmp = x - 2
            y_tmp = y - 2
            while self.board[x_tmp, y_tmp] == - color:
                x_tmp -= 1
                y_tmp -= 1
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | UPPER_LEFT
 
        ## 上
        if(self.board[x, y - 1] == - color):
            x_tmp = x
            y_tmp = y - 2
            while self.board[x_tmp, y_tmp] == - color:
                y_tmp -= 1
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | UPPER
 
        ## 右上
        if(self.board[x + 1, y - 1] == - color):
            x_tmp = x + 2
            y_tmp = y - 2
            while self.board[x_tmp, y_tmp] == - color:
                x_tmp += 1
                y_tmp -= 1
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | UPPER_RIGHT
 
        ## 右
        if(self.board[x + 1, y] == - color):
            x_tmp = x + 2
            y_tmp = y
            while self.board[x_tmp, y_tmp] == - color:
                x_tmp += 1
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | RIGHT
 
        ## 右下
        if(self.board[x + 1, y + 1] == - color):
            x_tmp = x + 2
            y_tmp = y + 2
            while self.board[x_tmp, y_tmp] == - color:
                x_tmp += 1
                y_tmp += 1
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | LOWER_RIGHT
 
        ## 下
        if(self.board[x, y + 1] == - color):
            x_tmp = x
            y_tmp = y + 2
            while self.board[x_tmp, y_tmp] == - color:
                y_tmp += 1
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | LOWER
 
        ## 左下
        if(self.board[x - 1, y + 1] == - color):
            x_tmp = x - 2
            y_tmp = y + 2
            while self.board[x_tmp, y_tmp] == - color:
                x_tmp -= 1
                y_tmp += 1
            if self.board[x_tmp, y_tmp] == color:
                dir = dir | LOWER_LEFT
 
        return dir
    
    def put_disc(self, x: int, y: int) -> bool:
        # 置く位置のチェック
        if x < 1 or BOARD_SIZE < x:
            return False
        if y < 1 or BOARD_SIZE < y:
            return False
        if self.movable_pos[x, y] == 0:
            return False

        self.flip_discs(x, y)
        self.turn += 1
        self.current_color = -self.current_color
        self.init_movable()
        if not self.movable_pos.any() and not self.is_end():
            self.current_color = -self.current_color
            self.init_movable()
        return True

    def flip_discs(self, x: int, y: int, flip: bool = True) -> int:
        # 石を置く
        if flip:
            self.board[x, y] = self.current_color
        
        # 以下石を裏返す
        # MovableDirの(y, x)座標をdirに代入
        dir = self.movable_dir[x, y]
        flip_count = 0

        ## 左
        if dir & LEFT: # AND演算子
            x_tmp = x - 1
            # 相手の石がある限りループが回る
            while self.board[x_tmp, y] == - self.current_color:
                if flip:
                    # 相手の石があるマスを自分の石の色に塗り替えている
                    self.board[x_tmp, y] = self.current_color
                flip_count += 1
                # さらに1マス左に進めてループを回す
                x_tmp -= 1

        ## 左上
        if dir & UPPER_LEFT:
            x_tmp = x - 1
            y_tmp = y - 1
            while self.board[x_tmp, y_tmp] == - self.current_color:
                if flip:
                    self.board[x_tmp, y_tmp] = self.current_color
                flip_count += 1
                x_tmp -= 1
                y_tmp -= 1

        ## 上
        if dir & UPPER:
            y_tmp = y - 1
            while self.board[x, y_tmp] == - self.current_color:
                if flip:
                    self.board[x, y_tmp] = self.current_color
                flip_count += 1
                y_tmp -= 1

        ## 右上
        if dir & UPPER_RIGHT:
            x_tmp = x + 1
            y_tmp = y - 1
            while self.board[x_tmp, y_tmp] == - self.current_color:
                if flip:
                    self.board[x_tmp, y_tmp] = self.current_color
                flip_count += 1
                x_tmp += 1
                y_tmp -= 1

        ## 右
        if dir & RIGHT:
            x_tmp = x + 1
            while self.board[x_tmp, y] == - self.current_color:
                if flip:
                    self.board[x_tmp, y] = self.current_color
                flip_count += 1
                x_tmp += 1

        ## 右下
        if dir & LOWER_RIGHT:
            x_tmp = x + 1
            y_tmp = y + 1
            while self.board[x_tmp, y_tmp] == - self.current_color:
                if flip:
                    self.board[x_tmp, y_tmp] = self.current_color
                flip_count += 1
                x_tmp += 1
                y_tmp += 1

        ## 下
        if dir & LOWER:
            y_tmp = y + 1
            while self.board[x, y_tmp] == - self.current_color:
                if flip:
                    self.board[x, y_tmp] = self.current_color
                flip_count += 1
                y_tmp += 1

        ## 左下
        if dir & LOWER_LEFT:
            x_tmp = x - 1
            y_tmp = y + 1
            while self.board[x_tmp, y_tmp] == - self.current_color:
                if flip:
                    self.board[x_tmp, y_tmp] = self.current_color
                flip_count += 1
                x_tmp -= 1
                y_tmp += 1

        return flip_count

    def put_max_pos(self) -> None:
        max_idx = np.unravel_index(np.argmax(self.movable_cnt), self.movable_cnt.shape)
        logging.debug(max_idx)
        self.put_disc(max_idx[0], max_idx[1])

    def is_end(self) -> bool:
        if self.movable_pos.any():
            return False # 現状打てる手があるならゲーム終了でない
        for x in range(1, BOARD_SIZE + 1):
            for y in range(1, BOARD_SIZE + 1):
                if self.check_mobility(x, y, -self.current_color) > 0:
                    return False # 置ける場所が1つでもある場合はゲーム終了でない
        return True

    def judge_winner(self) -> str:
        num_white = 0; num_black = 0
        for x in range(1, BOARD_SIZE + 1):
            for y in range(1, BOARD_SIZE + 1):
                if self.board[x, y] == BLACK:
                    num_black += 1
                elif self.board[x, y] == WHITE:
                    num_white += 1
        text = f'黒：{num_black}枚　白：{num_white}枚\n'
        if num_black == num_white:
            return text + '引き分け'
        elif num_black > num_white:
            return text + 'あなたの勝ち！\nおめでとう！！'
        else:
            return text + 'オセロ君の勝ち'

    def to_bytes(self) -> bytes:
        return self.board.tobytes()

    def to_image(self, user_id: str) -> str:
        img = cv2.imread(IMAGE_DIR + 'board_template.png')
        for x in range(1, BOARD_SIZE + 1):
            draw_x = x * 50 + 25
            for y in range(1, BOARD_SIZE + 1):
                draw_y = y * 50 + 25
                if self.board[x, y] == BLACK:
                    cv2.circle(img, (draw_x, draw_y), 20, (0, 0, 0), thickness=-1)
                elif self.board[x, y] == WHITE:
                    cv2.circle(img, (draw_x, draw_y), 20, (255, 255, 255), thickness=-1)
        img_path = IMAGE_DIR + user_id + '-' + datetime.datetime.now().strftime('%H%M%S%f') + '.png'
        cv2.imwrite(img_path, img)
        return img_path


    def to_string(self) -> str:
        board_str = '　   a  b  c  d  e  f  g  h\n' # 文字に変換された盤面
        num_white = 0
        num_black = 0
        status_str = {
            EMPTY: '□',
            WHITE: '○',
            BLACK: '●',
            WALL: '■'
        } # マスの状態に合わせた文字

        for i, row in enumerate(self.board[1 : BOARD_SIZE+1, 1 : BOARD_SIZE+1].T):
            board_str += f'{i+1}　'
            for val in row:
                board_str += status_str[val]
                if val == WHITE:
                    num_white += 1
                elif val == BLACK:
                    num_black += 1
            board_str += '\n'

        board_str += f'○：{num_white}、●：{num_black}\n次の手：{status_str[self.current_color]}'
        if self.is_end():
            if num_white == num_black:
                board_str += '\n引き分け'
            else:
                winner = '○' if num_white > num_black else '●'
                board_str += '\n勝者：' + winner
        return board_str

    def to_string_all(self) -> str:
        board_str = '　   a  b  c  d  e  f  g  h\n' # 文字に変換された盤面
        status_str = {
            EMPTY: '□',
            WHITE: '○',
            BLACK: '●',
            WALL: '■'
        } # マスの状態に合わせた文字

        for i, row in enumerate(self.board[1 : BOARD_SIZE+1, 1 : BOARD_SIZE+1].T):
            board_str += f'{i+1}　'
            for val in row:
                board_str += status_str[val]
            board_str += '\n'
        board_str += f'次の手：{status_str[self.current_color]}\n\n'

        for row in self.movable_pos[1 : BOARD_SIZE+1, 1 : BOARD_SIZE+1].T:
            for val in row:
                board_str += f'{val:^3}'
            board_str += '\n'
        board_str += '\n'

        for row in self.movable_dir[1 : BOARD_SIZE+1, 1 : BOARD_SIZE+1].T:
            for val in row:
                board_str += f'{val:^3}'
            board_str += '\n'
        board_str += '\n'

        for row in self.movable_cnt[1 : BOARD_SIZE+1, 1 : BOARD_SIZE+1].T:
            for val in row:
                board_str += f'{val:^3}'
            board_str += '\n'
        return board_str
