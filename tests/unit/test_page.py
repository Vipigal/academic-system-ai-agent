import pytest

from api.application.page import DEFAULT_LIMIT, FIRST_PAGE, MAX_LIMIT, PageRequest

ITEMS = tuple(range(45))
NO_ITEMS: tuple[int, ...] = ()


def test_page_request_is_read_from_the_arguments_of_a_tool_call() -> None:
    assert PageRequest.model_validate({"offset": 20}) == PageRequest(offset=20)
    assert set(PageRequest.model_json_schema()["properties"]) == {"offset", "limit"}


def test_first_page_is_the_default_request() -> None:
    assert PageRequest(offset=0, limit=DEFAULT_LIMIT) == FIRST_PAGE


def test_first_page_points_to_the_next_offset() -> None:
    page = PageRequest().paginate(ITEMS)

    assert page.items == ITEMS[:DEFAULT_LIMIT]
    assert page.info.offset == 0
    assert page.info.limit == DEFAULT_LIMIT
    assert page.info.total == 45
    assert page.info.next_offset == 20


def test_middle_page_carries_the_requested_window() -> None:
    page = PageRequest(offset=20, limit=10).paginate(ITEMS)

    assert page.items == ITEMS[20:30]
    assert page.info.next_offset == 30


def test_last_page_has_no_next_offset() -> None:
    page = PageRequest(offset=40, limit=10).paginate(ITEMS)

    assert page.items == ITEMS[40:]
    assert page.info.next_offset is None


def test_page_ending_exactly_on_the_total_has_no_next_offset() -> None:
    page = PageRequest(offset=35, limit=10).paginate(ITEMS)

    assert page.items == ITEMS[35:]
    assert page.info.next_offset is None


def test_empty_set_has_zero_total_and_no_next_offset() -> None:
    page = PageRequest().paginate(NO_ITEMS)

    assert page.items == ()
    assert page.info.total == 0
    assert page.info.next_offset is None


def test_offset_past_the_end_keeps_the_total_and_returns_nothing() -> None:
    page = PageRequest(offset=100).paginate(ITEMS)

    assert page.items == ()
    assert page.info.total == 45
    assert page.info.next_offset is None


def test_walking_every_page_returns_each_item_exactly_once() -> None:
    walked: list[int] = []
    next_offset: int | None = 0
    while next_offset is not None:
        page = PageRequest(offset=next_offset, limit=7).paginate(ITEMS)
        walked.extend(page.items)
        next_offset = page.info.next_offset

    assert tuple(walked) == ITEMS


def test_limit_above_the_maximum_is_capped() -> None:
    page = PageRequest(limit=MAX_LIMIT + 1).paginate(tuple(range(MAX_LIMIT + 5)))

    assert page.info.limit == MAX_LIMIT
    assert len(page.items) == MAX_LIMIT
    assert page.info.next_offset == MAX_LIMIT


@pytest.mark.parametrize("limit", [0, -3])
def test_limit_below_one_becomes_one(limit: int) -> None:
    page = PageRequest(limit=limit).paginate(ITEMS)

    assert page.info.limit == 1
    assert page.items == ITEMS[:1]


def test_negative_offset_starts_at_the_beginning() -> None:
    page = PageRequest(offset=-5).paginate(ITEMS)

    assert page.info.offset == 0
    assert page.items == ITEMS[:DEFAULT_LIMIT]
