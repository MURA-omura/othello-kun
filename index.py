# Python 3.10.4
# Flask 2.1.2
# Flaskの公式ドキュメント：https://flask.palletsprojects.com/en/2.0.x/
# python3の公式ドキュメント：https://docs.python.org/ja/3.9/
# python3の基礎文法のわかりやすいサイト：https://note.nkmk.me/python/
# 使用するモジュールのインポート
# pythonが提供しているモジュールのインポート

from typing import Dict, Tuple, List, Union
import datetime
import json
import logging
import os
import requests
import subprocess

# サードパーティモジュールのインポート
import cv2
from flask import Flask, request

# 自分で作成したモジュールのインポート
from alpha_beta import act_alpha_beta
from board import Board
from database import Database
from env import ACCESS_TOKEN, SERVER_DOMAIN, IMAGE_DIR, VIDEO_DIR
from constant import RESET_WORDS, HISTORY_WORDS, BOARD_SIZE, WHITE


# Flaskクラスをnewしてappに代入
# gunicornの起動コマンドに使用しているのでここは変更しないこと
app = Flask(__name__)
database = Database()

# ログの設定
format = "%(asctime)s: %(levelname)s: %(pathname)s: line %(lineno)s: %(message)s"
logging.basicConfig(filename='/var/log/intern3/flask.log', level=logging.DEBUG, format=format, datefmt='%Y-%m-%d %H:%M:%S')


# 座標を表す文字列を整数の座標に変換する
def pos2xy(pos: str) -> Tuple[Union[int, None], Union[int, None]]:
    x = None; y = None
    if len(pos) == 2: # メッセージの文字数が2でないならパス
        if pos[0].isdecimal() and pos[0] in [str(i) for i in range(1, BOARD_SIZE + 1)]:
            y = int(pos[0])
            if pos[1] in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
                x = ord(pos[1]) - ord('a') + 1
            elif pos[1] in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                x = ord(pos[1]) - ord('A') + 1
        elif pos[1].isdecimal() and pos[1] in [str(i) for i in range(1, BOARD_SIZE + 1)]:
            y = int(pos[1])
            if pos[0] in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
                x = ord(pos[0]) - ord('a') + 1
            elif pos[0] in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                x = ord(pos[0]) - ord('A') + 1
    return (x, y)


# 複数の画像のパスから動画を作成する
def make_video(image_paths: List[str], user_id: str) -> str:
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    file_name = user_id + '-' + datetime.datetime.now().strftime('%H%M%S%f') + '.mp4' # LINEはmp4コーデックオンリー
    writer = cv2.VideoWriter(f'{VIDEO_DIR}-pre{file_name}', fourcc, 2, (460, 460))
    for ip in image_paths:
        img = cv2.imread(ip)
        writer.write(img)
        os.remove(ip)
    writer.release()
    # そのままだと見れないのでエンコード
    subprocess.call(f'ffmpeg -i "{VIDEO_DIR}-pre{file_name}" "{VIDEO_DIR}{file_name}"', shell=True)
    os.remove(f'{VIDEO_DIR}-pre{file_name}')
    return VIDEO_DIR + file_name


# メッセージ群と送信先からレスポンスを作成する
def make_response(texts: List[str], receiver : str, is_push: bool = False) -> Tuple[Dict[str, str], Dict[str, str]]:
    messages = []
    for txt in texts:
        if txt.startswith(SERVER_DOMAIN + IMAGE_DIR):
            messages.append({
                'type': 'image',
                'originalContentUrl': txt,
                'previewImageUrl': txt
            })
        elif txt.startswith(SERVER_DOMAIN + VIDEO_DIR):
            messages.append({
                'type': 'video',
                'originalContentUrl': txt,
                'previewImageUrl': SERVER_DOMAIN + IMAGE_DIR + 'board_start.png'
            })
        else:
            messages.append({
                'type': 'text',
                'text': txt,
                'notificationDisabled': is_push
            })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    if is_push:
        body = {
            'to': receiver,
            'messages': messages
        }
    else:
        body = {
            'replyToken': receiver,
            'messages': messages
        }
    return headers, body


# 敵の石の配置
def act_enemy(board: Board, user_id: str) -> str:
    act_alpha_beta(board) # αβ法
    # board.put_max_pos() # 貪欲
    database.create(user_id, board.turn, board.current_color, board.to_bytes(), board.is_end())
    messages = SERVER_DOMAIN + board.to_image(user_id)
    return messages


# 盤面をリセットしてメッセージを生成
def reset_board(req: Dict) -> List[str]:
    database.update_end(req['source']['userId'])
    board = Board(None, None, None)
    database.create(req['source']['userId'], board.turn, board.current_color, board.to_bytes(), False)
    first_player = 'ボク(白)' if board.current_color == WHITE else 'あなた(黒)'
    messages = [SERVER_DOMAIN + board.to_image(req['source']['userId']), 'リセットしたよ\n先攻は' + first_player + 'だよ']
    if board.current_color == WHITE:
        messages.append(act_enemy(board, req['source']['userId']))
    messages.append('次の手を指定してね')
    return messages


# 履歴を生成して盤面を生成
def show_history(user_id: str) -> List[str]:
    image_paths = []
    board_history = database.read_all(user_id)
    if len(board_history) == 0:
        return ['対戦履歴がないよ']
    for bh in board_history:
        board_reproduced = Board(bh[0], bh[1], bh[2])
        image_paths.append(board_reproduced.to_image(user_id))
    video_path = make_video(image_paths, user_id)
    messages = [SERVER_DOMAIN + video_path, '対戦履歴だよ']
    return messages


# 対戦終了後の処理
def finalize(board: Board, user_id: str) -> List[str]:
    messages = [board.judge_winner()]
    #messages += show_history(user_id) # メッセージ数の上限に引っかかるのでコメントアウト
    messages[-1] += '\n対戦履歴を見たい場合は「対戦履歴」を入力してね\nもう一回プレイするには「リセット」を入力してね'
    return messages


# 座標を取得して一手進める
def move_forward(req: Dict) -> List[str]:
    turn, color, board = database.read(req['source']['userId']) # ユーザの最後の履歴を読み込む
    board = Board(turn, color, board) # 履歴から盤面を構築（履歴がなければ初期盤面）
    messages = [SERVER_DOMAIN + board.to_image(req['source']['userId'])]
    logging.debug(messages[-1])
    put_x, put_y = pos2xy(req['message']['text']) # 入力されたメッセージを座標に変換

    if put_x is None or put_y is None:
        messages.append('xyで指定してね')

    elif board.put_disc(put_x, put_y):
        messages = [SERVER_DOMAIN + board.to_image(req['source']['userId'])]
        database.create(req['source']['userId'], board.turn, board.current_color, board.to_bytes(), board.is_end())
        if board.is_end():
            messages += finalize(board, req['source']['userId'])
        # 白の番なら自動で置く(パスもあるのでループで)
        while not board.is_end() and board.current_color == WHITE:
            messages.append(act_enemy(board, req['source']['userId']))
            if board.is_end():
                messages += finalize(board, req['source']['userId'])
        if not board.is_end():
            messages.append('次の手を指定してね')

    else:
        messages.append('そこには置けないよ\nもう一度座標を指定してね')

    return messages


# 「/」にPOSTリクエストが来た場合、index関数が実行される
@app.route('/', methods=['post'])
def index():
    body_binary = request.get_data()
    request_body = json.loads(body_binary.decode())

    # イベントの中身があったら返信する
    if request_body['events'] is not None: # 先にreturn
        request_event = request_body['events'][0]
        if request_event['type'] == 'message' and request_event.get('message', {}).get('type') == 'text':
            # 特定のメッセージが来たときにオセロをリセットする
            if request_event['message']['text'] in RESET_WORDS:
                messages = reset_board(request_event)
            elif request_event['message']['text'] in HISTORY_WORDS:
                messages = show_history(request_event['source']['userId'])
            else:
                messages = move_forward(request_event)
                logging.debug(f'メッセージ：{messages}')

            # 返信用ヘッダ、ボディの作成
            headers, response_body = make_response(messages, request_event['replyToken'])
            # LINE APIに返信したい内容を送信
            res = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, data=json.dumps(response_body))
            logging.debug(res.text)
            # POST後即削除だとLINEで見れなかった
            #for msg in response_body['messages']:
            #    if msg['type'] == 'image':
            #        os.remove(msg['originalContentUrl'].replace(SERVER_DOMAIN, './'))
            #    elif msg['type'] == 'video':
            #        os.remove(msg['originalContentUrl'].replace(SERVER_DOMAIN, './'))
        
        elif request_event['type'] == 'follow' and request_event['source']['type'] == 'user':
            # 返信用ヘッダ、ボディの作成
            messages = [
                'ようこそ！\nボクとオセロをしよう！',
                'あなたは常に黒で、先行はランダムに決まるよ',
                'まずはリセットを押して対戦を始めよう！'
            ]
            headers, response_body = make_response(messages, request_event['source']['userId'], is_push=True)
            requests.post('https://api.line.me/v2/bot/message/push', headers=headers, data=json.dumps(response_body))
    return 'OK', 200
