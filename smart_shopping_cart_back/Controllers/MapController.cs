using Microsoft.AspNetCore.Mvc;
using smart_shopping_cart_back.Services;

namespace smart_shopping_cart_back.Controllers;

/// <summary>
/// 매장 지도 API 컨트롤러
/// - 매장 경계 및 선반 위치 조회
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class MapController : ControllerBase
{
    private readonly MapService _mapService;
    private readonly ILogger<MapController> _logger;

    public MapController(MapService mapService, ILogger<MapController> logger)
    {
        _mapService = mapService;
        _logger = logger;
    }

    /// <summary>
    /// 매장 지도 데이터 조회
    /// GET /api/map
    /// 
    /// 반환: 매장 경계 + 선반 위치/카테고리 정보
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> GetMapData([FromQuery] string mapId = "1")
    {
        try
        {
            var mapData = await _mapService.GetMapDataAsync(mapId);
            return Ok(mapData);
        }
        catch (Exception ex)
        {
            _logger.LogError($"[Map] 지도 조회 실패: {ex.Message}");
            return StatusCode(500, new { error = "지도 조회 실패", message = ex.Message });
        }
    }
}
