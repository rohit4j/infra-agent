from langchain.agents import Tool
import requests

class KongTool:
    def __init__(self, admin_url: str = "http://localhost:8001"):
        self.admin_url = admin_url.rstrip('/')
        self._verify_connection()

    def _verify_connection(self):
        try:
            response = requests.get(f"{self.admin_url}/")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Cannot connect to Kong Admin API: {str(e)}")

    def execute_command(self, command: str) -> str:
        try:
            method, endpoint = command.split(maxsplit=1)
            url = f"{self.admin_url}/{endpoint.lstrip('/')}"
            
            response = requests.request(
                method=method.upper(),
                url=url,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Kong API request failed: {str(e)}")

def get_kong_tool() -> Tool:
    try:
        tool = KongTool()
        return Tool(
            name="Kong Gateway Tool",
            func=tool.execute_command,
            description="Manages Kong Gateway via Admin API. Commands: 'GET /services', 'GET /routes', 'GET /plugins'"
        )
    except ConnectionError as e:
        print(f"Warning: Kong Tool initialization failed - {str(e)}")
        raise ConnectionError(f"Warning: Kong Tool initialization failed - {str(e)}")
        # return None