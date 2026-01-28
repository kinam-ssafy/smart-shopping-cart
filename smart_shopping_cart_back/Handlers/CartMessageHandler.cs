using smart_shopping_cart_back.Models;
using smart_shopping_cart_back.Services;
using System.Text.Json;

namespace smart_shopping_cart_back.Handlers;

/// <summary>
/// MQTT 메시지 처리 핸들러
/// - cart/1 토픽 메시지를 파싱
/// - DB에 카트 상품 저장
/// - SSE로 상품 정보 브로드캐스트
/// </summary>
public class CartMessageHandler
{
    private readonly ILogger<CartMessageHandler> _logger;
    private readonly CartDbService _cartDb;

    // 기본 카트 ID (향후 동적으로 처리 가능)
    private const int DefaultCartId = 1;

    public CartMessageHandler(ILogger<CartMessageHandler> logger, CartDbService cartDb)
    {
        _logger = logger;
        _cartDb = cartDb;
    }

    /// <summary>
    /// MQTT 메시지 처리
    /// </summary>
    /// <param name="topic">수신된 토픽</param>
    /// <param name="payload">수신된 JSON 메시지</param>
    /// <param name="sse">SSE 서비스</param>
    public async Task HandleAsync(string topic, string payload, SseService sse)
    {
        try
        {
            // JSON 파싱
            var message = JsonSerializer.Deserialize<CartMessage>(payload);

            if (message?.Uids == null)
            {
                _logger.LogWarning($"[Handler] 유효하지 않은 메시지: {payload}");
                return;
            }

            _logger.LogInformation($"[Handler] UID 수신: {message.Uids.Length}개");

            // 1. DB에 카트 상품 목록 저장
            await _cartDb.UpdateCartItemsAsync(DefaultCartId, message.Uids);

            // 2. RFID UID로 상품 상세 정보 조회
            var products = await _cartDb.GetProductsByRfidUidsAsync(message.Uids);

            // 3. SSE로 상품 정보 브로드캐스트
            await sse.BroadcastProductsAsync(products);

            _logger.LogInformation($"[Handler] 상품 정보 전송: {products.Count}개");
        }
        catch (JsonException ex)
        {
            _logger.LogError($"[Handler] JSON 파싱 실패: {ex.Message}");
        }
        catch (Exception ex)
        {
            _logger.LogError($"[Handler] 처리 실패: {ex.Message}");
        }
    }
}
