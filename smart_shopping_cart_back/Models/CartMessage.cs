using System.Text.Json.Serialization;

namespace smart_shopping_cart_back.Models;

/// <summary>
/// MQTT로 수신되는 카트 메시지 형식
/// </summary>
public class CartMessage
{
    /// <summary>
    /// 상품 UID 배열
    /// </summary>
    [JsonPropertyName("uids")]
    public string[] Uids { get; set; } = Array.Empty<string>();

    /// <summary>
    /// 메시지 시간
    /// </summary>
    [JsonPropertyName("time")]
    public string Time { get; set; } = "";
}
