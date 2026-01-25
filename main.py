import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno antes de importar módulos que dependen de ellas
load_dotenv()

# Asegurar que el directorio src/ esté en sys.path para permitir imports tipo `server.*`
ROOT = Path(__file__).parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from logger.logger import get_logger

logger = get_logger("ServerMain")

async def main():
    logger.info("Server starting")
    try:
        from mcp_server import mcp
        await mcp.run_stdio_async()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
