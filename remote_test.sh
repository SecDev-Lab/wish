#!/bin/bash

# リモートホストでのテストスクリプト
echo "Testing Sliver connection on remote host (kali.local)..."
ssh kali.local << 'EOF'
  # ログディレクトリの作成
  mkdir -p ~/.wish/logs

  # 設定ファイルの確認
  echo "Checking Sliver config file..."
  if [ -f ~/wish_127.0.0.1.cfg ]; then
    echo "Config file exists: ~/wish_127.0.0.1.cfg"
    ls -la ~/wish_127.0.0.1.cfg
  else
    echo "Config file not found: ~/wish_127.0.0.1.cfg"
    echo "Please check the path to the Sliver config file."
    exit 1
  fi

  # Sliver接続のテスト
  echo "Testing Sliver connection..."
  python3 -c "
import sys
try:
  from sliver import SliverClient, SliverClientConfig
  import asyncio
  import os

  async def test():
      config_path = os.path.expanduser('~/wish_127.0.0.1.cfg')
      print(f'Using config file: {config_path}')
      config = SliverClientConfig.parse_config_file(config_path)
      client = SliverClient(config)
      print('Connecting to Sliver server...')
      await client.connect()
      print('Connected to Sliver server')
      sessions = await client.sessions()
      print(f'Sessions: {sessions}')
      if sessions:
          session_id = sessions[0].ID
          print(f'Using session ID: {session_id}')
          session = await client.interact_session(session_id)
          print(f'Connected to session: {session}')
          # ターゲットOSに応じてコマンドを変換
          os_type = session.os.lower()
          print(f'Target OS: {os_type}')
          if 'windows' in os_type:
              print(f'Target OS is Windows, using cmd.exe')
              test_cmd = 'cmd.exe /C echo test'
          else:
              test_cmd = 'echo test'
              
          if 'windows' in os_type:
              # Windowsの場合、コマンドを分割
              cmd = 'cmd.exe'
              args = ['/C', 'echo', 'test']
              print(f'Executing test command: {cmd} with args {args}')
              result = await session.execute(cmd, args)
          else:
              # Linux/macOSの場合
              cmd_parts = test_cmd.split()
              cmd = cmd_parts[0]
              args = cmd_parts[1:] if len(cmd_parts) > 1 else []
              print(f'Executing test command: {cmd} with args {args}')
              result = await session.execute(cmd, args)
          stdout = result.Stdout.decode() if result.Stdout else None
          print(f'Command result: {stdout}')
          
          # systeminfo コマンドも同様に変換
          if 'windows' in os_type:
              systeminfo_cmd = 'cmd.exe /C systeminfo'
          else:
              systeminfo_cmd = 'systeminfo'
              
          if 'windows' in os_type:
              # Windowsの場合、コマンドを分割
              cmd = 'cmd.exe'
              args = ['/C', 'systeminfo']
              print(f'Executing systeminfo command: {cmd} with args {args}')
              result = await session.execute(cmd, args)
          else:
              # Linux/macOSの場合
              cmd = 'systeminfo'
              args = []
              print(f'Executing systeminfo command: {cmd} with args {args}')
              result = await session.execute(cmd, args)
          stdout = result.Stdout.decode() if result.Stdout else None
          print(f'systeminfo result: {stdout}')
      else:
          print('No sessions found')

  asyncio.run(test())
except Exception as e:
  print(f'Error: {e}')
  import traceback
  traceback.print_exc()
  sys.exit(1)
"
EOF

echo "Remote test completed."
