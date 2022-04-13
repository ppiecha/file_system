def test_create_item_from_empty(empty_favorites, favorite2):
    empty_favorites.create_item(new_favorite=favorite2)
    assert len(empty_favorites.items) == 1
    assert empty_favorites.items[0].dict() == favorite2.dict()


def test_create_item_from_one_item(one_item_favorites, favorite1, favorite2):
    one_item_favorites.create_item(current_favorite=favorite1, new_favorite=favorite2)
    assert len(one_item_favorites.items) == 1
    assert favorite1.children[0].dict() == favorite2.dict()


def test_create_item_top_level(one_item_favorites, favorite1, favorite2):
    one_item_favorites.create_item(new_favorite=favorite2)
    assert len(one_item_favorites.items) == 2
    assert one_item_favorites.items == [favorite1, favorite2]


def test_delete_item_top_level(empty_favorites, favorite2):
    empty_favorites.create_item(new_favorite=favorite2)
    empty_favorites.delete_item(current_favorite=favorite2)
    print(empty_favorites.items)
    assert len(empty_favorites.items) == 0


def test_delete_item_from_one_item(empty_favorites, favorite1, favorite2):
    empty_favorites.create_item(new_favorite=favorite1)
    empty_favorites.create_item(current_favorite=favorite1, new_favorite=favorite2)
    empty_favorites.delete_item(current_favorite=favorite2)
    assert len(empty_favorites.items) == 1
    assert empty_favorites.items[0] == favorite1
