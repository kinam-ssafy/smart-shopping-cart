namespace smart_shopping_cart_back.DTOs;

public sealed record SearchDefaultDto(
    List<CardTemplateDto> Popular,
    List<CardTemplateDto> Recommended
);