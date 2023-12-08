from __future__ import annotations

from typing import Dict, List, Literal, TypedDict


class Ad(TypedDict):
    id: str
    url: str
    place: str
    ratio: int
    imageUrl: str
    dayOfWeek: int


class Policies(TypedDict):
    gtlAvailable: bool
    ltlAvailable: bool
    canPublicNote: bool
    canCreateContent: bool
    canUpdateContent: bool
    canDeleteContent: bool
    canInvite: bool
    inviteLimit: int
    inviteLimitCycle: int
    inviteExpirationTime: int
    canManageCustomEmojis: bool
    canManageAvatarDecorations: bool
    canSearchNotes: bool
    canUseTranslator: bool
    canHideAds: bool
    driveCapacityMb: int
    alwaysMarkNsfw: bool
    pinLimit: int
    antennaLimit: int
    wordMuteLimit: int
    webhookLimit: int
    clipLimit: int
    noteEachClipsLimit: int
    userListLimit: int
    userEachUserListsLimit: int
    rateLimitFactor: int


class Meta(TypedDict):
    maintainerName: str
    maintainerEmail: str
    version: str
    name: str
    shortName: str | None
    uri: str
    description: str
    langs: List[str]
    tosUrl: str
    repositoryUrl: str
    feedbackUrl: str
    impressumUrl: str | None
    privacyPolicyUrl: str | None
    disableRegistration: bool
    emailRequiredForSignup: bool
    enableHcaptcha: bool
    hcaptchaSiteKey: str
    enableRecaptcha: bool
    recaptchaSiteKey: str
    enableTurnstile: bool
    turnstileSiteKey: str
    swPublickey: str
    themeColor: str
    mascotImageUrl: str
    bannerUrl: str
    infoImageUrl: str | None
    serverErrorImageUrl: str | None
    notFoundImageUrl: str | None
    iconUrl: str
    backgroundImageUrl: str
    logoImageUrl: str
    maxNoteTextLength: int
    defaultLightTheme: str | None
    defaultDarkTheme: str | None
    ads: List[Ad]
    notesPerOneAd: int
    enableEmail: bool
    enableServiceWorker: bool
    translatorAvailable: bool
    serverRules: List[str]
    policies: Policies
    mediaProxy: str


class Emoji(TypedDict):
    aliases: List[str]
    name: str
    category: str
    url: str
    roleIdsThatCanBeUsedThisEmojiAsReaction: List[str]


class Emojis(TypedDict):
    emojis: List[Emoji]


class AvatarDecoration(TypedDict):
    id: str
    angle: float
    url: str


class BadgeRole(TypedDict):
    name: str
    iconUrl: str
    displayOrder: int


class User(TypedDict):
    id: str
    name: str
    username: str
    host: str | None
    avatarUrl: str
    avatarBlurhash: str
    avatarDecorations: List[AvatarDecoration]
    isBot: bool
    isCat: bool
    emojis: Dict
    onlineStatus: Literal["online"]
    badgeRoles: List[BadgeRole]


class ImageFilePropertiy(TypedDict):
    width: int
    height: int


class File(TypedDict):
    id: str
    createdAt: str
    name: str
    type: str
    md5: str
    size: int
    isSensitive: bool
    blurhash: str
    properties: ImageFilePropertiy
    url: str
    thumbnailUrl: str
    comment: str | None
    folderId: str | None
    folder: str | None
    userId: str | None
    user: str | None


class Note(TypedDict):
    id: str
    createdAt: str
    userId: str
    user: User
    text: str | None
    cw: str | None
    visibility: Literal["public"]
    localOnly: bool
    reactionAcceptance: str | None
    renoteCount: int
    repliesCount: int
    reactions: Dict[str, int]
    reactionEmojis: Dict
    reactionAndUserPairCache: List[str]
    fileIds: List[str]
    files: List[File]
    replyId: str | None
    renoteId: str | None
    clippedCount: int
    renote: Note | None


class Field(TypedDict):
    name: str
    value: str


class Role(TypedDict):
    id: str
    name: str
    color: str | None
    iconUrl: str | None
    description: str | None
    isModerator: bool
    isAdministrator: bool
    displayOrder: int


class UserDetail(TypedDict):
    id: str
    name: str
    username: str
    host: str | None
    avatarUrl: str
    avatarBlurhash: str
    avatarDecorations: List[AvatarDecoration]
    isBot: bool
    isCat: bool
    emojis: Dict
    onlineStatus: Literal["online"]
    badgeRoles: List[BadgeRole]
    url: str
    uri: str
    movedTo: str | None
    alsoKnownAs: str | None
    createdAt: str
    updatedAt: str
    lastFetechedAt: str | None
    bannerUrl: str | None
    bannerBlurhash: str | None
    isLocked: bool
    isSilenced: bool
    isLimited: bool
    isSuspended: bool
    description: str | None
    location: str | None
    birthday: str | None
    lang: str | None
    fields: List[Field]
    verifiedLinks: List
    followersCount: int
    followingCount: int
    notesCount: int
    pinnedNoteIds: List[str]
    pinnedNotes: List[Note]
    pinnedPageId: None
    pinnedPage: None
    publicReactions: bool
    ffVisibility: Literal["public"]
    twoFactorEnabled: bool
    usePasswordLessLogin: bool
    securityKeys: bool
    roles: List[Role]
    memo: str | None
    isFollowing: bool
    isFollowed: bool
    hasPendingFollowRequestFromYou: bool
    hasPendingFollowRequestToYou: bool
    isBlocking: bool
    isBlocked: bool
    isMuted: bool
    isRenoteMuted: bool
    notify: Literal["none"]
    withReplies: bool
