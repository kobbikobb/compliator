"""Error types.

Design rule: every failure path in this system raises one of these and is
surfaced loudly by the runner. There is deliberately no code path that
swallows a collection failure and emits empty or placeholder evidence.
"""

from __future__ import annotations


class CompliatorError(Exception):
    """Base class for all expected POC failures."""


class ConfigError(CompliatorError):
    """Bad or inconsistent configuration (caught before any collection runs)."""


class PluginError(CompliatorError):
    """A source could not be reached or returned an unexpected shape.

    Raised when: fixture file missing/unreadable, source returned non-mapping
    data, required top-level keys absent, or a failure was requested via
    --simulate-failure (for demonstrating the fail-loud path).
    """


class EmptyPopulationError(CompliatorError):
    """A check's population resolved to zero items.

    Zero-item populations are treated as an error, never as a vacuous pass:
    an auditor's first question about any sampled population is whether it is
    complete, and silently passing on nothing is the worst possible answer.
    """


class VerificationError(CompliatorError):
    """Evidence record failed hash/integrity verification."""


class OnboardingError(CompliatorError):
    """The scaffolding run could not proceed as asked.

    Raised when: the answers file is missing, unreadable or has an unknown key,
    a framework or policy selection is not recognised, or an interactive run was
    requested with no terminal and no answers. It is never raised for a choice
    the user is entitled to make - declining every document is an answer, not a
    failure.
    """
