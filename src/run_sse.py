import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from sse import SSEHandler
from server import create_server
import logging

logger = logging.getLogger(__name__)

def main():
    server, init_options = create_server()
    sse_handler = SSEHandler(server, init_options)

    routes = [
        Route("/sse", endpoint=sse_handler.handle_sse),
        Mount("/messages/", app=sse_handler.sse.handle_post_message)
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