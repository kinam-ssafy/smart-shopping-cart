public sealed record SearchDefaultDto(
    List<CardTemplateDto> Popular,
    List<CardTemplateDto> Recommended
);