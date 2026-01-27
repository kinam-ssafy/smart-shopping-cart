using System.Collections.Concurrent;
using System.Text.Json;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// SSE(Server-Sent Events) 서비스
/// - SSE 연결 관리
/// - MQTT 메시지를 SSE로 브로드캐스트
/// </summary>
public class SseService
{
    // 연결된 SSE 클라이언트 목록 (Thread-safe)
    private readonly ConcurrentDictionary<string, HttpResponse> _clients = new();
    private readonly ILogger<SseService> _logger;

    public SseService(ILogger<SseService> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// 새 SSE 클라이언트 등록
    /// </summary>
    public string AddClient(HttpResponse response)
    {
        var clientId = Guid.NewGuid().ToString();
        _clients.TryAdd(clientId, response);
        _logger.LogInformation($"[SSE] 클라이언트 연결: {clientId} (총 {_clients.Count}명)");
        return clientId;
    }

    /// <summary>
    /// SSE 클라이언트 제거
    /// </summary>
    public void RemoveClient(string clientId)
    {
        _clients.TryRemove(clientId, out _);
        _logger.LogInformation($"[SSE] 클라이언트 해제: {clientId} (총 {_clients.Count}명)");
    }

    /// <summary>
    /// 모든 SSE 클라이언트에게 UID 배열 전송
    /// </summary>
    public async Task BroadcastUidsAsync(string[] uids)
    {
        var data = JsonSerializer.Serialize(new { uids });
        var message = $"data: {data}\n\n";

        foreach (var (clientId, response) in _clients)
        {
            try
            {
                await response.WriteAsync(message);
                await response.Body.FlushAsync();
            }
            catch (Exception)
            {
                // 연결 끊긴 클라이언트 제거
                RemoveClient(clientId);
            }
        }
    }
}
