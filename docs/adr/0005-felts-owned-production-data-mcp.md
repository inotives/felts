# Use a Felts-owned MCP server for production analytical access

Felts will expose production analytical data through a small project-owned MCP server
with `list_views`, `describe_view`, and `query` tools instead of connecting agents
directly through a generic PostgreSQL MCP. The extra policy layer is justified because
Felts must enforce an explicit schema-qualified view allowlist, query bounds, and
metadata-only auditing independently of agent prompts and PostgreSQL read-only
permissions.
