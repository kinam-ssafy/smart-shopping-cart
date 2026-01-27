using Microsoft.AspNetCore.Mvc;

namespace smart_shopping_cart_back.Controllers;

/// <summary>
/// 헬스체크 API 컨트롤러
/// - 서버 상태 확인용 엔드포인트 제공
/// </summary>
[ApiController]
[Route("/")]  // → / (루트 경로)
public class HealthController : ControllerBase
{
    /// <summary>
    /// 서버 헬스체크
    /// GET /
    /// </summary>
    /// <returns>서버 상태 정보 (status, timestamp, service명)</returns>
    [HttpGet]
    public IActionResult Get()
    {
        return Ok(new
        {
            status = "healthy",          // 서버 상태
            timestamp = DateTime.UtcNow, // 현재 시간 (UTC)
            service = "smart_shopping_cart_back"  // 서비스명
        });
    }
}
