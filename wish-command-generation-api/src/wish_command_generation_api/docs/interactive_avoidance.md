# 対話回避

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
