import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Disable reload in production
    is_production = os.getenv("RENDER", False) or os.getenv("PRODUCTION", False)
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,
        log_level="info"
    )