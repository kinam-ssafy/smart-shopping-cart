using Microsoft.AspNetCore.Mvc;
using smart_shopping_cart_back.Services;

namespace smart_shopping_cart_back.Controllers;

/// <summary>
/// 카트 SSE API 컨트롤러
/// - SSE 연결 엔드포인트
/// - MQTT 연결 상태 확인
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class CartController : ControllerBase
{
    private readonly MqttService _mqtt;
    private readonly SseService _sse;

    public CartController(MqttService mqtt, SseService sse)
    {
        _mqtt = mqtt;
        _sse = sse;
    }

    /// <summary>
    /// MQTT 연결 상태 확인
    /// GET /api/cart/status
    /// </summary>
    [HttpGet("status")]
    public IActionResult GetStatus()
    {
        return Ok(new
        {
            mqttConnected = _mqtt.IsConnected,
            timestamp = DateTime.UtcNow
        });
    }

    /// <summary>
    /// SSE 연결 - 실시간 UID 스트림
    /// GET /api/cart/stream
    /// </summary>
    [HttpGet("stream")]
    public async Task GetStream(CancellationToken cancellationToken)
    {
        // SSE 헤더 설정
        Response.Headers.Append("Content-Type", "text/event-stream");
        Response.Headers.Append("Cache-Control", "no-cache");
        Response.Headers.Append("Connection", "keep-alive");

        // SSE 클라이언트 등록
        var clientId = _sse.AddClient(Response);

        try
        {
            // 연결 유지 (취소될 때까지 대기)
            await Task.Delay(Timeout.Infinite, cancellationToken);
        }
        catch (TaskCanceledException)
        {
            // 클라이언트가 연결을 끊음 (정상)
        }
        finally
        {
            // 클라이언트 제거
            _sse.RemoveClient(clientId);
        }
    }
}
