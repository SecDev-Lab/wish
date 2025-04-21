"""Constants for the command generation API."""

# 対話回避のドキュメント
DIALOG_AVOIDANCE_DOC = """# 対話回避

コマンド実行途中でのユーザー入力が不可である点に注意し、以下のように対話を回避すること。

`$LHOST` `$TARGET_IP` などの変数名は、タスク指示から具体的な値を代入すること。

## msfconsole

最後に `exit -y` するのがポイント。

```bash
msfconsole -q -x "use $特定のモジュール; set RHOSTS $TARGET_IP; $他のコマンド... ; exit -y"
```

## smbclient

最後に `-c ''$COMMAND''` とするのがポイント。 `$COMMAND` には `ls` など実行すべきコマンドを当てはめること。

```bash
smbclient -N //$TARGET_IP/$dir --option=''client min protocol''=LANMAN1 -c ''$COMMAND''
```
"""

# 高速な代替コマンドのドキュメント
FAST_ALTERNATIVE_DOC = """# 高速な代替コマンド

## nmap -p- $TARGET_IP

```bash
rustscan -a $TARGET_IP
```

## nmap -p $PORT1,$PORT2 $TARGET_IP

```bash
rustcan -a $TARGET_IP -p $PORT1,$PORT2
```

## nmap -p ${from}-${to} $TARGET_IP

```bash
rustcan -a $TARGET_IP -r ${from}-${to}
```

## nmap (-p以外のオプション) $TARGET_IP

nmap の `-p` オプション以外は、 rustscan の `--` の後に持ってこれる。

```bash
rustscan -a $TARGET_IP -- (-p以外のオプション)
```
"""

# リストファイルのドキュメント
LIST_FILES_DOC = """# リストファイル

辞書攻撃のために、以下のリストファイルの使用を許可する。

## ユーザーリスト

- /usr/share/seclists/Usernames/top-usernames-shortlist.txt

## パスワードリスト

- /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt
"""

# 分割統治のドキュメント
DIVIDE_AND_CONQUER_DOC = """# 分割統治

実行時間の長いコマンドは、コマンドを複数に分割して並列実行（分割統治と呼ぶ）することで高速化が期待できる。
以下の分割統治のみを許可する。

## nmap

before

```bash
nmap -p- $TARGET_IP
```

---

after

```bash
nmap -p1-1000 $TARGET_IP
nmap -p1001-2000 $TARGET_IP
nmap -p2001-3000 $TARGET_IP
nmap -p3001-4000 $TARGET_IP
nmap -p4001-5000 $TARGET_IP
nmap -p5001-6000 $TARGET_IP
nmap -p6001-7000 $TARGET_IP
nmap -p7001-8000 $TARGET_IP
nmap -p8001-9000 $TARGET_IP
nmap -p9001-10000 $TARGET_IP
nmap -p10001-11000 $TARGET_IP
nmap -p11001-12000 $TARGET_IP
nmap -p12001-13000 $TARGET_IP
nmap -p13001-14000 $TARGET_IP
nmap -p14001-15000 $TARGET_IP
nmap -p15001-16000 $TARGET_IP
nmap -p16001-17000 $TARGET_IP
nmap -p17001-18000 $TARGET_IP
nmap -p18001-19000 $TARGET_IP
nmap -p19001-20000 $TARGET_IP
nmap -p20001-21000 $TARGET_IP
nmap -p21001-22000 $TARGET_IP
nmap -p22001-23000 $TARGET_IP
nmap -p23001-24000 $TARGET_IP
nmap -p24001-25000 $TARGET_IP
nmap -p25001-26000 $TARGET_IP
nmap -p26001-27000 $TARGET_IP
nmap -p27001-28000 $TARGET_IP
nmap -p28001-29000 $TARGET_IP
nmap -p29001-30000 $TARGET_IP
nmap -p30001-31000 $TARGET_IP
nmap -p31001-32000 $TARGET_IP
nmap -p32001-33000 $TARGET_IP
nmap -p33001-34000 $TARGET_IP
nmap -p34001-35000 $TARGET_IP
nmap -p35001-36000 $TARGET_IP
nmap -p36001-37000 $TARGET_IP
nmap -p37001-38000 $TARGET_IP
nmap -p38001-39000 $TARGET_IP
nmap -p39001-40000 $TARGET_IP
nmap -p40001-41000 $TARGET_IP
nmap -p41001-42000 $TARGET_IP
nmap -p42001-43000 $TARGET_IP
nmap -p43001-44000 $TARGET_IP
nmap -p44001-45000 $TARGET_IP
nmap -p45001-46000 $TARGET_IP
nmap -p46001-47000 $TARGET_IP
nmap -p47001-48000 $TARGET_IP
nmap -p48001-49000 $TARGET_IP
nmap -p49001-50000 $TARGET_IP
nmap -p50001-51000 $TARGET_IP
nmap -p51001-52000 $TARGET_IP
nmap -p52001-53000 $TARGET_IP
nmap -p53001-54000 $TARGET_IP
nmap -p54001-55000 $TARGET_IP
nmap -p55001-56000 $TARGET_IP
nmap -p56001-57000 $TARGET_IP
nmap -p57001-58000 $TARGET_IP
nmap -p58001-59000 $TARGET_IP
nmap -p59001-60000 $TARGET_IP
nmap -p60001-61000 $TARGET_IP
nmap -p61001-62000 $TARGET_IP
nmap -p62001-63000 $TARGET_IP
nmap -p63001-64000 $TARGET_IP
nmap -p64001-65000 $TARGET_IP
nmap -p65001-65535 $TARGET_IP
```
"""
