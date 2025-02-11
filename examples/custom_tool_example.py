import asyncio
from smartpup import Pup, ToolRegistry, BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform basic arithmetic operations"
    
    async def execute(
        self,
        operation: str,
        a: float,
        b: float
    ) -> str:
        """
        Perform basic arithmetic
        
        Args:
            operation: One of 'add', 'subtract', 'multiply', 'divide'
            a: First number
            b: Second number
        """
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return "Error: Cannot divide by zero"
                result = a / b
            else:
                return f"Error: Unknown operation '{operation}'"
            
            return f"Result of {a} {operation} {b} = {result}"
            
        except Exception as e:
            return f"Error performing calculation: {str(e)}"

async def main():
    # Initialize and register tool
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool)
    
    # Create calculator pup
    calculator_pup = Pup(
        instructions="You are a math assistant. Use the calculator tool to perform calculations.",
        tools=registry.get_tools(["calculator"])
    )

    # Run one calculation
    response = await calculator_pup.run("What is 15 divided by 0.3?")
    print(f"Answer: {response}")

if __name__ == "__main__":
    asyncio.run(main()) 