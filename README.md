# Scorebot v4.0 is a proof of concept version.

Scorebot v4 is a proof of concept version ment to test the new scoring system. It is NOT stable
and recommended only in use where crashes are ok to have.

This will be getting replaced by UDP, but is currently here for code review.

Please use the v3.3 branch if you require a stable working version of scorebot-core.

Thanks

# Scorebot Core

Sorebot is a scoring engine for CTF competitions.
It is built upon a Blue Team / Red Team model, where Blue Teams defend flags against Red teams. (Blue Teams may also attack other Blue Teams to steal flags).
Scoring is based upon flags stolen, scored service up time, and injects submitted (there is no scoring tracking for injects yet).

This is a fork of "https://github.com/dichotomy/scorebot" for Scorebot vrsion 3 and greater.
From version 3 - ownwards, the components of Scorebot are broken up into seperate "modules".

- Scorebot-Core  (this)
- Scorebot-HealthAndWelfare https://github.com/dichotomy/scorebot/tree/version3.0/Monitors
- Scorebot-TicketServer https://github.com/dichotomy/scorebot/tree/version3.0/TicketManager
- Scorebot-BeaconServer https://github.com/dichotomy/scorebot/tree/version3.0/CLI_BEACON_SERVER
- Socrebot-Flag/CLIServer https://github.com/dichotomy/scorebot/tree/version3.0/CLI_BEACON_SERVER

These are the primary components of Scorebot, collectivly called the Scorebot Engine, SBE for short.

I am using this repository to help seperate out and manage the official Scorebot Core code as we develop and add new features.
