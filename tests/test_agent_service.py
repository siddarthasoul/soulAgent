from src.services.agent_service import AgentService


def run_test(
    agent_service: AgentService,
    number: int,
    user_query: str,
) -> None:
    print("=" * 80)
    print(f"TEST {number}")
    print("=" * 80)
    print("USER QUERY")
    print("-" * 80)
    print(user_query)
    print()

    try:
        result = agent_service.handle_user_message(
            user_query
        )

        print("QUERY ROUTE")
        print("-" * 80)
        print(result.route)
        print()

        print("DISPATCH PATH")
        print("-" * 80)
        print(result.dispatch_path)
        print()

        print("AGENT")
        print("-" * 80)
        print(result.agent)
        print()

        print("RESPONSE")
        print("-" * 80)
        print(result.response)
        print()

        if result.visualization is not None:
            print("VISUALIZATION")
            print("-" * 80)
            print(result.visualization)
            print()

    except Exception as exc:
        print("ERROR")
        print("-" * 80)
        print(type(exc).__name__)
        print(exc)
        print()


def main() -> None:
    agent_service = AgentService()

    test_queries = [

    # ==============================================================
    # PHYSICS — CALCULATIONS
    # ==============================================================

    "A cyclist starts from rest and reaches 12 m/s in 6 seconds. "
    "What is the acceleration?",

    "A 10 kg box is pushed with a net force of 35 N. "
    "What acceleration does it have?",

    "An object moves at 8 m/s for 15 seconds. "
    "How far does it travel?",

    "A car moving at 25 m/s slows down to 5 m/s in 4 seconds. "
    "What is its acceleration?",

    "A 2 kg object is moving at 6 m/s. "
    "What is its momentum?",


    # ==============================================================
    # PHYSICS — CONCEPTUAL
    # ==============================================================

    "What is the difference between mass and weight?",

    "Why does increasing the mass of an object make it harder "
    "to accelerate with the same force?",


    # ==============================================================
    # CHEMISTRY — CALCULATIONS
    # ==============================================================

    "What is the molar mass of H2SO4?",

    "What is the molar mass of NaCl?",

    "What is the molar mass of Al2(SO4)3?",


    # ==============================================================
    # CHEMISTRY — REASONING
    # ==============================================================

    "What is the difference between an atom and a molecule?",

    "Explain why water is considered a polar molecule.",


    # ==============================================================
    # MATH — CALCULATIONS
    # ==============================================================

    "Solve 3x + 7 = 22.",

    "What is the derivative of x^3 + 2x^2 - 5x?",

    "Calculate the determinant of [[4, 2], [3, 1]].",


    # ==============================================================
    # MULTI-TASK
    # ==============================================================

    "Explain Newton's second law and calculate the acceleration "
    "of a 12 kg object when a force of 48 N acts on it.",

    "Explain kinetic energy and calculate the kinetic energy "
    "of a 4 kg object moving at 10 m/s.",

]

    
    for number, query in enumerate(
        test_queries,
        start=1,
    ):
        run_test(
            agent_service=agent_service,
            number=number,
            user_query=query,
        )


if __name__ == "__main__":
    main()