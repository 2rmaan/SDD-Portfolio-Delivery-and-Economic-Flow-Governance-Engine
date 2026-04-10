# Feature Specification: Portfolio Delivery & Economic Flow Governance Engine

**Feature Branch**: `001-portfolio-delivery-engine`
**Created**: 2026-04-09
**Status**: Draft
**Input**: User description: "Portfolio Delivery & Economic Flow Governance Engine — Enterprise-Scale Oversight for Multi-Workstream Software Delivery"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Flow Efficiency Monitoring (Priority: P1)

A portfolio manager opens the dashboard and immediately sees flow efficiency for every
workstream. Any workstream below the 45% active-work threshold is flagged visually.
She drills into "Cloud Infrastructure," confirms the bottleneck is in external approval
gates, and exports the data to share with the DevOps lead.

**Why this priority**: Flow efficiency is the earliest leading indicator of systemic waste.
Without it, CoD and cycle-time metrics have no causal anchor. This story delivers the
core diagnostic value of the engine and constitutes a standalone MVP.

**Independent Test**: Load the dashboard with a dataset containing at least two workstreams
— one above and one below the 45% threshold. Verify that the below-threshold workstream is
flagged, the percentages are correctly calculated, and the data can be exported.

**Acceptance Scenarios**:

1. **Given** delivery data for 3 workstreams is loaded, **When** the portfolio manager opens
   the Flow Efficiency view, **Then** each workstream displays its efficiency percentage
   (active work time ÷ total lead time × 100) and workstreams below 45% are visually
   distinguished from compliant ones.
2. **Given** a workstream's efficiency drops below 45%, **When** the dashboard refreshes,
   **Then** the system highlights the workstream as requiring attention without manual
   intervention.
3. **Given** a workstream is displayed, **When** the manager requests a data export,
   **Then** the system produces a structured file containing workstream name, efficiency
   percentage, and contributing team data.

---

### User Story 2 - Cost of Delay by Team (Priority: P2)

An executive opens the CoD view and sees which teams are accumulating the most financial
waste from tickets sitting in "Started" or "Waiting" states. Gamma Team's disproportionate
CoD triggers an action. The executive can sort teams by total CoD and drill into individual
tickets contributing to the leak.

**Why this priority**: CoD converts abstract delay into dollar values, enabling capital
reallocation decisions. It requires flow data (US1) as its input, making it a natural P2.

**Independent Test**: Provide a dataset with at least three teams, each having tickets in
various wait states and distinct resource daily rates. Verify that CoD = Wait Time ×
Resource Daily Rate is computed per ticket, aggregated per team, and the highest-CoD team
is ranked first.

**Acceptance Scenarios**:

1. **Given** tickets exist across multiple teams with recorded wait times and known daily
   rates, **When** the CoD view is opened, **Then** each team displays its total accumulated
   Cost of Delay in currency, calculated as the sum of (Wait Time × Resource Daily Rate)
   for all its tickets.
2. **Given** the CoD view is loaded, **When** the executive sorts by CoD descending,
   **Then** teams are reordered with the highest financial waste at the top.
3. **Given** a team is selected, **When** the executive drills in, **Then** individual
   tickets are listed with their wait time, daily rate, and per-ticket CoD contribution.

---

### User Story 3 - Cycle Time Distribution & Predictability (Priority: P3)

A delivery manager reviews cycle time distribution for each priority tier. She sees that
"Medium" priority items have high variance and uses this insight to tighten the Definition
of Ready, reducing future variance and improving roadmap reliability.

**Why this priority**: Cycle-time analysis is a coaching and process improvement tool.
It is valuable but does not block prioritization (US1/US2) decisions, making it P3.

**Independent Test**: Load a dataset with at least 20 completed tickets across three
priority levels. Verify that cycle time statistics (median, spread) are displayed per
priority tier and that high-variance tiers are distinguishable from stable ones.

**Acceptance Scenarios**:

1. **Given** completed tickets exist with recorded start and end dates across priority
   levels (P0, P1, P2, Medium, etc.), **When** the Cycle Time view is opened, **Then**
   each priority tier displays a distribution of cycle times showing median and spread.
2. **Given** a priority tier has a wide spread of cycle times, **When** the delivery
   manager views it, **Then** the tier is visually differentiated from tiers with tight,
   predictable distributions.
3. **Given** the distribution view is open, **When** the manager filters by team,
   **Then** the distribution updates to reflect only that team's tickets.

---

### User Story 4 - Value vs. Lead Time ROI Analysis (Priority: P4)

A product owner opens the ROI Scatter view and immediately sees that the highest-value
features are clustered at the far right of the lead time axis — a strategic failure.
She uses this evidence to justify introducing an Expedite Lane for high-value items
in the next planning cycle.

**Why this priority**: ROI scatter is a strategic planning aid, not a daily operational
view. It synthesizes all prior metrics, making it the natural capstone story at P4.

**Independent Test**: Load a dataset with features having both business value scores and
lead time records. Verify that the scatter chart plots each feature at the correct
(lead-time, value) coordinate and that clusters of high-value/high-lead-time items are
visually identifiable.

**Acceptance Scenarios**:

1. **Given** features exist with assigned business value scores and recorded lead times,
   **When** the ROI Scatter view is opened, **Then** each feature is plotted with lead
   time on the x-axis and business value on the y-axis.
2. **Given** the scatter is displayed, **When** the product owner filters by priority
   tier, **Then** only features matching the selected tier are shown.
3. **Given** the scatter is displayed, **When** the product owner hovers over a data
   point, **Then** the feature name, value score, and lead time are shown.

---

### Edge Cases

- What happens when a ticket has no recorded wait time (never entered a waiting state)?
- How does the system handle teams with no completed tickets in the selected time period?
- What happens when a feature has no assigned business value score in the ROI scatter?
- How are tickets that span multiple workstreams attributed for CoD calculation?
- What happens if resource daily rates are missing for a team?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate Flow Efficiency per workstream as the ratio of active
  work time to total lead time, expressed as a percentage.
- **FR-002**: System MUST flag workstreams whose Flow Efficiency falls below a configurable
  threshold (default: 45%).
- **FR-003**: System MUST calculate Cost of Delay per ticket as Wait Time multiplied by
  the assigned Resource Daily Rate, and aggregate this by team.
- **FR-004**: System MUST display teams ranked by total Cost of Delay, with drill-down to
  individual ticket contributions.
- **FR-005**: System MUST display cycle time distribution per priority tier, showing
  median and spread for completed tickets.
- **FR-006**: System MUST display a Value vs. Lead Time scatter chart, with each feature
  plotted by its business value score and total lead time.
- **FR-007**: System MUST support portfolios spanning multiple workstreams and teams,
  with consistent aggregation across all four metric views.
- **FR-008**: System MUST allow filtering of all views by time period, workstream, team,
  and priority tier.
- **FR-009**: System MUST support data export of any view in a structured format.
- **FR-010**: System MUST accept delivery data input including ticket states, timestamps,
  team assignments, priorities, business value scores, and resource daily rates.

### Key Entities

- **WorkItem**: Represents a ticket or feature. Key attributes: identifier, priority,
  business value score, current state, state history with timestamps (created, started,
  waiting, active, completed).
- **Team**: A delivery team within a workstream. Attributes: name, workstream, resource
  daily rate.
- **Workstream**: A logical grouping of teams (e.g., Cloud Infrastructure, Gamma Team).
  Attributes: name, member teams.
- **Portfolio**: The top-level container. Aggregates all workstreams for cross-cutting
  metric calculation.
- **DeliveryMetrics**: Computed artifact per entity. Includes flow efficiency, cost of
  delay, cycle time, and lead time derived from WorkItem state histories.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Portfolio managers can identify the workstream with the highest financial
  waste within 2 minutes of loading the dashboard, without prior training.
- **SC-002**: Cost of Delay figures are accurate to within 1% of manual calculation
  for any given team and time period.
- **SC-003**: The dashboard remains responsive for portfolios with at least 10 workstreams,
  50 teams, and 10,000 work items.
- **SC-004**: 90% of first-time users correctly identify the highest-CoD team within
  5 minutes using only the dashboard.
- **SC-005**: Delivery managers can produce a shareable cycle time report within
  3 minutes without assistance.

## Assumptions

- Teams have stable, known resource daily rates that can be associated with work items
  at calculation time; retroactive rate changes are out of scope for v1.
- Work item state histories (timestamps per state transition) are available as structured
  input; real-time integration with external tracking tools (e.g., Jira, Linear) is out
  of scope for v1.
- Business value scores for features are pre-assigned by product owners and provided
  as part of the input data; the engine does not score features itself.
- A "wait state" is any state where the ticket is neither actively being worked on nor
  completed (e.g., "Waiting for Review," "Blocked," "In Queue").
- The flow efficiency threshold of 45% is the default; operators can configure it
  per workstream.
