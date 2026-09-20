from bridge.models import Player


def count_players_by_position(
        players: tuple[Player, ...],
) -> dict[str, int]:
    # Store each position as a key and it player count as the value.
    counts = {}

    for player in players:
        # Start a new postition at zero, then add ths player to its count.
        counts[player.position] = counts.get(player.position, 0) + 1

    return counts

def best_overall_by_position(
    players: tuple[Player, ...],
) -> dict[str, int]:
    # Store the highest overall rating encountered for each position.
    best_ratings = {}

    for player in players:
        # The first player establishes the rating; later players may raise it.
        if player.position not in best_ratings:
            best_ratings[player.position] = player.overall
        else:
            best_ratings[player.position] = max(
                best_ratings[player.position],
                player.overall,
            )

    return best_ratings

def average_overall_by_position(
    players: tuple[Player, ...],
) -> dict[str, float]:
    # Add together the overall ratings for each position.
    totals = {}

    for player in players:
        totals[player.position] = (
            totals.get(player.position, 0) + player.overall
        )

    # Reuse our counting function to calculate each group's average.
    counts = count_players_by_position(players)
    averages = {}

    for position in totals:
        averages[position] = totals[position] / counts[position]

    return averages