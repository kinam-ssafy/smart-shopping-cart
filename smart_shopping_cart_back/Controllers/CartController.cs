using Microsoft.AspNetCore.Mvc;
using smart_shopping_cart_back.Services;
using smart_shopping_cart_back.Models;

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
    private readonly CartDbService _cartDb;
    private readonly ILogger<CartController> _logger;

    // 기본 카트 ID (향후 동적으로 처리 가능)
    private const int DefaultCartId = 1;

    public CartController(
        MqttService mqtt, 
        SseService sse, 
        CartDbService cartDb,
        ILogger<CartController> logger)
    {
        _mqtt = mqtt;
        _sse = sse;
        _cartDb = cartDb;
        _logger = logger;
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
    /// 현재 카트 상품 목록 조회
    /// GET /api/cart/items
    /// </summary>
    [HttpGet("items")]
    public async Task<IActionResult> GetCartItems()
    {
        try
        {
            var products = await _cartDb.GetCartProductsAsync(DefaultCartId);
            return Ok(new { products });
        }
        catch (Exception ex)
        {
            _logger.LogError($"[Cart] 상품 조회 실패: {ex.Message}");
            return StatusCode(500, new { error = "상품 조회 실패" });
        }
    }

    /// <summary>
    /// SSE 연결 - 실시간 카트 상품 스트림
    /// GET /api/cart/stream
    /// 
    /// 1. 연결 시 DB에서 현재 카트 상품 조회하여 전송
    /// 2. 이후 MQTT 업데이트 시 실시간 전송
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
            // 1. 연결 즉시 DB에서 현재 카트 상품 조회하여 전송
            var currentProducts = await _cartDb.GetCartProductsAsync(DefaultCartId);
            await _sse.SendToClientAsync(Response, currentProducts);
            _logger.LogInformation($"[SSE] 초기 상품 전송: {currentProducts.Count}개");

            // 2. 연결 유지 (MQTT 업데이트 시 BroadcastProductsAsync로 전송됨)
            await Task.Delay(Timeout.Infinite, cancellationToken);
        }
        catch (TaskCanceledException)
        {
            // 클라이언트가 연결을 끊음 (정상)
        }
        catch (Exception ex)
        {
            _logger.LogError($"[SSE] 스트림 오류: {ex.Message}");
        }
        finally
        {
            _sse.RemoveClient(clientId);
        }
    }
}
