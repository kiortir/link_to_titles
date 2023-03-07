class RetriesExceededException(Exception):
    pass


class StreamTimeout(Exception):
    pass


class TaskCallableNotRegistered(Exception):
    pass