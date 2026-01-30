using Microsoft.AspNetCore.Mvc;
using smart_shopping_cart_back.Services;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Controllers;

[ApiController]
[Route("api/search")]
public class SearchController : ControllerBase
{
    private readonly ISearchService _searchService;

    public SearchController(ISearchService searchService)
    {
        _searchService = searchService;
    }

    // GET /api/search?query=...
    [HttpGet("")]
    public async Task<ActionResult<List<CardTemplateDto>>> Search([FromQuery] string query, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(query))
            return BadRequest(new { error = "query is required" });

        return Ok(await _searchService.SearchByNameAsync(query.Trim(), ct));
    }

    // GET /api/search/default
    [HttpGet("default")]
    public async Task<ActionResult<SearchDefaultResponseDto>> Default(CancellationToken ct)
    {
        return Ok(await _searchService.SearchDefaultAsync(ct));
    }
}