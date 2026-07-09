# Contributing

Thank you for considering a contribution.

## Project philosophy

Level Sense Pro Observer is a transparent observer. Contributions should
preserve this design:

-   Do not modify device payloads by default.
-   Do not replace the vendor cloud.
-   Do not remove cloud functionality.
-   Preserve unknown data when possible.
-   Prefer diagnostics over guessing.

## Code style

-   Keep files focused on one responsibility.
-   Add comments that explain why important choices were made.
-   Prefer typed dataclasses for protocol state.
-   Avoid adding unnecessary default entities.
-   Put advanced or noisy data behind options.

## Testing

Before opening a pull request, verify:

-   Home Assistant starts cleanly.
-   The Level Sense website still updates.
-   Default entities update.
-   Cloud result remains `success`.
-   Diagnostics download works.
-   Raw sensors can be enabled and disabled.

## Reporting issues

Include:

-   Home Assistant version.
-   Integration version.
-   Whether AdGuard, Pi-hole, or another DNS tool is used.
-   Relevant logs.
-   Diagnostics download when possible.

## Documentation

Please keep user-facing documentation synchronized with functional
changes. Good documentation is considered part of every contribution.
