# CFB27 schema discovery

## Scope and ownership

The owner asked Codex to conduct schema/save-format discovery autonomously and resume the learning-first workflow for actual application implementation afterward. Discovery remains read-only. Downloaded schema assets and local game data stay outside this repository.

## Public bundle compatibility check — 2026-09-19

Source: [CFB27_833_0.gz](https://github.com/KevinMilesCode/CFB27-Real-Coach-Importer/blob/main/schema/CFB27_833_0.gz). Downloaded as data only; no third-party application was run.

- Local file: `E:\aibridgemod\schema-discovery\CFB27_833_0.gz`
- SHA-256: `38501a49eedaa4762163fc47b758d40fa267a1bce1fd0d7aa66cf5ab8ab8fd91`
- JSON metadata: major 486, minor 1, gameYear 27. Bundle metadata and save header numbering differ.
- The bundle contains both Team (424 members) and Player (288 members).
- OverallPercentage, Spline, and Spline_CalculateY match the local revision-4 exports in declared member count and ordered field index/name/type tuples. This comparison does not establish equality of every metadata attribute or resolved inheritance behavior.
- All 71 PositionE name/index/value tuples match the local export.
- In particular, the bundle's Spline entry does not directly retain the exported CalculateY `final` attribute; schema resolution/skip behavior must be checked before implementing a general decoder.

The inspected save is `DYNASTY-TULANENEW-AUTOSAVE`, read from OneDrive Documents in one read for this check. Size: 9,646,981 bytes. SHA-256: `24f1af6d72e7bddc369a95849ec96373d95902dbe9c439fe916c144ae7d7a9ef`. Its first candidate chunk completed zlib decompression within a 64 MiB output limit, with no trailing/unprocessed compressed data and an FrTk signature. Inner version: 833.1.

## Matching table-header candidates

Offsets refer to the decompressed database. These candidates have SPBF/BSFT markers and match the bundle's member count; this is structural evidence, not proof that every field decodes correctly or every declared slot is occupied.

| Name | Table ID | Start | Declared count/capacity | Words per record | Members |
|---|---:|---:|---:|---:|---:|
| Player | 4255 | 12649810 | 17500 | 48 | 288 |
| Team | 5308 | 22068727 | 1 | 197 | 424 |
| Team | 5310 | 22072206 | 1 | 197 | 424 |
| Team | 5311 | 22075425 | 1 | 197 | 424 |
| Team | 5312 | 22078644 | 1 | 197 | 424 |
| Team | 5313 | 22081863 | 1 | 197 | 424 |
| Team | 6057 | 26569079 | 1 | 197 | 424 |
| Team | 6058 | 26572298 | 1 | 197 | 424 |
| Team | 6059 | 26575517 | 6 | 197 | 424 |
| Team | 6351 | 28432538 | 143 | 197 | 424 |

OverallPercentage ID 4097 and Spline IDs 5176/5177 also match their bundle field counts. Multiple instances of the same schema exist: never choose the first Team or Spline match solely by name.

## Next discovery work

1. Resolve schema inheritance/final members and descriptor layouts before interpreting packed fields.
2. Identify the main team table through identity values and references. ID 6351 is a candidate based on capacity, not yet a verified selection.
3. Decode team identity/roster references and player identity, position, TeamIndex, and rating samples; inspect string-storage rules and occupancy.
4. Establish team/player joins and how the user-controlled program is identified; validate samples against available game evidence.
5. Produce a discovery handoff and concrete HuddleMind model/adapter plan, clearly separating verified fields from unresolved interpretations.

The public bundle can support continued investigation without requiring a full manual export immediately. Exact compatibility remains conditional until field decoding and sample validation succeed.

## Team-to-player roster discovery — 2026-09-19

`bridge/discover_rosters.py` is a separate, read-only research probe. It reads one save snapshot, bounds the decompressed chunk to 64 MiB, requires a complete zlib stream, scans candidate SPBF/ASTO tables, and rejects ambiguous player targets. Schema attributes are consumed in their serialized array order, which differs from numeric attribute-index order for Player. Only isolated, aligned 32-bit fields are decoded; this does not implement packed fields or general inheritance resolution.

String words are offsets into the table's secondary byte section. Names are bounded by the schema maximum length and that section, then decoded as UTF-8. This interpretation was checked against the reference [string reader](https://github.com/bep713/madden-franchise/blob/master/src/strategies/common/table2Field/FranchiseTable2FieldStrategy.js) and actual save data.

Results on the same save hash recorded above:

- Team table 6351 contains 143 candidate team rows with readable identity fields and resolvable Player[] roster references.
- Following those references yields 12,154 distinct, non-null Player references, all targeting table 4255. Every referenced player has non-empty first and last names. Rosters contain 84 or 85 such references.
- Tulane is Team row 118 and references Player[] table 6137, row 120. Its roster has 85 non-null references. Source and target row numbers must not be assumed equal.
- Tulane samples: Zycarl Lewis Jr. (Player row 6349), Bredell Richardson (8980), Justin Agu (84).
- Four synthetic tests pass for integer/header bounds, invalid string pointers/rows, and rejection of packed fields.
- Full local report: ignored `local_data/roster-discovery.json`; no save/schema assets are added to Git.

These results establish a usable candidate team-to-roster-to-player identity path. They do not yet establish free-list occupancy, user-controlled team selection, packed position/rating/TeamIndex fields, or comparison against the in-game roster. Table 6351 now has identity/reference evidence beyond its capacity, but automatic selection across other saves remains unimplemented. The earlier final/inherited-member discrepancy is still open for general decoding.

## PocketScout archive comparison — 2026-09-19

Owner-provided [PocketScout Utilities 0.9.14 archive](https://drive.google.com/file/d/1ImmlBvez46FFPoqAH_jtwVvn68bTmhb5/view) downloaded to `E:\aibridgemod\schema-discovery\pocketscout-download` (100,022,914 bytes). Only packaged app resources were extracted into `schema-discovery/pocketscout-static`; no application code was executed. Release metadata identifies PocketScout and Yoyopaulsen and build time 2026-09-08T14:13:08.302Z. The package includes readable JavaScript and madden-franchise version 4.3.1.

- Bundled schema: `resources/app/node_modules/madden-franchise/data/schemas/27/C27_486_6.gz`.
- SHA-256: `dc0d37834a95cbad6edd39d9adbd5572c04ddb6f3f795bf87c00b4fe883aa8d5`.
- Metadata: major 486, minor 6, gameYear 27. This is different from the GitHub bundle's 486.1 metadata, not proof of better compatibility with save 833.1.
- Comparing `schemas` entries by name: 3,503 versus 3,526 in the GitHub bundle; no newly named definitions, 23 absent, and 99 shared definitions differ.
- Team remains 424 attributes, Player 288, Coach 138. User, UserEntity, PositionE, Spline, and OverallPercentage definitions compare equal.
- Player's StartingHotCold, nine Team contract-goal status fields, and Coach's LeagueJobMotivation lack embedded enum metadata present in the GitHub bundle. A higher minor label is therefore not sufficient reason to replace the existing source.
- Running our own read-only roster probe with this schema on the same save hash produces exactly the same team/roster/player-name report.
- Packaged `src/modules/userRecruitingHours.js` checks `record.IsUserControlled` with `!record.isEmpty` when selecting coach records. This is a discovery lead, not yet validated against our save.

Keep both bundles for comparison; retain the existing GitHub schema for now. Neither PocketScout nor its bundled JavaScript was launched, and extracted third-party assets remain outside the repository.
