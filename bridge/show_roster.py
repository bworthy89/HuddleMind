import argparse
from pathlib import Path

from bridge.load_snapshot import load_snapshot

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

    args = parser.parse_args()

    # Report expected file-access or validation failures as command-line errors.
    try:
        snapshot = load_snapshot(args.save, args.schema)
    except (OSError, ValueError) as error:
        parser.exit(
            status=1,
            message=f"Could not load dynasty: {error}\n",
        )

    print("Coach:", snapshot.coach.full_name)
    print("Team:", snapshot.team.name)
    print("Roster size:", len(snapshot.team.players))
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
        print(f"No players found for position {args.position}.")
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
