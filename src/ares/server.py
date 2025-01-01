import mcp.types as types
from mcp.server import Server
from ares_call import ARES


def main():
    """Run the server using sse"""

    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route

    server = Server("mcp-ares")
    sse = SseServerTransport("/messages")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        List available tools.
        Each tool specifies its arguments using JSON Schema validation.
        """
        return [
            types.Tool(
                name="get-company-info",
                description="Get info about any Czech company",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the company to find",
                        },
                    },
                    "required": ["name"],
                },
            )
        ]

    @server.call_tool()
    async def handle_call_tool(
            name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests.
        """
        if not arguments:
            raise ValueError("Missing arguments")

        if name == "get-company-info":
            company_name = arguments.get("name")
            if not company_name:
                raise ValueError("Missing name parameter")

            result_text = await ARES.get_base_data(company_name)

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    async def handle_messages(request):
        # Create a dummy response that we'll return to Starlette
        from starlette.responses import Response

        response = Response("", status_code=202)

        async def send_wrapper(message):
            # Skip sending response since we're handling it at the Starlette level
            if (
                    message["type"] != "http.response.start"
                    and message["type"] != "http.response.body"
            ):
                await request._send(message)

        await sse.handle_post_message(request.scope, request.receive, send_wrapper)
        return response


    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )

    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=8956)

    return 0


