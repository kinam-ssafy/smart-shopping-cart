using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Pgvector;

namespace smart_shopping_cart_back.Services;

public class EmbeddingService : IEmbeddingService
{
    private readonly HttpClient _http;
    private readonly string _apiKey;
    private readonly string _model;
    private const string BaseUrl = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings";

    public EmbeddingService(HttpClient http, IConfiguration config)
    {
        _http = http;
        _apiKey = config["GMS_KEY"] ?? throw new InvalidOperationException("GMS_KEY missing");
        _model = config["OpenAI:Model"] ?? "text-embedding-3-small";
    }

    public async Task<Vector> EmbedAsync(string text, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(text))
            throw new ArgumentException("Embedding input text is empty.", nameof(text));

        text = text.Trim();

        using var req = new HttpRequestMessage(HttpMethod.Post, BaseUrl);
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _apiKey);

        var payload = new
        {
            model = _model,
            input = text
        };

        req.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

        using var resp = await _http.SendAsync(req, ct);
        var body = await resp.Content.ReadAsStringAsync(ct);

        if (!resp.IsSuccessStatusCode)
            throw new InvalidOperationException($"Embedding API failed: {(int)resp.StatusCode} {resp.ReasonPhrase}\n{body}");

        using var doc = JsonDocument.Parse(body);
        var arr = doc.RootElement
            .GetProperty("data")[0]
            .GetProperty("embedding")
            .EnumerateArray()
            .Select(x => (float)x.GetDouble())
            .ToArray();

        if (arr.Length != 1536)
            throw new InvalidOperationException($"Unexpected embedding length: {arr.Length}");

        return new Vector(arr);
    }
}