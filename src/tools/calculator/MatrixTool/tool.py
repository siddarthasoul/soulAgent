import math


class MatrixTool:


    def add(
        self,
        a: list[list[float]],
        b: list[list[float]],
    ) -> list[list[float]]:
        self._validate_same_shape(a, b)

        return [
            [
                x + y
                for x, y in zip(row_a, row_b)
            ]
            for row_a, row_b in zip(a, b)
        ]

    def subtract(
        self,
        a: list[list[float]],
        b: list[list[float]],
    ) -> list[list[float]]:
        self._validate_same_shape(a, b)

        return [
            [
                x - y
                for x, y in zip(row_a, row_b)
            ]
            for row_a, row_b in zip(a, b)
        ]

    def scalar_multiply(
        self,
        matrix: list[list[float]],
        scalar: float,
    ) -> list[list[float]]:
        self._validate_matrix(matrix)

        return [
            [
                scalar * value
                for value in row
            ]
            for row in matrix
        ]

    def multiply(
        self,
        a: list[list[float]],
        b: list[list[float]],
    ) -> list[list[float]]:
        self._validate_matrix(a)
        self._validate_matrix(b)

        a_rows = len(a)
        a_cols = len(a[0])
        b_rows = len(b)
        b_cols = len(b[0])

        if a_cols != b_rows:
            raise ValueError(
                "Matrix dimensions are incompatible "
                "for multiplication."
            )

        return [
            [
                sum(
                    a[i][k] * b[k][j]
                    for k in range(a_cols)
                )
                for j in range(b_cols)
            ]
            for i in range(a_rows)
        ]

    def transpose(
        self,
        matrix: list[list[float]],
    ) -> list[list[float]]:
        self._validate_matrix(matrix)

        return [
            list(column)
            for column in zip(*matrix)
        ]

    def determinant(
        self,
        matrix: list[list[float]],
    ) -> float:
        self._validate_square(matrix)

        return self._determinant(matrix)

    def inverse(
        self,
        matrix: list[list[float]],
    ) -> list[list[float]]:
        self._validate_square(matrix)

        determinant = self.determinant(matrix)

        if math.isclose(determinant, 0.0):
            raise ValueError(
                "Matrix is singular and cannot be inverted."
            )

        n = len(matrix)

        if n == 1:
            return [[1.0 / matrix[0][0]]]

        if n == 2:
            a, b = matrix[0]
            c, d = matrix[1]

            return [
                [d / determinant, -b / determinant],
                [-c / determinant, a / determinant],
            ]

        augmented = [
            [
                float(value)
                for value in row
            ]
            + [
                1.0 if i == j else 0.0
                for j in range(n)
            ]
            for i, row in enumerate(matrix)
        ]

        for column in range(n):
            pivot = max(
                range(column, n),
                key=lambda row: abs(
                    augmented[row][column]
                ),
            )

            if math.isclose(
                augmented[pivot][column],
                0.0,
            ):
                raise ValueError(
                    "Matrix is singular and cannot be inverted."
                )

            augmented[column], augmented[pivot] = (
                augmented[pivot],
                augmented[column],
            )

            pivot_value = augmented[column][column]

            augmented[column] = [
                value / pivot_value
                for value in augmented[column]
            ]

            for row in range(n):
                if row == column:
                    continue

                factor = augmented[row][column]

                augmented[row] = [
                    current - factor * pivot_value
                    for current, pivot_value in zip(
                        augmented[row],
                        augmented[column],
                    )
                ]

        return [
            row[n:]
            for row in augmented
        ]

    def rank(
        self,
        matrix: list[list[float]],
    ) -> int:
        self._validate_matrix(matrix)

        matrix = [
            [float(value) for value in row]
            for row in matrix
        ]

        rows = len(matrix)
        columns = len(matrix[0])

        rank = 0

        for column in range(columns):
            pivot = None

            for row in range(rank, rows):
                if not math.isclose(
                    matrix[row][column],
                    0.0,
                ):
                    pivot = row
                    break

            if pivot is None:
                continue

            matrix[rank], matrix[pivot] = (
                matrix[pivot],
                matrix[rank],
            )

            pivot_value = matrix[rank][column]

            matrix[rank] = [
                value / pivot_value
                for value in matrix[rank]
            ]

            for row in range(rows):
                if row == rank:
                    continue

                factor = matrix[row][column]

                matrix[row] = [
                    current - factor * pivot_value
                    for current, pivot_value in zip(
                        matrix[row],
                        matrix[rank],
                    )
                ]

            rank += 1

            if rank == rows:
                break

        return rank

    def trace(
        self,
        matrix: list[list[float]],
    ) -> float:
        self._validate_square(matrix)

        return sum(
            matrix[i][i]
            for i in range(len(matrix))
        )

    def solve(
        self,
        matrix: list[list[float]],
        vector: list[float],
    ) -> list[float]:
        self._validate_square(matrix)

        if len(matrix) != len(vector):
            raise ValueError(
                "Matrix and vector dimensions do not match."
            )

        inverse = self.inverse(matrix)

        result = [
            sum(
                inverse[i][j] * vector[j]
                for j in range(len(vector))
            )
            for i in range(len(inverse))
        ]

        return result

    def eigenvalues(
        self,
        matrix: list[list[float]],
    ) -> list[float]:
        self._validate_square(matrix)

        if len(matrix) != 2:
            raise ValueError(
                "Eigenvalue calculation currently "
                "supports 2x2 matrices."
            )

        a, b = matrix[0]
        c, d = matrix[1]

        trace = a + d
        determinant = a * d - b * c

        discriminant = (
            trace**2 - 4 * determinant
        )

        if discriminant < 0:
            raise ValueError(
                "Complex eigenvalues are not supported."
            )

        root = math.sqrt(discriminant)

        return [
            (trace + root) / 2,
            (trace - root) / 2,
        ]

    @staticmethod
    def _validate_matrix(
        matrix: list[list[float]],
    ) -> None:
        if not matrix:
            raise ValueError(
                "Matrix cannot be empty."
            )

        if not all(isinstance(row, list) for row in matrix):
            raise ValueError(
                "Matrix must be a list of rows."
            )

        if not all(matrix):
            raise ValueError(
                "Matrix rows cannot be empty."
            )

        columns = len(matrix[0])

        if any(
            len(row) != columns
            for row in matrix
        ):
            raise ValueError(
                "Matrix rows must have equal length."
            )

        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            for row in matrix
            for value in row
        ):
            raise ValueError(
                "Matrix must contain only numbers."
            )

    def _validate_square(
        self,
        matrix: list[list[float]],
    ) -> None:
        self._validate_matrix(matrix)

        if len(matrix) != len(matrix[0]):
            raise ValueError(
                "Matrix must be square."
            )

    def _validate_same_shape(
        self,
        a: list[list[float]],
        b: list[list[float]],
    ) -> None:
        self._validate_matrix(a)
        self._validate_matrix(b)

        if (
            len(a) != len(b)
            or len(a[0]) != len(b[0])
        ):
            raise ValueError(
                "Matrices must have the same shape."
            )

    def _determinant(
        self,
        matrix: list[list[float]],
    ) -> float:
        n = len(matrix)

        if n == 1:
            return float(matrix[0][0])

        if n == 2:
            return (
                matrix[0][0] * matrix[1][1]
                - matrix[0][1] * matrix[1][0]
            )

        determinant = 0.0

        for column in range(n):
            minor = [
                [
                    matrix[row][j]
                    for j in range(n)
                    if j != column
                ]
                for row in range(1, n)
            ]

            sign = 1 if column % 2 == 0 else -1

            determinant += (
                sign
                * matrix[0][column]
                * self._determinant(minor)
            )

        return determinant
