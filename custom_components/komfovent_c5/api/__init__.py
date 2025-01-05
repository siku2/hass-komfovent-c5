from .client import Client

# import order matters
...

from .alarms import *  # noqa: E402, F403
from .functions import *  # noqa: E402, F403
from .modes import *  # noqa: E402, F403
from .monitoring import *  # noqa: E402, F403
from .service import *  # noqa: E402, F403
from .settings import *  # noqa: E402, F403

_ = Client


def determine_is_extended(*, version: int) -> bool:
    # okay so this is obviously scuffed and the entire concept of 'is extended' probably isn't correct either.
    # Right now I just don't have enough information to determine whether the available registers are based on the
    # version or the model type.
    #
    # Current working theory is that it's the version and v2 introduced a bunch of new registers across all models.
    #
    # for now this provides some additional compatibility until more users come along and provide further information.
    return version >= 2000
