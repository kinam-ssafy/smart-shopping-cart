using Microsoft.AspNetCore.Mvc;

namespace smart_shopping_cart_back.Controllers;

[ApiController]
[Route("/")]
public class HealthController : ControllerBase
{
    [HttpGet]
    public IActionResult Get()
    {
        return Ok(new
        {
            status = "healthy",
            timestamp = DateTime.UtcNow,
            service = "smart_shopping_cart_back"
        });
    }
}
