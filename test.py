from tools.registry import ToolRegistry

registry = ToolRegistry()
registry.discover_tools()
tools = registry.list_tools()
for tool in tools:
    print(f"\nTool: {tool['name']}")
    print(f"Description: {tool['description']}")
    print("Parameters:")
    for param_name, param_info in tool['parameters'].items():
        print(f"  - {param_name}: {param_info.get('description', 'No description')}")
