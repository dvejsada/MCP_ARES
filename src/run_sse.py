import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from sse import SSEHandler
from server import create_server
import logging

logger = logging.getLogger(__name__)

def main():
    server, init_options = create_server()
    sse_handler = SSEHandler(server, init_options)

    routes = [
        Route("/sse", endpoint=sse_handler.handle_sse),
        Route("/messages", endpoint=sse_handler.handle_messages, methods=["POST"])
    ]

    app = Starlette(routes=routes)
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8956,
        log_level="debug",
        log_config=None
    )

    server = uvicorn.Server(config)
    try:
        server.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()