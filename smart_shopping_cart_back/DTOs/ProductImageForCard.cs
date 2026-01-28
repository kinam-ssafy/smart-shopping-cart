public sealed record ProductImageForCardDto(
    Guid ProductImageId,
    string ImageUrl,
    string? ImageAltText,
    int SortOrder
);