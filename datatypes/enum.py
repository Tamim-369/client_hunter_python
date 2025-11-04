from enum import Enum, auto

class LeadStatus(str, Enum):
    NEW = "new"
    MESSAGED = "messaged"
    IN_TALK = "in-talk"
    REJECTED = "rejected"
    CLIENT = "client"
    ARCHIVED = "archived"

class AdSpendIntensity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"