from enum import Enum

class ConversationType(str , Enum):
    DIRECT = "direct"
    GROUP = "group"


class MemberRole(str , Enum):
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"


class MessageType(str , Enum):
    TEXT = "text"
    SYSTEM = "system"


class NotificationType(str, Enum):
    NEW_MESSAGE = "new_message"
    ADDED_TO_GROUP = "added_to_group"
    REMOVED_FROM_GROUP = "removed_from_group"
    PROMOTED_TO_ADMIN = "promoted_to_admin"