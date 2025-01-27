import subprocess
import shutil
import os
import mysql.connector

from langchain.agents import Tool
from dotenv import load_dotenv
from urllib.parse import urlparse


class MariaDBTool:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Option 1: Using URI
        uri = os.getenv('MARIADB_URI')
        if uri:
            parsed = urlparse(uri)
            self.host = parsed.hostname
            self.port = parsed.port
            self.user = parsed.username
            self.password = parsed.password
            self.database = parsed.path.lstrip('/')
        else:
            # Option 2: Using separate variables
            self.host = os.getenv('MARIADB_HOST', 'localhost')
            self.port = int(os.getenv('MARIADB_PORT', '3306'))
            self.user = os.getenv('MARIADB_USER')
            self.password = os.getenv('MARIADB_PASSWORD')
            self.database = os.getenv('MARIADB_DATABASE')

        # Test connection
        self.test_connection()

    def test_connection(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                collation='utf8mb4_general_ci'

            )
            conn.close()
        except mysql.connector.Error as e:
            raise ConnectionError(f"Failed to connect to MariaDB: {e}")

    def execute_command(self, command):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                collation='utf8mb4_general_ci'

            )
            cursor = conn.cursor()
            cursor.execute(command)
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except mysql.connector.Error as e:
            raise ConnectionError(f"Failed to connect to MariaDB: {e}")


def get_mariadb_tool() -> Tool:
    """Create and return a MariaDB Tool for use with LangGraph."""
    tool = MariaDBTool()
    return Tool(
        name="MariaDB Tool",
        func=tool.execute_command,
        description="Executes MariaDB CLI commands to manage MariaDB databases. Common commands: SHOW DATABASES, USE [db], SHOW TABLES, SELECT * FROM [table]"
    )
