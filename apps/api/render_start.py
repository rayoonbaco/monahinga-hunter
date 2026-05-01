# PASS 15 - Render readiness (port + safe startup)

import os
import uvicorn

from apps.api.main import app  # reuse existing app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8010"))
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=port, reload=False)
