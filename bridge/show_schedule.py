import argparse
from pathlib import Path

from bridge.load_schedule import load_schedule
from bridge.schedule_summary import summarize_results

def main() -> None:
    # Accept the save and schema paths from the command line.
    parser = argparse.ArgumentParser(
        description="Display the controlled team's dynasty schedule."
    )
    parser.add_argument("save", type=Path, help="Path to the dynasty save.")
    parser.add_argument("schema", type=Path, help="Path to the schema bundle.")
    args = parser.parse_args()

    # Report expected loading failures without a full traceback.
    try:
        games = load_schedule(args.save, args.schema)
    except (OSError, ValueError) as error:
        parser.exit(
            status=1,
            message=f"Could not load schedule: {error}\n",
        )

    print("Scheduled games:", len(games))

    # Summarize the controlled team's results across the loaded fixtures.
    summary = summarize_results(games)
    completed = summary["wins"] + summary["losses"] + summary["ties"]

    print("Completed:", completed)
    print(
        f"Record (W-L-T): "
        f"{summary['wins']}-{summary['losses']}-{summary['ties']}"
    )
    print("Pending:", summary["pending"])
    print("Unknown status:", summary["unknown"])
    print()

    # Handle an empty schedule before attempting to display game records.
    if not games:
        print("No scheduled games found.")
        return

    for game in games:
        matchup = f"{game.away_team} at {game.home_team}"

        # Zero is a valid score, so check explicitly for None.
        if game.home_score is not None and game.away_score is not None:
            print(
                f"Week {game.week}: {matchup}"
                f" | {game.away_score} - {game.home_score}"
                f" | {game.status}"
            )
        else:
            print(f"Week {game.week}: {matchup} | {game.status}")

# Run the command only when this module is executed directly.
if __name__ == "__main__":
    main()
