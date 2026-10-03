import math


class VectorTool:

    def add(
        self,
        a: list[float],
        b: list[float],
    ) -> list[float]:
        self._validate_same_dimension(a, b)

        return [
            x + y
            for x, y in zip(a, b)
        ]

    def subtract(
        self,
        a: list[float],
        b: list[float],
    ) -> list[float]:
        self._validate_same_dimension(a, b)

        return [
            x - y
            for x, y in zip(a, b)
        ]

    def scalar_multiply(
        self,
        vector: list[float],
        scalar: float,
    ) -> list[float]:
        self._validate_vector(vector)

        return [
            scalar * value
            for value in vector
        ]

    def dot(
        self,
        a: list[float],
        b: list[float],
    ) -> float:
        self._validate_same_dimension(a, b)

        return sum(
            x * y
            for x, y in zip(a, b)
        )

    def cross(
        self,
        a: list[float],
        b: list[float],
    ) -> list[float]:
        self._validate_vector(a)
        self._validate_vector(b)

        if len(a) != 3 or len(b) != 3:
            raise ValueError(
                "Cross product requires 3-dimensional vectors."
            )

        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        ]

    def magnitude(
        self,
        vector: list[float],
    ) -> float:
        self._validate_vector(vector)

        return math.sqrt(
            sum(value * value for value in vector)
        )

    def normalize(
        self,
        vector: list[float],
    ) -> list[float]:
        self._validate_vector(vector)

        magnitude = self.magnitude(vector)

        if magnitude == 0:
            raise ValueError(
                "Cannot normalize the zero vector."
            )

        return [
            value / magnitude
            for value in vector
        ]

    def angle(
        self,
        a: list[float],
        b: list[float],
    ) -> float:
        """
        Returns the angle between vectors in radians.
        """
        self._validate_same_dimension(a, b)

        magnitude_a = self.magnitude(a)
        magnitude_b = self.magnitude(b)

        if magnitude_a == 0 or magnitude_b == 0:
            raise ValueError(
                "Angle is undefined for a zero vector."
            )

        cosine = (
            self.dot(a, b)
            / (magnitude_a * magnitude_b)
        )

        # Protect against floating-point errors such as
        # 1.0000000000000002.
        cosine = max(-1.0, min(1.0, cosine))

        return math.acos(cosine)

    @staticmethod
    def _validate_vector(vector: list[float]) -> None:
        if not isinstance(vector, list):
            raise ValueError(
                "Vector must be a list of numbers."
            )

        if not vector:
            raise ValueError(
                "Vector cannot be empty."
            )

        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            for value in vector
        ):
            raise ValueError(
                "Vector must contain only numbers."
            )

    def _validate_same_dimension(
        self,
        a: list[float],
        b: list[float],
    ) -> None:
        self._validate_vector(a)
        self._validate_vector(b)

        if len(a) != len(b):
            raise ValueError(
                "Vectors must have the same dimension."
            )
