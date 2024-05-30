class BinarySemaphore:
    """
    Represents a binary semaphore (thread lock) with two states, locked and unlocked
    and methods to acquire and release the lock.

    See Also:
        https://en.m.wikipedia.org/wiki/Semaphore_(programming)
    """

    def __init__(self):
        self.locked = False
        self.attempting_acquisition = False

    def is_locked(self):
        """
        Returns True if the semaphore is locked or an acquisition attempt is in progress, False otherwise.
        """
        return self.locked or self.attempting_acquisition

    def acquire(self):
        """
        Acquires the lock. If the lock is already held by another thread, this method will block until the lock is released.
        """
        self.attempting_acquisition = True
        while self.locked:
            pass
        self.locked = True
        self.attempting_acquisition = False

    def release(self):
        """
        Releases the lock.
        """
        self.locked = False
