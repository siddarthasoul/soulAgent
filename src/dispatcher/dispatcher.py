from common.types.router import QueryRoute, TaskType


class Dispatcher:

    def dispatch(self, route: QueryRoute) -> list[str]:
        path: list[str] = []

        if route.needs_search:
            path.append("search")

        if route.needs_planning:
            path.append("planner")

        for task in route.tasks:
            path.append(task.type.value)

        if route.complexity == "complex":
            path.append("verify")

        return path
