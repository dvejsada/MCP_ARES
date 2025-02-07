# What is it?

A [Model Context Protocol](https://modelcontextprotocol.io/) Server running over SSE

# What it offers?

Tools for LLM to get current information on Czech companies from company register (incl. Commercial Register), Register of Beneficial Owners and check insolvency register.

Company information may be fetched either by name or by ID number.

# What do I need?

MCP Client, such is Claude Desktop or [LibreChat](https://github.com/danny-avila/LibreChat)

# How to run this?

Using Docker with precompiled image as per docker-compose.yml. App is listening on port 8956.

## How to add to LibreChat

In your librechat.yaml file, add the following section:

```yaml
mcpServers:
  mcp-ares:
    type: sse # type can optionally be omitted
    url: URL of your docker container # e.g. http://localhost:8956/sse
```

## How to use in LibreChat

After the server is added to LibreChat as per above, restart LibreChat to connect to MCP server and discover tools. Then, create an agent and add the respective tools to agent.

When the agent is created, you may ask the agent to get you seat address of the company, ask how the company may sign a contract etc.