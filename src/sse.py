from starlette.responses import Response
from mcp.server.sse import SseServerTransport
import logging

logger = logging.getLogger(__name__)

class SSEHandler:
    def __init__(self, server, init_options):
        self.server = server
        self.init_options = init_options
        self.sse = SseServerTransport("/messages/")

    async def handle_sse(self, request):
        async with self.sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await self.server.run(
                streams[0], streams[1],
                self.init_options
            )

