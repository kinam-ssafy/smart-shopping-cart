namespace smart_shopping_cart_back.DTOs;

public sealed record SearchDefaultResponseDto(
    List<CardTemplateDto> Popular,
    List<CardTemplateDto> Recommended
);