public sealed record ReviewForCardDto(
    Guid ReviewId,
    string ImageUrl,
    string? ImageAltText,
    int Rating,
    string? Content,
    DateTimeOffset CreatedAt
);