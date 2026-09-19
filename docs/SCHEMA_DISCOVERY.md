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

The public bundle can support continued investigation without requiring a full manual export immediately. Exact compatibility remains conditional until field decoding and sample validation succeed. No actual Team/Player records have yet been decoded at this checkpoint.
