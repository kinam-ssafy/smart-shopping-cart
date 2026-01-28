public sealed record CardTemplateDto(
    string ProductId,
    string Name,
    decimal Price,
    string? LocationText, // you can later replace with category path
    string Bay,
    int Level,
    int PositionIndex,
    int Stock,
    bool Active,
    double AvgRating,
    List<ProductImageForCardDto> Images,
    List<ReviewForCardDto> Reviews
);