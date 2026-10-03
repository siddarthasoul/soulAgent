from typing import Any

from rdkit import Chem
from rdkit.Chem import Draw
from src.tools.calculator.tool import MathTool
from chempy import Substance
from chempy import balance_stoichiometry
from rdkit.Chem import rdChemReactions


class ChemistryTool:

    def __init__(self) -> None:
        self.math = MathTool()

    def solve(
        self,
        problem: str,
        arguments: dict[str, Any],
    ) -> Any:

        if not isinstance(problem, str) or not problem.strip():
            raise ValueError("Chemistry problem is required.")

        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary.")

        handlers = {
            "molar_mass": self._molar_mass,
            "balance": self._balance,
            "equation": self._equation,
        }

        handler = handlers.get(problem)

        if handler is None:
            raise ValueError(f"Unsupported chemistry problem: {problem}")

        return handler(**arguments)

    def visualize(
        self,
        type: str,
        arguments: dict[str, Any],
    ) -> Any:

        if not isinstance(type, str) or not type.strip():
            raise ValueError("Visualization type is required.")

        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary.")

        if type == "molecule":
            return self._draw_molecule(**arguments)

        if type == "reaction":
            return self._draw_reaction(**arguments)

        raise ValueError(f"Unsupported visualization type: {type}")

    @staticmethod
    def _molar_mass(
        formula: str,
    ) -> float:

        if not isinstance(formula, str) or not formula.strip():
            raise ValueError("Chemical formula is required.")

        substance = Substance.from_formula(formula)

        return float(substance.molar_mass())

    @staticmethod
    def _balance(
        reactants: list[str],
        products: list[str],
    ) -> dict[str, list[int]]:

        if not reactants:
            raise ValueError("At least one reactant is required.")

        if not products:
            raise ValueError("At least one product is required.")

        reactant_coefficients, product_coefficients = balance_stoichiometry(
            set(reactants),
            set(products),
        )

        return {
            "reactants": [
                reactant_coefficients[compound] for compound in reactants
            ],
            "products": [
                product_coefficients[compound] for compound in products
            ],
        }

    @staticmethod
    def _draw_molecule(
        smiles: str,
        output_path: str = "molecule.png",
    ) -> str:

        if not isinstance(smiles, str) or not smiles.strip():
            raise ValueError("SMILES string is required.")

        molecule = Chem.MolFromSmiles(smiles)

        if molecule is None:
            raise ValueError("Invalid SMILES string.")

        image = Draw.MolToImage(molecule)

        image.save(output_path)

        return output_path

    @staticmethod
    def _draw_reaction(
        reaction_smarts: str,
        output_path: str = "reaction.png",
    ) -> str:

        if not isinstance(reaction_smarts, str) or not reaction_smarts.strip():
            raise ValueError("Reaction SMARTS is required.")

        reaction = rdChemReactions.ReactionFromSmarts(
            reaction_smarts,
            useSmiles=True,
        )

        if reaction is None:
            raise ValueError("Invalid reaction SMARTS.")

        image = Draw.ReactionToImage(reaction)

        image.save(output_path)

        return output_path



    def _equation(
        self,
        equation: str,
        variable: str = "x",
    ) -> list[str]:

        if not isinstance(equation, str) or not equation.strip():
            raise ValueError(
                "Equation cannot be empty."
            )

        if not isinstance(variable, str) or not variable.strip():
            raise ValueError(
                "Variable is required."
            )

        return self.math.run(
            tool="algebra",
            operation="solve",
            arguments={
                "equation": equation,
                "variable": variable,
            },
        )