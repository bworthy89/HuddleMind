# Milestone 6 design preview

Public sample-only preview: https://huddlemind-api.worthymedia.tech/preview/

This standalone HTML prototype is for design review before building the Next.js
application. It has no API calls, credentials, account authentication, or live
save data. Names in the player/recruit samples are fictional. Summary counts
illustrate the design; the sample lists are intentionally smaller.

Navigation includes overview, roster search/filter/sort, player details,
schedule, recruiting details, dynasty selection, and simulated bridge status.
Phone layout uses bottom navigation; desktop uses a sidebar.

Deployment: Nginx serves `/var/www/huddlemind-preview/index.html` at `/preview/`.
The existing authenticated receiver routes remain proxied normally. The preview
sets no-store and noindex headers, but is public, not access controlled.

Validation: hosted page loaded over HTTPS; browser inspection verified phone
layout, roster navigation, QB filter, and player details. Owner phone design
review remains pending. This does not complete Milestone 6 functionality.
