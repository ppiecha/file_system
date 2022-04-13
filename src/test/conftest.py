import pytest

from src.app.model.favorite import Favorite, Favorites


@pytest.fixture(name="favorite1")
def fixture_favorite1() -> Favorite:
    return Favorite(name="test_favorite1", description="test_favorite1", path="c:\\")


@pytest.fixture()
def favorite2() -> Favorite:
    return Favorite(name="test_favorite2", description="test_favorite2", path="d:\\")


@pytest.fixture
def empty_favorites() -> Favorites:
    return Favorites()


@pytest.fixture
def one_item_favorites(favorite1) -> Favorites:
    return Favorites(items=[favorite1], selected=favorite1)
