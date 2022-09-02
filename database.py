# テーブル：
# id: INT
# user_id: CHAR(33)
# turn: TINYINT
# color: TINYINT
# board: BYTE(100) (4x4はBYTE(36))
# end: BOOL
'''
CREATE TABLE othello (
    id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY, user_id CHAR(33) NOT NULL, turn TINYINT NOT NULL, color TINYINT NOT NULL, board BINARY(64) NOT NULL, end BOOL NOT NULL,
    INDEX idx_othello_01 (user_id)
);
'''

from typing import Tuple, List, Union
import pymysql  # 参考: https://pymysql.readthedocs.io/en/latest/index.html
import logging
from env import MYSQL_PASSWORD

class Database(object):
    def __init__(self):
        # ログの設定
        format = "%(asctime)s: %(levelname)s: %(pathname)s: line %(lineno)s: %(message)s"
        logging.basicConfig(filename='/var/log/intern3/flask.log', level=logging.DEBUG, format=format, datefmt='%Y-%m-%d %H:%M:%S')

        self.conn = pymysql.connect(host='localhost', user='intern3', passwd=MYSQL_PASSWORD, db='intern3')
        self.cur = self.conn.cursor()


    def create(self, user_id: str, turn: int, color: int, board: bytes, end: bool) -> None:
        self.cur.execute('INSERT INTO othello (user_id, turn, color, board, end) VALUES (%s, %s, %s, %s, %s)', (user_id, turn, color, board, end))
        self.conn.commit()


    def read(self, user_id: str) -> Tuple[Union[int, None], Union[int, None], Union[bytes, None]]:
        self.cur.execute('SELECT turn, color, board, end FROM othello WHERE user_id=%s', (user_id,))
        boards = self.cur.fetchall()
        if len(boards) == 0 or boards[-1][3] == True:
            return None, None, None
        else:
            return (boards[-1][0], boards[-1][1], boards[-1][2])


    def read_all(self, user_id: str) -> List[Tuple[int, int, bytes]]:
        self.cur.execute('SELECT turn, color, board, end FROM othello WHERE user_id=%s', (user_id,))
        boards = self.cur.fetchall()
        begin_id = 0
        if len(boards) <= 2:
            return []
        for i in range(len(boards) - 2, -1, -1):
            if boards[i][3] > 0:
                begin_id = i + 1
                break
        return [b[:3] for b in boards[begin_id:]]


    def update_end(self, user_id: str) -> bool:
        self.cur.execute('SELECT MAX(id) FROM othello WHERE user_id=%s', (user_id,))
        id = self.cur.fetchone()[0]
        if id is None:
            return False
        else:
            self.cur.execute('UPDATE othello SET end=true WHERE id=%s', (id))
            self.conn.commit()
            return True


    def delete(self):
        pass
