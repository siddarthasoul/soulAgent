from src.tools.registry import ToolRegistry


def add(a: int, b: int) -> int:
    return a + b


def main() -> None:
    registry = ToolRegistry()

    registry.register("add", add)

    assert registry.has("add")
    assert registry.get("add") is add
    assert registry.list_tools() == ["add"]

    print("ToolRegistry test passed")


if __name__ == "__main__":
    main()