from typing import Any


# For now we disable all type-checking in the monte-carlo submodule.
def __getattr__(name) -> Any: ...
