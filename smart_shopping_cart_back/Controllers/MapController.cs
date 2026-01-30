using Microsoft.AspNetCore.Mvc;
using smart_shopping_cart_back.Services;
using System.Text.Json;

namespace smart_shopping_cart_back.Controllers;

/// <summary>
/// 매장 지도 API 컨트롤러
/// - 매장 경계 및 선반 위치 조회
/// - 실시간 위치 SSE 스트리밍
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class MapController : ControllerBase
{
    private readonly MapService _mapService;
    private readonly PositionService _positionService;
    private readonly ILogger<MapController> _logger;

    public MapController(
        MapService mapService,
        PositionService positionService,
        ILogger<MapController> logger)
    {
        _mapService = mapService;
        _positionService = positionService;
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

    /// <summary>
    /// 실시간 위치 SSE 스트림
    /// GET /api/map/position/stream
    /// 
    /// 카트 위치를 실시간으로 전송 (약 6-7 FPS)
    /// </summary>
    [HttpGet("position/stream")]
    public async Task GetPositionStream(CancellationToken cancellationToken)
    {
        Response.ContentType = "text/event-stream";
        Response.Headers.CacheControl = "no-cache";
        Response.Headers.Connection = "keep-alive";

        _logger.LogInformation("[Position SSE] 클라이언트 연결");

        // 초기 위치 전송 (있으면)
        var currentPosition = _positionService.CurrentPosition;
        if (currentPosition != null)
        {
            await SendPositionEventAsync(currentPosition);
        }

        // 위치 업데이트 이벤트 핸들러
        var tcs = new TaskCompletionSource<bool>();
        Action<Models.CartPositionDto> positionHandler = async (position) =>
        {
            try
            {
                await SendPositionEventAsync(position);
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"[Position SSE] 전송 실패: {ex.Message}");
                tcs.TrySetResult(true);
            }
        };

        _positionService.OnPositionUpdated += positionHandler;

        try
        {
            // 연결 유지 (취소될 때까지)
            await Task.WhenAny(
                tcs.Task,
                Task.Delay(Timeout.Infinite, cancellationToken)
            );
        }
        catch (OperationCanceledException)
        {
            // 정상 종료
        }
        finally
        {
            _positionService.OnPositionUpdated -= positionHandler;
            _logger.LogInformation("[Position SSE] 클라이언트 연결 해제");
        }
    }

    private async Task SendPositionEventAsync(Models.CartPositionDto position)
    {
        var json = JsonSerializer.Serialize(new
        {
            x = position.X,
            y = position.Y,
            theta = position.Theta,
            timestamp = position.Timestamp
        });

        await Response.WriteAsync($"data: {json}\n\n");
        await Response.Body.FlushAsync();
    }
}
