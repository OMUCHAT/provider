from typing import List, Literal, NotRequired, TypedDict, Union


class Param(TypedDict):
    key: str
    value: str


class ServiceTrackingParams(TypedDict):
    service: str
    params: List[Param]


class MainAppWebResponseContext(TypedDict):
    loggedOut: bool
    trackingParam: str


class WebResponseContextExtensionData(TypedDict):
    hasDecorated: bool


class ResponseContext(TypedDict):
    serviceTrackingParams: List[ServiceTrackingParams]
    mainAppWebResponseContext: MainAppWebResponseContext
    webResponseContextExtensionData: WebResponseContextExtensionData


class InvalidationId(TypedDict):
    objectSource: int
    objectId: str
    topic: str
    subscribeToGcmTopics: bool
    protoCreationTimestampMs: str


class InvalidationContinuationData(TypedDict):
    invalidationId: InvalidationId
    timeoutMs: int
    continuation: str


class Continuation(TypedDict):
    invalidationContinuationData: NotRequired[InvalidationContinuationData]


class TextRun(TypedDict):
    text: str


class Thumbnail(TypedDict):
    url: str
    width: int
    height: int


class Thumbnails(TypedDict):
    thumbnails: List[Thumbnail]


class AccessibilityData(TypedDict):
    label: str


class Accessibility(TypedDict):
    accessibilityData: AccessibilityData


class Image(TypedDict):
    thumbnails: List[Thumbnail]
    accessibility: Accessibility


class Emoji(TypedDict):
    emojiId: str
    shortcuts: List[str]
    searchTerms: List[str]
    image: Image
    isCustomEmoji: bool


class EmojiRun(TypedDict):
    emoji: Emoji


type Runs = List[Union[TextRun, EmojiRun]]


class Message(TypedDict):
    runs: Runs


class SimpleText(TypedDict):
    simpleText: str


class WebCommandMetadata(TypedDict):
    ignoreNavigation: bool


class CommandMetadata(TypedDict):
    webCommandMetadata: WebCommandMetadata


class LiveChatItemContextMenuEndpoint(TypedDict):
    params: str


class ContextMenuEndpoint(TypedDict):
    commandMetadata: CommandMetadata
    liveChatItemContextMenuEndpoint: LiveChatItemContextMenuEndpoint


class Icon(TypedDict):
    iconType: Literal["OWNER", "MODERATOR"]


class LiveChatAuthorBadgeRenderer(TypedDict):
    customThumbnail: Thumbnails
    tooltip: str
    accessibility: Accessibility
    icon: NotRequired[Icon]


class AuthorBadge(TypedDict):
    liveChatAuthorBadgeRenderer: LiveChatAuthorBadgeRenderer


class ClientResource(TypedDict):
    imageName: str


class Source(TypedDict):
    clientResource: ClientResource


class Sources(TypedDict):
    sources: List[Source]


class ImageTint(TypedDict):
    color: int


class BorderImageProcessor(TypedDict):
    imageTint: ImageTint


class Processor(TypedDict):
    bprderImageProcessor: BorderImageProcessor


class UnheartedIcon(TypedDict):
    sources: List[Source]
    processor: Processor


class CreatorHeartViewModel(TypedDict):
    creatorThumbnail: Thumbnails
    heartedIcon: Sources
    unheartedIcon: UnheartedIcon
    heartedHoverText: str
    heartedAccessibilityLabel: str
    unheartedAccessibilityLabel: str
    engagementStateKey: str


class CreatorHeartButton(TypedDict):
    creatorHeartViewModel: CreatorHeartViewModel


class LiveChatMessageRenderer(TypedDict):
    message: Message
    authorName: SimpleText
    authorPhoto: Thumbnails
    authorBadges: List[AuthorBadge]
    authorExternalChannelId: str
    id: str
    timestampUsec: str


class LiveChatTextMessageRenderer(LiveChatMessageRenderer):
    message: Message
    authorName: SimpleText
    authorPhoto: Thumbnails
    contextMenuEndpoint: ContextMenuEndpoint
    id: str
    timestampUsec: str
    authorBadges: List[AuthorBadge]
    authorExternalChannelId: str
    contextMenuAccessibility: Accessibility


class LiveChatPaidMessageRenderer(LiveChatMessageRenderer):
    id: str
    timestampUsec: str
    authorName: SimpleText
    authorPhoto: Thumbnails
    purchaseAmountText: SimpleText
    message: Message
    headerBackgroundColor: int
    headerTextColor: int
    bodyBackgroundColor: int
    bodyTextColor: int
    authorExternalChannelId: str
    authorNameTextColor: int
    contextMenuEndpoint: ContextMenuEndpoint
    timestampColor: int
    contextMenuAccessibility: Accessibility
    trackingParams: str
    authorBadges: List[AuthorBadge]
    textInputBackgroundColor: int
    creatorHeartButton: CreatorHeartButton
    isV2Style: bool


class MessageItemData(TypedDict):
    liveChatTextMessageRenderer: NotRequired[LiveChatTextMessageRenderer]
    liveChatPaidMessageRenderer: NotRequired[LiveChatPaidMessageRenderer]


class MessageItem(TypedDict):
    item: MessageItemData


class AddChatItemAction(TypedDict):
    addChatItemAction: MessageItem


class MarkChatItemAsDeletedActionData(TypedDict):
    deletedStateMessage: Message
    targetItemId: str


class MarkChatItemAsDeletedAction(TypedDict):
    markChatItemAsDeletedAction: MarkChatItemAsDeletedActionData


type Action = Union[AddChatItemAction, MarkChatItemAsDeletedAction]


class LiveChatContinuation(TypedDict):
    continuations: List[Continuation]
    actions: List[Action]


class ContinuationContents(TypedDict):
    liveChatContinuation: LiveChatContinuation


class Reaction(TypedDict):
    key: str
    value: int


class ReactionData(TypedDict):
    unicodeEmojiId: str
    reactionCount: int


class ReactionBucket(TypedDict):
    reactions: NotRequired[List[Reaction]]
    reactionsData: NotRequired[List[ReactionData]]


class EmojiFountainDataEntity(TypedDict):
    reactionBuckets: List[ReactionBucket]


class Payload(TypedDict):
    emojiFountainDataEntity: NotRequired[EmojiFountainDataEntity]


class Mutation(TypedDict):
    payload: Payload


class EntityBatchUpdate(TypedDict):
    mutations: List[Mutation]


class FrameworkUpdates(TypedDict):
    entityBatchUpdate: EntityBatchUpdate


class Response(TypedDict):
    responseContext: ResponseContext
    continuationContents: ContinuationContents
    frameworkUpdates: NotRequired[FrameworkUpdates]  # reactions
