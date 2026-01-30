namespace smart_shopping_cart_back.Models;

/// <summary>
/// 매장 지도 API 응답 DTO
/// </summary>
public class MapDataDto
{
    public StoreMapDto StoreMap { get; set; } = new();
    public List<FixtureDto> Fixtures { get; set; } = new();
}

public class StoreMapDto
{
    public string Id { get; set; } = "1";
    public string Version { get; set; } = "1";
    /// <summary>
    /// 매장 경계 좌표 배열 [[x, y], ...]
    /// </summary>
    public List<double[]> Boundary { get; set; } = new();
    public string Units { get; set; } = "meters";
}

public class FixtureDto
{
    public string Id { get; set; } = "";
    public string Label { get; set; } = "";
    public string ParentCategoryId { get; set; } = "";
    public string CategoryName { get; set; } = "";
    /// <summary>
    /// 선반 geometry 좌표 배열 [[x, y], ...]
    /// </summary>
    public List<double[]> Geometry { get; set; } = new();
}
