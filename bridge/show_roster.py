import argparse
from pathlib import Path

from bridge.load_snapshot import load_snapshot
from bridge.snapshot_export import write_snapshot_json
from bridge.roster_summary import (
    average_overall_by_position,
    best_overall_by_position,
    count_players_by_position,
    summarize_rating_by_position,
    summarize_position_depth,
)
from bridge.player_ratings import RATING_FIELDS

def main() -> None:
    # Accept file paths from the command line instead of hardcoding them.
    parser = argparse.ArgumentParser(
        description="Read a dynasty save and display the controlled team's roster."
    )
    parser.add_argument("save", type=Path, help="Path to the dynasty save.")
    parser.add_argument("schema", type=Path, help="Path to the schema bundle.")

    parser.add_argument(
        "--position",
        type=str.upper,
        help="Show only this position, such as QB or WR.",
    )

    # Optionally save the complet snapshot to a new JSON file.
    parser.add_argument(
        "--export",
        type=Path,
        help="Write the full snapshot to a new JSON file.",
    )

    # Allow one summary mode at a time so neither option is silently ignored.
    summary_options = parser.add_mutually_exclusive_group()

    summary_options.add_argument(
        "--rating",
        choices=RATING_FIELDS,
        help="Show a rating summary, such as SpeedRating or StrengthRating.",
    )

    summary_options.add_argument(
        "--depth",
        action="store_true",
        help="Show position depth by overall rating, not game depth-chart order.",
    )

    args = parser.parse_args()

    # Report expected file-access or validation failures as command-line errors.
    try:
        snapshot = load_snapshot(args.save, args.schema)
    except (OSError, ValueError) as error:
        parser.exit(
            status=1,
            message=f"Could not load dynasty: {error}\n",
        )

    if args.export is not None:
        try:
            write_snapshot_json(snapshot, args.export)
        except OSError as error:
            parser.exit(
                status=1,
                message=f"Could not export snapshot: {error}\n",
            )
        print("Exported:", args.export)


    print("Coach:", snapshot.coach.full_name)
    print("Team:", snapshot.team.name)
    print("Roster size:", len(snapshot.team.players))

    # Summarize the complete roster using overall-rating order.
    if args.depth:
        summary = summarize_position_depth(snapshot.team.players)

        print()
        print("Ordered by overall rating, not the game's depth chart.")
        print(
            f"{'Position':<10} {'Players':>7} "
            f"{'Top OVR':>8} {'Next OVR':>9} {'Gap':>5}"
        )
        print("-" * 43)

        for position, details in summary.items():
            # A missing second player has no rating gap to calculate.
            next_overall = details["next_overall"]
            gap = details["gap"]

            next_text = (
                "N/A" if next_overall is None else str(next_overall)
            )
            gap_text = "N/A" if gap is None else str(gap)

            print(
                f"{position:<10} {details['roster_count']:>7} "
                f"{details['top_overall']:>8} "
                f"{next_text:>9} {gap_text:>5}"
            )

        # Finish after displaying the requested depth summary.
        return

    # Show the requested attribute summary using the complete roster.
    if args.rating is not None:
        summary = summarize_rating_by_position(
            snapshot.team.players,
            args.rating,
        )

        print()
        print("Rating:", args.rating)
        print(f"{'Position':<10} {'Rated/Total':>12} {'Average':>12}")
        print("-" * 36)

        for position, details in summary.items():
            # Report how many players contributed to the average.
            coverage = (
                f"{details['rated_players']}/{details['roster_count']}"
            )

            # Missing values stay distinct from a real average of zero.
            average = details["average"]
            average_text = (
                "Unavailable" if average is None else f"{average:.1f}"
            )

            print(
                f"{position:<10} {coverage:>12} {average_text:>12}"
            )

        # Finish after the requested rating summary.
        return

    # Calculate summaries from the full roster, independent of display filtering.
    position_counts = count_players_by_position(snapshot.team.players)
    best_ratings = best_overall_by_position(snapshot.team.players)
    average_ratings = average_overall_by_position(snapshot.team.players)

    print()
    print(
        f"{'Position':<10} "
        f"{'Players':>7} "
        f"{'Best OVR':>9} "
        f"{'Avg OVR':>9}"
    )
    print("-" * 38)

    # Display the calculated average to one decimal place.
    for position in sorted(position_counts):
        print(
            f"{position:<10} "
            f"{position_counts[position]:>7} "
            f"{best_ratings[position]:>9} "
            f"{average_ratings[position]:>9.1f}"
        )

    print()

    # Keep the full roster unless the user requests a particular position.
    players_to_show = snapshot.team.players

    if args.position:
        players_to_show = tuple(
            player
            for player in players_to_show
            if player.position == args.position
        )

    # Explain an empty result and stop before printing the table headings.
    if not players_to_show:
        if args.position:
            print(f"No players found for position {args.position}.")
        else:
            print("The team roster is empty.")
        return

    # Sort a display copy by position, descending overall, then player name.
    sorted_players = sorted(
        players_to_show,
        key=lambda player: (
            player.position,
            -player.overall,
            player.full_name,
        ),
    )


    print(f"{'Player':<28} {'Pos':<6} {'OVR':>3}")
    print("-" * 39)



    # Align names and positions left, and overall ratings right.
    for player in sorted_players:
        print(
            f"{player.full_name:<28} "
            f"{player.position:<6} "
            f"{player.overall:>3}"
        )

# Run the command only when this module is executed, not when it is imported.
if __name__ == "__main__":
    main()
