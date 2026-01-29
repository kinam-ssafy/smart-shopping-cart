public sealed record CardTemplateDto(
    string ProductId,
    string Name,
    decimal Price,
    string? LocationText,
    string Bay,
    int Level,
    int PositionIndex,
    int Stock,
    bool Active,
    double AvgRating,
    List<ProductImageForCardDto> Images,
    List<ReviewForCardDto> Reviews
);

public sealed record ProductImageForCardDto(
    Guid ProductImageId,
    string ImageUrl,
    string? ImageAltText,
    int SortOrder
);

public sealed record ReviewForCardDto(
    Guid ReviewId,
    string ImageUrl,
    string? ImageAltText,
    int Rating,
    string? Content,
    DateTimeOffset CreatedAt
);

public sealed record SearchDefaultResponseDto(
    List<CardTemplateDto> Popular,
    List<CardTemplateDto> Recommended
);
