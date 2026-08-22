from backend.location import calculate_distance


def test_same_location():

    distance = calculate_distance(
        13.0827,
        80.2707,
        13.0827,
        80.2707
    )

    assert distance == 0


def test_distance_is_positive():

    distance = calculate_distance(
        13.0827,
        80.2707,
        13.0878,
        80.2785
    )

    assert distance > 0


def test_distance_is_in_kilometers():

    distance = calculate_distance(
        13.0827,
        80.2707,
        13.0878,
        80.2785
    )

    assert distance < 10