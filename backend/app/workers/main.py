"""
Worker base para tareas asíncronas futuras.
Por ahora sirve como punto de expansión para:
- Reportes pesados
- Notificaciones por email/WhatsApp
- Conciliación de pagos
- Generación de PDFs de tickets
"""

import asyncio

from app.core.logging import configure_logging, logger


async def main():
    configure_logging()

    logger.info("worker_started")

    while True:
        try:
            await asyncio.sleep(60)

            logger.debug("worker_heartbeat")

        except asyncio.CancelledError:
            logger.info("worker_stopped")
            break
        except Exception as exc:
            logger.error("worker_error", error=str(exc))
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
