from ipv8.community import CommunitySettings
from cs4545.system.da_types import DistributedAlgorithm


class CrashAlgorithm(DistributedAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)