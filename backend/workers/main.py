from __future__ import annotations

import asyncio

from backend.core.config import get_settings
from backend.core.database import get_sessionmaker
from backend.core.logging import configure_logging
from backend.workers.worker import WorkerRuntime


async def async_main() -> None:
    configure_logging()
    settings = get_settings()
    worker = WorkerRuntime(worker_id=settings.worker_id, queue_name=settings.queue_name)
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        await worker.run_once(db)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
