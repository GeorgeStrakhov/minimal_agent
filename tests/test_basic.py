import pytest
import asyncio
from smartpup import Pup, ToolRegistry, BaseTool

# A simple test tool
class EchoTool(BaseTool):
    name = "echo"
    description = "Repeats the input"
    
    async def execute(
        self,
        message: str
    ) -> str:
        """
        Echo the input message
        
        Args:
            message: Message to echo back
        """
        return f"Echo: {message}"

@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.register_tool(EchoTool)
    return reg

@pytest.mark.asyncio
async def test_basic_tool_execution(registry):
    """Test that a pup can use a basic tool"""
    pup = Pup(
        instructions="You are an echo bot. Use the echo tool to repeat what the user says.",
        tools=registry.get_tools(["echo"])
    )
    
    response = await pup.run("Please echo 'hello world'")
    assert "Echo: hello world" in response

@pytest.mark.asyncio
async def test_tool_discovery():
    """Test that built-in tools can be discovered"""
    registry = ToolRegistry()
    registry.discover_tools()
    
    tools = registry.list_tools()
    assert len(tools) > 0
    assert any(t["name"] == "get_current_weather" for t in tools)
    assert any(t["name"] == "remember" for t in tools)

@pytest.mark.asyncio
async def test_tool_registration():
    """Test that custom tools can be registered"""
    registry = ToolRegistry()
    registry.register_tool(EchoTool)
    
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "echo" 