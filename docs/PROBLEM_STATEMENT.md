# Problem Statement

**Title:** Context-Aware, Profile-Based Route Finding in Dhaka City: A Comparative Study of Search Algorithms

## 1. Background

In Dhaka, the shortest route by distance is often neither the fastest nor the safest. Average speed on main roads has fallen to about 4.8 km/h at peak (down from about 25 km/h in the late 1990s). Rain floods more than a hundred known hotspots and can make roads impassable. Processions block major intersections such as Shahbagh, Paltan and Farmgate with little warning. Some areas carry mugging and accident risk that rises sharply at night.

Different travelers also weigh these factors differently. An ambulance cares mostly about time. Someone going to an important meeting cares about a *predictable* arrival time. A person traveling alone at night cares most about safety.

## 2. Problem

Given a road network of Dhaka, a source, a destination, a departure time and day, the current city conditions (rainfall, active blockades, road works), and a traveler profile, find the route with the lowest **generalized cost**. Generalized cost is expected travel time plus penalties for unreliability and safety risk, all expressed in minute-equivalents and weighted by the traveler profile.

Then answer the main question of the study: **How do classical uninformed and informed search algorithms compare on this problem in solution quality and computational effort, and how does that comparison change as conditions change?**

## 3. Inputs and output

| Input | Description |
| --- | --- |
| Road graph G = (V, E) | Directed drive network of Dhaka from OpenStreetMap (tens of thousands of intersections); one-way streets preserved |
| Source s, goal g | Two nodes in V (chosen by clicking the map; snapped to the nearest node) |
| Departure context | Time of day, day of week, month |
| Conditions | Rainfall (mm) and hours since rain stopped; set of blocked intersections; set of road-work edges |
| Traveler profile | One of: ambulance, urgent meeting, solo night traveler, general commuter, bus/truck |

**Output:** a path from s to g, its generalized cost, its distance, and a per-edge breakdown of the cost factors. If no passable path exists, the output says so.

## 4. Search problem formulation

The baseline (MVP) uses a **static snapshot**: every edge cost is evaluated once, at the departure time.

- **State:** the current intersection v ∈ V
- **Initial state:** s
- **Actions:** move along any outgoing edge (v, w) whose cost is finite
- **Transition model:** Result(v, (v, w)) = w
- **Goal test:** v = g
- **Path cost:** sum of edge costs c(u, v) over the path

**Extension (time-dependent):** the state becomes (v, t), and traversing an edge advances the clock by its travel time, so each edge is costed at the time the traveler actually reaches it. This matters for long trips that cross a traffic band boundary, for example leaving at 15:30 and hitting the 16:00 peak.

## 5. Edge cost model

For edge (u, v), context x and profile p with parameters β (reliability weight) and λ (risk weight):

```latex
\begin{aligned}
c(u,v) &= T(u,v) \times \big(1 + \beta \, U(u,v)\big) + \lambda \times R(u,v) \times \frac{L(u,v)}{L_{ref}} \\
T(u,v) &= \frac{L(u,v)}{v_{free}(u,v)} \times F_{traffic} \times F_{rain} \times F_{work}
\end{aligned}
```

| Term | Meaning | Range |
| --- | --- | --- |
| L, v_free | Edge length and free-flow speed by road type | L > 0 |
| F_traffic | Congestion by time band, day type and road class (and spillover near a blockade) | ≥ 1 |
| F_rain | Flood-hotspot slowdown by rainfall band; ∞ above the closure threshold | ≥ 1 or ∞ |
| F_work | Road-work slowdown, and the terminal-zone penalty for buses and trucks | ≥ 1 |
| U | Uncertainty: 1 near blockade-prone intersections, 0.5 at flood hotspots in monsoon, else 0 | [0, 1] |
| R | R_crime + R_accident for hotspot edges, by time band (day, night, pre-dawn) | ≥ 0 |
| L_ref | Reference length that turns risk into a per-distance exposure | constant |

An edge is **impassable** (c = ∞) if either of its endpoints is blocked, or its rainfall band is above the closure threshold for that profile. All constants live in a configuration file. They are first estimates from news and research sources and will be calibrated against Google Maps travel times.

**Why the bounds matter:** because every F ≥ 1 and U, R ≥ 0, every edge satisfies c(u, v) ≥ L(u, v) / v_max, where v_max is the fastest free-flow speed anywhere in the graph. That bound is what makes the A\* heuristic below admissible and consistent.

## 6. Traveler profiles

| Profile | Priority | λ | β | Special rule |
| --- | --- | --- | --- | --- |
| Ambulance | Time | 0.5 | 0.5 | Halves moderate congestion (floor 1) but not gridlock (F_traffic ≥ 4); avoids flood edges with F_rain ≥ 3; extra ×1.5 on road works |
| Urgent meeting | Time + reliability | 1.0 | 1.0 | Strong penalty on uncertain edges |
| Solo night traveler | Safety | 5.0 | 0.3 | Strong penalty on risk hotspots |
| General commuter | Time | 1.0 | 0.3 | None |
| Bus / truck | Time | 1.0 | 0.3 | ×1.5 in terminal zones (extortion delays) |

## 7. Algorithms

All algorithms are implemented from scratch behind one shared interface and one shared cost function. Library pathfinding is not used.

| Class | Algorithm | Optimal for c? |
| --- | --- | --- |
| Uninformed, cost-blind | BFS, DFS, Iterative Deepening (IDS) | No: BFS and IDS minimize edge count; DFS minimizes nothing |
| Uninformed, cost-aware | Uniform Cost Search (UCS), Bidirectional UCS | Yes |
| Informed | Greedy Best-First, A\* | Greedy: no. A\*: yes |

**Heuristic:** h(n) = haversine(n, g) / v_max, in minutes. It is admissible because no road is shorter than the straight line and no edge is faster than v_max. It is consistent because the straight-line distance satisfies the triangle inequality.

Cost-blind algorithms still respect impassable edges. The cost of the path they return is measured with the same c, so their results can be compared fairly with the others.

## 8. Research questions

1. **Quality:** How far from optimal are the paths returned by BFS, DFS, IDS and Greedy, measured as cost ÷ UCS cost, and under which conditions does the gap grow?
2. **Effort:** How much does the heuristic (A\*) and the two-sided search (Bidirectional) reduce node expansions, frontier size and runtime compared with UCS, while keeping the same optimal cost?
3. **Sensitivity:** How do the optimal route and the algorithm ranking change across scenarios and traveler profiles? For example, do cost-blind algorithms keep the same path while A\* reroutes?

## 9. Experimental design

**Scenarios:** normal midday; peak hour (16:00–21:00); heavy rain (for example 70 mm, which closes flood hotspots); procession (for example Shahbagh or Paltan blocked).

**Origin–destination pairs:** five fixed demo routes (Mirpur 10 → Dhaka Medical College, Uttara → Motijheel, Mohammadpur → Gulshan 1, Dhanmondi 27 → Banani, Jatrabari → Farmgate), plus a seeded random sample of node pairs for statistical comparison.

**Runs:** every algorithm × scenario × profile × OD pair, with fixed expansion and time limits.

| Metric | Definition |
| --- | --- |
| Path cost | Sum of c over the returned path (minute-equivalents) |
| Suboptimality ratio | Path cost ÷ UCS path cost (1.0 = optimal) |
| Nodes expanded | Number of nodes popped and expanded |
| Max frontier size | Peak frontier length (memory proxy) |
| Runtime | Wall-clock time in ms |
| Success rate | Share of runs that reach the goal within the limits |

**Model validity:** for the five demo routes, compare the model's travel time T with Google Maps estimates at the same time and day. Recalibrate the traffic bands if the mean error is above 30%.

## 10. Deliverables

1. A Dhaka road graph annotated with hotspot flags (flood, blockade-prone, crime, accident, terminal), each traced to a cited source.
2. A cost engine and seven search algorithms, with automated tests for correctness, admissibility, consistency and optimality.
3. An interactive web app where users pick points on the map, change conditions and profiles, compare algorithms side by side with explored-node animation and cost breakdowns, and see the route replanned live when a new blockade appears mid-trip.
4. The comparison results and calibration table that answer the research questions.

## 11. Scope and assumptions

- This is a data-driven simulation, not live navigation. There are no live traffic feeds, and congestion follows average time-of-day patterns.
- Blockades and road works are entered by the user, not predicted.
- The baseline costs every edge at the departure time. Time-dependent costs are an extension.
- Signals, rickshaw mixing, and traffic yielding to ambulances are not modeled separately.
- OpenStreetMap road and one-way data may contain errors.
