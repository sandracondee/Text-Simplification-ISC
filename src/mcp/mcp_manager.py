import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

class MCPManager:
    def __init__(self):
        self.configs = {
            "metrics_server": {
                "url": os.getenv("MCP_METRICS_SERVER_URL"),
                "transport": "streamable_http"
            },
            "search_server": {
                "url": os.getenv("MCP_SEARCH_SERVER_URL"),
                "transport": "streamable_http"
            }
        }
        self._clients_cache = {}
        self._tools_cache = {}

    async def get_tools_for_agent(self, server_names: list):
        """
        Devuelve las herramientas solicitadas. 
        Si ya se conectó a esos servidores antes, reutiliza la conexión.
        """
        cache_key = tuple(sorted(server_names))

        if cache_key not in self._tools_cache:
            filtered_config = {k: v for k, v in self.configs.items() if k in server_names}
            client = MultiServerMCPClient(filtered_config)
            self._clients_cache[cache_key] = client
            self._tools_cache[cache_key] = await client.get_tools()

        return self._tools_cache[cache_key]

mcp_manager = MCPManager()