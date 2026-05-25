from dataclasses import dataclass
from math import ceil


@dataclass(slots=True)
class PaginationResult:
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationResult:
    total_pages = ceil(total_items / page_size) if total_items > 0 else 0

    return PaginationResult(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )