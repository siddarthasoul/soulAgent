from src.agents.math.agent import MathAgent
from src.core.context import AgentContext
from src.tools.calculator.tool import MathTool


def main() -> None:
    context = AgentContext(
        request_id="math-test-1",
        user_message="Calculate 2 + 3",
    )

    context.tools.register(
        "math",
        MathTool(),
    )

    agent = MathAgent()

    result = agent.run(
        user_message="Calculate 2 + 3",
        use_tool=True,
        context=context,
    )

    print("RESULT:", result)

    assert result == "5.0"

    print("MathAgent context test passed")


if __name__ == "__main__":
    main()