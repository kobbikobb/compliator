"""What an ISMS needs, in the order it should exist.

Data only, no behaviour: the document sequence the README describes, the
recommended starting set of policies, and the frameworks an instance can
declare. ``compliator init`` reads this to know what to offer and in what order.

Two things to keep in mind when editing this file:

- **The policy sequence and summaries are the ones documented in**
  ``isms/policies/README.md``. If the two disagree, that file is the argument
  and this table is the bug.
- **No framework mapping lives here.** An entry says whether a framework
  requires a statement of applicability and which file records it - not which
  of our controls satisfy which of its requirements. That decision is the SoA's
  job, per ``isms/frameworks.md``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Policy:
    """One entry of the recommended policy sequence."""

    number: int
    slug: str
    title: str
    summary: str
    checkable: str  # "yes" | "partly" | "no" - whether it can be checked by a control

    @property
    def id(self) -> str:
        return f"POL-{self.number:03d}"

    @property
    def filename(self) -> str:
        return f"{self.id}-{self.slug}.md"

    @property
    def path(self) -> str:
        return f"isms/policies/{self.filename}"


# Order matters: it is the sequence to write them in, not importance. The gap
# between 2 and 3 is the risk work that produces the SoA (README, "Order to
# populate").
POLICIES: tuple[Policy, ...] = (
    Policy(1, "information-security", "Information Security Policy", "the commitment: what we protect, who owns it, that we review it", "partly"),
    Policy(2, "risk-management", "Risk Management Policy", "how we identify, assess, treat, and accept risk", "no"),
    Policy(3, "access-control", "Access Control Policy", "identities, MFA, least privilege, joiners/movers/leavers", "yes"),
    Policy(4, "change-management", "Change Management Policy", "reviewed changes, tests, separation of environments", "yes"),
    Policy(5, "acceptable-use", "Acceptable Use Policy", "what people may do with company systems and data", "partly"),
    Policy(6, "logging-monitoring", "Logging and Monitoring Policy", "what is logged, retention, who reviews it", "yes"),
    Policy(7, "incident-response", "Incident Response Policy", "how incidents are reported, triaged, resolved, learned from", "partly"),
    Policy(8, "backup-continuity", "Backup and Continuity Policy", "backups, restore testing, what happens when things break", "yes"),
    Policy(9, "supplier-management", "Supplier Management Policy", "assessing and reviewing vendors and processors", "partly"),
    Policy(10, "data-protection", "Data Protection Policy", "data classification, encryption, retention, deletion", "yes"),
    Policy(11, "hr-security", "HR Security Policy", "onboarding, offboarding, screening, training", "partly"),
    Policy(12, "physical-security", "Physical Security Policy", "only if there is somewhere physical to protect", "no"),
)

# The set isms/policies/README.md calls out for a small organisation: 1, 2, the
# risk work, then 3, 4, 6, 7, 8 and a short version of 10. 5, 9, 11 and 12 are
# deliberately absent - "fewer, true policies beat a full set nobody follows".
SUGGESTED_START: tuple[int, ...] = (1, 2, 3, 4, 6, 7, 8, 10)


@dataclass(frozen=True)
class Framework:
    """An external framework an instance can orient to."""

    key: str
    title: str
    requires_soa: bool
    soa_filename: str | None
    note: str

    @property
    def soa_path(self) -> str | None:
        return f"isms/{self.soa_filename}" if self.soa_filename else None


FRAMEWORKS: tuple[Framework, ...] = (
    Framework(
        key="iso_27001_2022",
        title="ISO/IEC 27001:2022",
        requires_soa=True,
        soa_filename="soa.iso_27001_2022.md",
        note="requires a statement of applicability; the filename pins the revision",
    ),
    Framework(
        key="soc2",
        title="SOC 2 Trust Services Criteria",
        requires_soa=False,
        soa_filename=None,
        note="no statement of applicability: you choose criteria and describe the system",
    ),
)

# What a person is likely to type, mapped to a registry key. ", " and " and "
# separated lists are split before lookup, so "iso, soc2" and "both" both work.
ALIASES: dict[str, tuple[str, ...]] = {
    "iso": ("iso_27001_2022",),
    "iso27001": ("iso_27001_2022",),
    "iso_27001": ("iso_27001_2022",),
    "iso_27001_2022": ("iso_27001_2022",),
    "27001": ("iso_27001_2022",),
    "soc2": ("soc2",),
    "soc_2": ("soc2",),
    "both": ("iso_27001_2022", "soc2"),
    "all": ("iso_27001_2022", "soc2"),
    "none": (),
}

# Documents that are not policies, in creation order. Paths are relative to the
# instance root; the SoA is added only when a declared framework requires one.
SCOPE_PATH = "isms/scope.md"
FRAMEWORKS_PATH = "isms/frameworks.md"
RISK_PATH = "isms/risks/RISK-001-lost-access.md"
