class Pair:
    def __init__(self, first, second):
        """
        Represents a generic pair of values.

        Args:
            first: The first element of the pair.
            second: The second element of the pair.
        """
        self._first = first
        self._second = second

    @property
    def first(self):
        """
        Get the first element of the pair.

        Returns:
            The first element.
        """
        return self._first

    @property
    def second(self):
        """
        Get the second element of the pair.

        Returns:
            The second element.
        """
        return self._second

    @classmethod
    def of(cls, first, second):
        """
        Create a Pair object with the given elements.

        Args:
            first: The first element of the pair.
            second: The second element of the pair.

        Returns:
            A Pair object with the specified elements.
        """
        return cls(first, second)
