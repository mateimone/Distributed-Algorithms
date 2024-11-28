from typing import Set, List

from typing_extensions import override

from cs4545.implementation import DolevAlgorithm
from cs4545.system.da_types import *

@dataclass(msg_id=5)
class EchoMessage:
    id: str
    content: str
    path: Path
    time: float

@dataclass(msg_id=6)
class ReadyMessage:
    id: str
    content: str
    path: Path
    time: float

class BrachaAlgorithm(DolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
