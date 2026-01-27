using MQTTnet;
using System.Text;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// MQTT 브로커 통신 서비스
/// - 브로커 연결/해제
/// - 토픽 구독
/// - 메시지 수신 이벤트 발생
/// </summary>
public class MqttService
{
    private IMqttClient? _client;
    private readonly IConfiguration _config;
    private readonly ILogger<MqttService> _logger;

    /// <summary>
    /// MQTT 메시지 수신 이벤트
    /// </summary>
    public event Func<string, string, Task>? OnMessageReceived;

    /// <summary>
    /// 연결 상태
    /// </summary>
    public bool IsConnected => _client?.IsConnected ?? false;

    public MqttService(IConfiguration config, ILogger<MqttService> logger)
    {
        _config = config;
        _logger = logger;
    }

    /// <summary>
    /// MQTT 브로커에 연결하고 토픽 구독
    /// </summary>
    public async Task ConnectAndSubscribeAsync()
    {
        _client = new MqttClientFactory().CreateMqttClient();

        var broker = _config["Mqtt:Broker"] ?? "localhost";
        var port = int.Parse(_config["Mqtt:Port"] ?? "1883");
        var topic = _config["Mqtt:Topic"] ?? "cart/1";
        var username = _config["Mqtt:Username"];
        var password = _config["Mqtt:Password"];

        // 연결 옵션 빌더
        var optionsBuilder = new MqttClientOptionsBuilder()
            .WithTcpServer(broker, port)
            .WithClientId($"smart-cart-backend-{Guid.NewGuid()}");

        // 인증 정보가 있으면 추가
        if (!string.IsNullOrEmpty(username) && !string.IsNullOrEmpty(password))
        {
            optionsBuilder.WithCredentials(username, password);
            _logger.LogInformation($"[MQTT] 인증 사용: {username}");
        }

        var options = optionsBuilder.Build();

        // 메시지 수신 핸들러
        _client.ApplicationMessageReceivedAsync += async e =>
        {
            var t = e.ApplicationMessage.Topic;
            var p = Encoding.UTF8.GetString(e.ApplicationMessage.Payload);

            _logger.LogInformation($"[MQTT] 수신: {t}");

            if (OnMessageReceived != null)
            {
                await OnMessageReceived.Invoke(t, p);
            }
        };

        // 연결
        await _client.ConnectAsync(options);
        _logger.LogInformation($"[MQTT] 브로커 연결됨: {broker}:{port}");

        // 토픽 구독
        var subscribeOptions = new MqttClientSubscribeOptionsBuilder()
            .WithTopicFilter(topic)
            .Build();

        await _client.SubscribeAsync(subscribeOptions);
        _logger.LogInformation($"[MQTT] 토픽 구독: {topic}");
    }

    /// <summary>
    /// 연결 해제
    /// </summary>
    public async Task DisconnectAsync()
    {
        if (_client != null && _client.IsConnected)
        {
            await _client.DisconnectAsync();
            _logger.LogInformation("[MQTT] 연결 해제됨");
        }
    }
}
