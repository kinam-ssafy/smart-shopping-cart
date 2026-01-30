using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Models;
using smart_shopping_cart_back.Data;

namespace smart_shopping_cart_back.Services;

public interface ISearchService
{
    Task<SearchDefaultResponseDto> SearchDefaultAsync(CancellationToken ct);
    Task<List<ProductDto>> SearchByNameAsync(string query, CancellationToken ct);
}