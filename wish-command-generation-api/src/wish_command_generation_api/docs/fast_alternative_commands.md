# 高速な代替コマンド

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
