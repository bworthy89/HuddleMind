import argparse
import sqlite3

from pathlib import Path
from bridge.load_dynasty import load_dynasty
from bridge.local_store import get_dynasty, save_observation


def main():
    # Collect the source files and the destination dynasty identity.
    parser = argparse.ArgumentParser(
        description="Capture a dynasty snapshot in HuddleMind's local history."
    )
    parser.add_argument("save", type=Path, help="Path to the dynasty save.")
    parser.add_argument("schema", type=Path, help="Path to the schema bundle.")
    parser.add_argument(
        "dynasty_id",
        help="Existing Huddlemind dynasty ID.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("local_data/huddlemind.sqlite3"),
        help="Path to HuddleMind's SQLite database.",
    )

    args = parser.parse_args()

    try:
        # Require an existing database before attempting a lookup.
        if not args.database.is_file():
            raise ValueError(
                f"Database not found: {args.database}"
            )

        # Check the dynasty identity before loading the game save.
        dynasty = get_dynasty(args.database, args.dynasty_id)
        if dynasty is None:
            raise ValueError(
                f"Dynasty not found: {args.dynasty_id}"
            )

        # Read the save, then preserve its complete normalized snapshot.
        details = load_dynasty(args.save, args.schema)
        observation_id = save_observation(
            args.database,
            args.dynasty_id,
            details,
        )
    except (OSError, ValueError, sqlite3.Error) as error:
        # Report expected file, parsing, and database failures clearly.
        parser.exit(
            status=1,
            message=f"Could not capture dynasty: {error}\n",
        )

    # The ID may identify a new observation or an existing duplicate.
    print("Dynasty:", dynasty[1])
    print("Observation ID:", observation_id)
    print("Team:", details.roster.team.name)


# Run the command only when this module is executed directly.
if __name__ == "__main__":
    main()