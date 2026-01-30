using smart_shopping_cart_back.Handlers;
using smart_shopping_cart_back.Services;

namespace smart_shopping_cart_back.BackgroundServices;

/// <summary>
/// MQTT 연결을 관리하는 백그라운드 서비스
/// - 서버 시작 시 MQTT 브로커에 연결
/// - 연결 끊기면 자동 재연결
/// - 메시지 수신 시 핸들러로 전달
/// </summary>
public class MqttHostedService : BackgroundService
{
    private readonly MqttService _mqtt;
    private readonly SseService _sse;
    private readonly PositionService _position;
    private readonly CartMessageHandler _handler;
    private readonly ILogger<MqttHostedService> _logger;
    private readonly IConfiguration _config;

    // 재연결 대기 시간 (5초)
    private readonly TimeSpan _reconnectDelay = TimeSpan.FromSeconds(5);

    public MqttHostedService(
        MqttService mqtt,
        SseService sse,
        PositionService position,
        CartMessageHandler handler,
        IConfiguration config,
        ILogger<MqttHostedService> logger)
    {
        _mqtt = mqtt;
        _sse = sse;
        _position = position;
        _handler = handler;
        _config = config;
        _logger = logger;
    }

    /// <summary>
    /// 백그라운드 서비스 실행 (서버 시작 시 자동 호출)
    /// </summary>
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var positionTopic = _config["Mqtt:PositionTopic"] ?? "cart/1/position";

        // MQTT 메시지 수신 핸들러 등록
        _mqtt.OnMessageReceived += async (topic, payload) =>
        {
            // 위치 토픽 처리
            if (topic == positionTopic)
            {
                _position.HandlePositionMessage(payload);
                return;
            }

            // 장바구니 토픽 처리
            await _handler.HandleAsync(topic, payload, _sse);
        };

        // 연결 유지 루프
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                // MQTT 브로커 연결
                if (!_mqtt.IsConnected)
                {
                    _logger.LogInformation("[MQTT] 브로커 연결 시도...");
                    await _mqtt.ConnectAndSubscribeAsync();
                    _logger.LogInformation("[MQTT] 브로커 연결 완료!");
                }

                // 연결 상태 유지 (1초마다 체크)
                await Task.Delay(1000, stoppingToken);
            }
            catch (OperationCanceledException)
            {
                // 서버 종료 시 정상 종료
                break;
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"[MQTT] 연결 실패: {ex.Message}. {_reconnectDelay.TotalSeconds}초 후 재시도...");
                await Task.Delay(_reconnectDelay, stoppingToken);
            }
        }
    }

    /// <summary>
    /// 서비스 종료 시 호출
    /// </summary>
    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("[MQTT] 서비스 종료 중...");
        await _mqtt.DisconnectAsync();
        await base.StopAsync(cancellationToken);
    }
}
