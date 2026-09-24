# HuddleMind Web App

The web app will be HuddleMind's primary user interface and should work well from a phone, tablet, laptop, or second PC.

## Planned Responsibilities

- Authentication
- Dynasty selection
- Program dashboard
- AI staff report
- Recruiting analysis
- Roster / depth analysis
- Schedule / results
- Opponent scouting
- Live game dashboard
- Live play-call recommendations
- Recommendation history
- Settings and bridge status

## Planned Starting Stack

- Next.js
- TypeScript
- Tailwind CSS
- Responsive/mobile-first design
- PWA support later

## Current implementation

The private Next.js application runs at `/app` with Overview, Roster, Schedule,
and Recruiting tabs, responsive CSS, and a persistent mobile bottom navigation.
All data comes from the authenticated receiver's latest snapshot. Schedule and
Recruiting provide filters and saved results/target details; all views are read-only.

Run `npm test`, `npm run build`, and `node tests/http-smoke.mjs` from this folder.

See `deploy/WEB.md` for authentication, deployment, and verification details.
