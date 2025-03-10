import asyncio
import logging
import os
from pathlib import Path
from sliver import SliverClient, SliverClientConfig

async def main():
    # ログディレクトリの作成
    log_dir = Path(os.path.expanduser("~/.wish/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # ログファイルの設定
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "sliver_test.log", mode='w'),
            logging.StreamHandler()  # 標準出力にも出力
        ]
    )
    
    logger = logging.getLogger()
    logger.info("Starting Sliver API test")
    
    # ユーザーが実際に使用しているパスを使用
    config_path = os.path.expanduser("~/wish_127.0.0.1.cfg")
    logger.info(f"Using config file: {config_path}")
    
    # 設定ファイルが存在するか確認
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        print(f"Config file not found: {config_path}")
        print("Please provide the correct path to the Sliver config file:")
        print("1. Check the path you used in the command: uv run wish --sliver-config ~/wish_127.0.0.1.cfg")
        print("2. Make sure the file exists at that location")
        return
    logger.info(f"Using config file: {config_path}")
    
    try:
        config = SliverClientConfig.parse_config_file(config_path)
        client = SliverClient(config)
        
        # Connect to server
        logger.info("Connecting to Sliver server")
        await client.connect()
        logger.info("Connected to Sliver server")
        
        # Get session list
        logger.info("Getting session list")
        sessions = await client.sessions()
        logger.info(f"Sessions: {sessions}")
        
        if sessions:
            session_id = sessions[0].ID
            logger.info(f"Using session ID: {session_id}")
            
            # Connect to the session
            logger.info("Connecting to session")
            session = await client.interact_session(session_id)
            logger.info(f"Connected to session: {session}")
            
            # Execute a test command
            test_cmd = "systeminfo"
            logger.info(f"Executing test command: {test_cmd}")
            result = await session.execute(test_cmd, [])
            logger.info(f"Command executed, status: {result.Status}")
            
            if result.Stdout:
                stdout = result.Stdout.decode('utf-8')
                logger.info(f"Stdout: {stdout}")
            else:
                logger.warning("No stdout received")
                
            if result.Stderr:
                stderr = result.Stderr.decode('utf-8')
                logger.info(f"Stderr: {stderr}")
        else:
            logger.error("No sessions found")
    except Exception as e:
        logger.exception(f"Error in Sliver API test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
