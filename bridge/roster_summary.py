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

def get_player_rating(player: Player, field_name: str) -> int | None:
    # Find the saved attribute by its exact schema field name.
    for rating in player.ratings:
        if rating.field == field_name:
            return rating.value

    # Older snapshots for unsupported fields may not contain this rating.
    return None

def average_rating_by_position(
    players: tuple[Player, ...],
    field_name: str,
) -> dict[str, float]:
    # Track rating totals and the number of available values per position.
    totals = {}
    counts = {}

    for player in players:
        rating = get_player_rating(player, field_name)

        # Missing ratings must not count as zero or lower the average.
        if rating is None:
            continue

        totals[player.position] = totals.get(player.position, 0) + rating
        counts[player.position] = counts.get(player.position, 0) + 1

    # Only positions with at least one avaiable rating appear in the result.
    averages = {}
    for position in totals:
        averages[position] = totals[position] / counts[position]

    return averages

def count_available_ratings_by_position(
    players: tuple[Player, ...],
    field_name: str,
) -> dict[str, int]:
    # Include every roster position, even when no ratings are available.
    counts = {}

    for player in players:
        counts.setdefault(player.position, 0)

        # A saved zero is available; only None means unavailable.
        if get_player_rating(player, field_name) is not None:
            counts[player.position] += 1

    return counts

def summarize_rating_by_position(
    players: tuple[Player, ...],
    field_name: str,
) -> dict[str, dict[str, int | float | None]]:
    # Reuse our helpers to keep counting and averaging rules consistent.
    roster_counts = count_players_by_position(players)
    available_counts = count_available_ratings_by_position(players, field_name)
    averages = average_rating_by_position(players, field_name)

    summaries = {}
    for position in sorted(roster_counts):
        summaries[position] = {
            "roster_count": roster_counts[position],
            "rated_players": available_counts[position],
            "average": averages.get(position),
        }
    
    
    return summaries

def rank_players_by_position(
    players: tuple[Player, ...],
) -> dict[str, tuple[Player, ...]]:
    # Collect players who share the same roster position.
    groups = {}

    for player in players:
        groups.setdefault(player.position, []).append(player)

    ranked_groups = {}
    for position in sorted(groups):
        # Use name and record identity to keep tied ratings in a stable order.
        ranked_groups[position] = tuple(
            sorted(
                groups[position],
                key=lambda player: (
                    -player.overall,
                    player.full_name.casefold(),
                    player.record_id.table_id,
                    player.record_id.row_id,
                ),
            )
        )

    return ranked_groups

def summarize_position_depth(
    players: tuple[Player, ...],
) -> dict[str, dict[str, int | None]]:
    # Reuse our ranking helper to put each position's highest ratings first.
    ranked_groups = rank_players_by_position(players)

    summaries = {}
    for position, position_players in ranked_groups.items():
        top_overall = position_players[0].overall

        # A second rating and gap are unavailable for a one-player group.
        next_overall = None
        gap = None

        if len(position_players) >= 2:
            next_overall = position_players[1].overall
            gap = top_overall - next_overall

        summaries[position] = {
            "roster_count": len(position_players),
            "top_overall": top_overall,
            "next_overall": next_overall,
            "gap": gap,
        }

    return summaries