import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from ares_call import ARES
import logging


def create_server():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("mcp-ares")
    logger.setLevel(logging.DEBUG)
    logger.info("Starting MCP Ares")

    # Initialize base MCP server
    server = Server("mcp-ares")

    init_options = InitializationOptions(
        server_name="mcp-ares",
        server_version="0.1",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        List available tools.
        Each tool specifies its arguments using JSON Schema validation.
        """
        return [
            types.Tool(
                name="get-company-info-by-name",
                description="Get information about any Czech company from public register based on name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Czech company to find information on in public register (e.g. ČEZ, a.s.)",
                        },
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="get-company-info-by-id-number",
                description="Get information about any Czech company from public register based on identification number",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id_number": {
                            "type": "string",
                            "description": "Identification number (in Czech 'IČO') of the Czech company to find information on in public register (e.g. 26858974)",
                        },
                    },
                    "required": ["id_number"],
                },
            ),
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

        if name == "get-company-info-by-name":
            company_name = arguments.get("name")
            if not company_name:
                raise ValueError("Missing name parameter")

            result_text = await ARES.get_base_data(company_name, "name")

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        elif name == "get-company-info-by-id-number":
            company_id = arguments.get("id_number")
            if not company_id:
                raise ValueError("Missing Id. number parameter")

            result_text = await ARES.get_base_data(company_id, "id")

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    return server, init_options


