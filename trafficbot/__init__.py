"""Traffic Bot Pro inspired toolkit."""

from .bot import TrafficBot
from .config import CampaignConfig, VisitProfile
from .scheduler import ScheduledCampaign

__all__ = [
    "TrafficBot",
    "CampaignConfig",
    "VisitProfile",
    "ScheduledCampaign",
    "__version__",
]

__version__ = "1.0.0"
