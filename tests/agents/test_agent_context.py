from src.core.context import AgentContext
from src.tools.calculator.tool import MathTool


def main() -> None:
    context = AgentContext(
        request_id="test-123",
        user_message="Calculate 2 + 2",
    )

    context.tools.register(
        "math",
        MathTool(),
    )

    math_tool = context.tools.get("math")

    result = math_tool.run(
        tool="calculator",
        operation="run",
        arguments={
            "expression": "2 + 2",
        },
    )

    assert result == 4.0

    print("AgentContext tool execution passed")
    print("RESULT:", result)


if __name__ == "__main__":
    main()