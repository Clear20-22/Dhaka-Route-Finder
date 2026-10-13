# Implementation Spec: Dhaka Smart Route Finder

এই file এ website বানানোর পুরো নির্দেশনা আছে, যা VS Code এর Claude Code কে দেওয়ার জন্য লেখা। Problem আর research question আছে [`PROBLEM_STATEMENT.md`](PROBLEM_STATEMENT.md) এ, আর প্রতিটা weight এর পেছনের data ও source আছে [`CONCEPT.md`](CONCEPT.md) এ।

## ০. শুরু করার আগে: যা download ও install করতে হবে

নিচের টেবিলের জিনিসগুলো নিজে install করতে হবে। Project এর library গুলো (OSMnx, FastAPI, React ইত্যাদি) Claude Code নিজেই project এর ভেতরে install করবে।

| কী | কোথা থেকে | নোট |
| --- | --- | --- |
| VS Code (1.94 বা নতুন) | [code.visualstudio.com](https://code.visualstudio.com) | Editor |
| Claude Code extension | VS Code এর Extensions view এ "Claude Code" (Anthropic) | Paid Claude subscription (Pro, Max, Team বা Enterprise) অথবা Claude Console account লাগবে ([docs](https://code.claude.com/docs/en/vs-code.md)) |
| Python 3.12 | [python.org](https://www.python.org/downloads/) | OSMnx 3.9 থেকে 3.13 support করে ([PyPI](https://pypi.org/project/osmnx)); Windows এ install এর সময় "Add python.exe to PATH" টিক দাও |
| Node.js (LTS) | [nodejs.org](https://nodejs.org) | Frontend (React + Vite) এর জন্য; LTS লেখা version টা নাও |
| Git | [git-scm.com](https://git-scm.com) | Version control; Windows এ সাথে Git Bash ও আসে |
| GitHub account | [github.com](https://github.com) | Repo রাখার জন্য |
| Docker Desktop (ঐচ্ছিক) | [docker.com](https://www.docker.com/products/docker-desktop/) | শুধু Docker Compose দিয়ে চালাতে চাইলে |

VS Code এ বাড়তি কাজে লাগবে এমন extension: Python (Microsoft), Tailwind CSS IntelliSense, আর ESLint।

### Install ঠিক হয়েছে কিনা যাচাই

VS Code এর terminal এ এগুলো চালাও, প্রতিটা একটা version দেখাবে।

```bash
code --version      # 1.94 বা বেশি
python --version    # 3.12.x (Mac/Linux এ python3 --version)
node --version
npm --version
git --version
```

### Project এর library (Claude Code install করবে)

Backend এর `requirements.txt` এ এগুলো থাকবে। Python এর library সবসময় project এর virtual environment (`.venv`) এ install হবে, পুরো computer এ না।

```text
osmnx>=2.0          # networkx, geopandas সহ আসে
scikit-learn        # unprojected graph এ nearest node খুঁজতে OSMnx এর লাগে
fastapi
uvicorn[standard]
pydantic>=2
pyyaml
pytest
httpx               # FastAPI এর TestClient এর জন্য
```

Frontend এ লাগবে `react`, `react-dom`, `leaflet`, `react-leaflet`, `tailwindcss`, `typescript`, `vite` আর `vitest`।

প্রথমবার ঢাকার graph নামাতে internet লাগবে, আর OpenStreetMap থেকে নামাতে কয়েক মিনিট সময় লাগতে পারে। একবার নামালে পরে GraphML file থেকে চলবে। Windows এ `pip install osmnx` এ সমস্যা হলে Miniforge (conda-forge) দিয়ে install করে দেখো।

## ১. লক্ষ্য ও scope

Website টা ঢাকার আসল road map এ ৭টা search algorithm চালিয়ে দেখাবে। সময়, বৃষ্টি, অবরোধ বা যাত্রীর ধরন বদলালে route কীভাবে বদলায় তা live দেখা যাবে। মূল উদ্দেশ্য lab demo তে algorithm গুলোর পার্থক্য চোখে দেখানো।

### MVP তে যা থাকবেই

- Map এ click করে start আর goal বাছাই
- ৭টা algorithm: BFS, DFS, IDS, UCS, Bidirectional, Greedy, A\*
- এক বা একাধিক algorithm একসাথে চালিয়ে তুলনা
- Explored node এর animation আর final path, প্রতিটা algorithm আলাদা রঙে
- Scenario control: সময়, দিন, বৃষ্টির mm, যাত্রীর ধরন, অবরোধ ও খোঁড়াখুঁড়ি on/off
- Result টেবিল: cost, distance, nodes expanded, max frontier, runtime
- Route এর প্রতিটা edge এ hover করলে cost এর factor ভাঙানো হিসাব
- Live replanning: চলার পথে অবরোধ হলে route বদলানো

### MVP তে থাকবে না

Live traffic API সংযোগ, user account, আর mobile app পরের ধাপের কাজ।

## ২. Tech stack

Backend Python এ, frontend React এ। একটা কঠিন নিয়ম: **search algorithm গুলো নিজে লিখতে হবে।** NetworkX বা OSMnx শুধু graph load করার জন্য; `nx.shortest_path` বা অন্য কোনো ready-made pathfinding ব্যবহার করা যাবে না।

| Layer | Tool | কেন |
| --- | --- | --- |
| Graph data | OSMnx + NetworkX | OpenStreetMap থেকে ঢাকার road network নামানো ও GraphML এ cache করা |
| Backend | Python 3.12 + FastAPI | Algorithm লেখা সহজ, FastAPI দ্রুত আর `/docs` এ auto API docs দেয় |
| Config | YAML (`weights.yaml`) + JSON (`hotspots.json`) | Weight বদলাতে code ছুঁতে হবে না |
| Frontend | React + Vite + TypeScript | Component ভিত্তিক UI, দ্রুত build |
| Map | Leaflet (react-leaflet) + OpenStreetMap tiles | ফ্রি; Canvas renderer এ হাজার হাজার বিন্দু আঁকা যায় |
| Styling | Tailwind CSS | দ্রুত পরিষ্কার UI, dark mode সহজ |
| Testing | pytest (backend), Vitest (frontend) | Algorithm এর সঠিকতা automated ভাবে যাচাই |
| Run | Docker Compose (ঐচ্ছিক) | এক command এ পুরো project চালানো |

## ৩. System architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ Frontend (React + Leaflet)                                   │
│ ControlPanel · AlgorithmPicker · MapView · ResultsTable ·    │
│ ReplanPanel                                                  │
└───────────────┬──────────────────────────────▲───────────────┘
                │ scenario + start/goal (JSON)  │ path, explored, breakdown
┌───────────────▼──────────────────────────────┴───────────────┐
│ Backend API (FastAPI, /api/*)                                │
│ /search · /replan · /nearest-node · /hotspots · /graph/meta  │
└───────────────┬──────────────────────────────────────────────┘
┌───────────────▼──────────────────────────────────────────────┐
│ Engine                                                       │
│ scenario.py → cost.py (edge_cost, heuristic) → search/ (৭টা) │
│ replan.py                                                    │
└───────────────┬──────────────────────────────────────────────┘
┌───────────────▼──────────────────────────────────────────────┐
│ Data (server চালুর সময় একবার load)                           │
│ dhaka_drive.graphml · weights.yaml · hotspots.json           │
└───────────────▲──────────────────────────────────────────────┘
                │ project শুরুতে একবার
   scripts/: prepare_graph.py → map_hotspots.py   (run_experiments.py Engine সরাসরি ব্যবহার করে)
```

Frontend scenario পাঠায়; backend সেই scenario থেকে cost বানিয়ে search চালায়। Data layer server চালু হওয়ার সময় একবার load হয়, আর offline script গুলো শুধু project শুরুতে একবার চালাতে হয়।

## ৪. Project structure

Repo টা দুই ভাগে: `backend/` আর `frontend/`। প্রতিটা algorithm আলাদা file এ, যাতে viva তে সহজে দেখানো যায়।

```text
dhaka-smart-route/
├── CLAUDE.md                    # Claude Code এর জন্য স্থায়ী নিয়ম (১৩ নম্বর অংশ)
├── README.md
├── .gitignore                   # .venv, node_modules, *.graphml
├── docs/
│   ├── PROBLEM_STATEMENT.md     # problem, research question, experiment design
│   ├── CONCEPT.md               # ধারণা, বাস্তব data, source
│   └── SPEC.md                  # এই file
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app ও route
│   │   ├── config.py            # weights.yaml ও hotspots.json load
│   │   ├── graph_store.py       # cache থেকে graph load, nearest node খোঁজা
│   │   ├── scenario.py          # Scenario ও Profile model
│   │   ├── cost.py              # edge cost function ও heuristic
│   │   ├── replan.py            # live replanning
│   │   ├── schemas.py           # Pydantic request/response model
│   │   └── search/
│   │       ├── base.py          # SearchResult, SearchLimits, path reconstruct
│   │       ├── bfs.py
│   │       ├── dfs.py
│   │       ├── ids.py
│   │       ├── ucs.py
│   │       ├── bidirectional.py
│   │       ├── greedy.py
│   │       └── astar.py
│   ├── data/
│   │   ├── weights.yaml
│   │   ├── hotspots.json
│   │   └── dhaka_drive.graphml  # prepare_graph.py বানাবে (git এ রাখবে না)
│   ├── scripts/
│   │   ├── prepare_graph.py     # OSMnx দিয়ে graph download ও attribute যোগ
│   │   ├── map_hotspots.py      # hotspot এর lat/lng → কাছের edge এ flag
│   │   └── run_experiments.py   # সব algorithm × scenario × profile × route চালিয়ে CSV
│   ├── results/                 # run_experiments.py এর CSV ও summary
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts               # backend call
│   │   ├── types.ts
│   │   ├── strings.ts           # সব UI লেখা এক জায়গায়
│   │   └── components/
│   │       ├── MapView.tsx      # map, path, explored animation, hotspot layer
│   │       ├── ControlPanel.tsx # scenario control
│   │       ├── AlgorithmPicker.tsx
│   │       ├── ResultsTable.tsx
│   │       └── ReplanPanel.tsx
│   └── package.json
└── docker-compose.yml
```

## ৫. Data model ও config

Graph টা OSM এর directed MultiDiGraph, তাই one-way রাস্তা ঠিক থাকে। একই দুই node এর মধ্যে একাধিক edge থাকলে search সবচেয়ে কম cost এর edge টা নেবে।

### Edge attribute (prepare\_graph.py আর map\_hotspots.py যোগ করবে)

| Attribute | Type | উৎস | মানে |
| --- | --- | --- | --- |
| `length_m` | float | OSM | রাস্তার দৈর্ঘ্য, মিটারে |
| `highway` | string | OSM | Road type (primary, residential ইত্যাদি) |
| `v_free_kmh` | float | `weights.yaml` এর `road_speeds_kmh` | যানজটহীন speed |
| `road_class` | "main" বা "local" | `highway` থেকে | কোন traffic profile পাবে |
| `flood_hotspot` | bool | `hotspots.json` | জলাবদ্ধতা hotspot |
| `blockade_prone` | bool | `hotspots.json` | অবরোধ-প্রবণ মোড়ের কাছে |
| `crime_hotspot` | bool | `hotspots.json` | ছিনতাই hotspot |
| `accident_hotspot` | bool | `hotspots.json` | দুর্ঘটনা-প্রবণ এলাকা |
| `terminal_zone` | bool | `hotspots.json` | Bus/truck terminal এর কাছে |

Graph এর metadata তে `v_max_kmh` রাখতে হবে, যা সব edge এর `v_free_kmh` এর সর্বোচ্চ মান। Heuristic এটা ব্যবহার করবে।

### OSMnx এর সাথে কাজের নোট

- OSMnx এ দৈর্ঘ্যের attribute এর নাম `length` (মিটার); `prepare_graph.py` সেটা `length_m` নামে রাখবে।
- Simplify করা graph এ `highway` কখনো list হয় (যেমন `["primary", "secondary"]`); তখন সবচেয়ে দ্রুত type টা নাও। `primary_link` এর মত `_link` type কে মূল type ধরো।
- Node এর lat হলো `y`, lng হলো `x`।
- OSMnx 2.x এ bbox এর ক্রম (left, bottom, right, top), মানে (west, south, east, north) ([changelog](https://data.safetycli.com/changelogs/osmnx))। Place এর নাম দিয়ে ঢাকা ঠিকমতো না এলে bbox ব্যবহার করো।
- Unprojected graph এ `ox.distance.nearest_nodes` চালাতে scikit-learn লাগে।
- Download এর পর শুধু largest strongly connected component রাখা হয়। নইলে bbox এর কিনারায় কাটা one-way রাস্তার কারণে এমন node থাকে যেখান থেকে বের হওয়া যায় না, আর সেখানে click করলে algorithm না, data র কারণে `not_found` আসে।
- OSM এ ঢাকার বেশিরভাগ রাস্তার নাম বাংলায় (যেমন Elevated Expressway = `ঢাকা এলিভেটেড এক্সপ্রেসওয়ে`, tag `motorway`)। নাম দিয়ে খোঁজার সময় বাংলা নামও দেখতে হবে।

### hotspots.json

প্রতিটা hotspot একটা বিন্দু আর radius। `map_hotspots.py` সেই radius এর ভেতরে যেসব edge এর মাঝখান পড়ে, সেগুলোতে flag বসাবে। `type` হবে `flood`, `blockade`, `crime`, `accident` বা `terminal`। নিচের coordinate আনুমানিক, তাই OSM এ যাচাই করে নিতে হবে।

```json
{
  "version": "2026-10-12",
  "hotspots": [
    {
      "id": "flood-new-market",
      "type": "flood",
      "name": "New Market",
      "lat": 23.7334,
      "lng": 90.3847,
      "radius_m": 300,
      "source": "https://www.bssnews.net/js-session/401176/news"
    },
    {
      "id": "blockade-shahbagh",
      "type": "blockade",
      "name": "Shahbagh intersection",
      "lat": 23.7380,
      "lng": 90.3958,
      "radius_m": 250,
      "source": "https://en.ittefaq.com.bd/14056/road-blockades-cause-severe-traffic-congestion-in"
    }
  ]
}
```

`docs/CONCEPT.md` এর ২ক অংশের সব hotspot এই ফাইলে যাবে, প্রতিটার সাথে source link। Airport Road এর মত লম্বা রাস্তার জন্য রাস্তা বরাবর কয়েকটা বিন্দু দাও।

### weights.yaml

সব সংখ্যা শুরুর অনুমান, `docs/CONCEPT.md` এর ২ক আর ৩ নম্বর অংশ থেকে নেওয়া। Code এ কোনো সংখ্যা hardcode করা যাবে না।

```yaml
graph_area:               # prepare_graph.py যে এলাকা নামাবে
  bbox: {west: 90.33, south: 23.69, east: 90.51, north: 23.90}
  network_type: drive

road_speeds_kmh:          # v_free, অনুমান
  motorway: 60            # Elevated Expressway; OSM এ আসল tag prepare_graph.py তে দেখে নিতে হবে
  trunk: 40
  primary: 30
  secondary: 25
  tertiary: 20
  residential: 15
  default: 15
main_road_types: [motorway, trunk, primary, secondary]

traffic_bands:            # F_traffic, main road, weekday
  - {from: "22:00", to: "05:00", factor: 1.1}
  - {from: "05:00", to: "07:00", factor: 1.5}
  - {from: "07:00", to: "10:00", factor: 4.0}
  - {from: "10:00", to: "16:00", factor: 3.0}
  - {from: "16:00", to: "21:00", factor: 5.0}
  - {from: "21:00", to: "22:00", factor: 2.0}
local_road_scale: 0.5     # local road: 1 + (F - 1) × 0.5
weekend_days: [FRI, SAT]
weekend_scale: 0.5        # weekend: 1 + (F - 1) × 0.5

rain_bands:               # শুধু flood_hotspot edge এ
  - {max_mm: 25, factor: 1.3}
  - {max_mm: 60, factor: 3.0}
  - {max_mm: .inf, factor: .inf}
flood_recovery_hours: 3

blockade_spillover: 2.0   # বন্ধ মোড়ের পাশের edge এ
spillover_radius_m: 500
work_zone_factor: 2.0

risk:
  crime:    {day: 1, night: 3, predawn: 5}
  accident: {day: 1, night: 2, predawn: 2}
risk_ref_length_m: 500    # L_ref: risk প্রতি edge এ না, প্রতি ৫০০ m এ
risk_bands:
  day:     ["06:00", "19:00"]
  night:   ["19:00", "03:00"]
  predawn: ["03:00", "06:00"]

uncertainty:
  blockade_prone: 1.0
  flood_hotspot_monsoon: 0.5
monsoon_months: [6, 7, 8, 9]

profiles:
  ambulance:  {lambda: 0.5, beta: 0.5, gridlock_threshold: 4.0, avoid_rain_factor: 3.0, work_zone_extra: 1.5}
  meeting:    {lambda: 1.0, beta: 1.0}
  night_solo: {lambda: 5.0, beta: 0.3}
  general:    {lambda: 1.0, beta: 0.3}
  bus_truck:  {lambda: 1.0, beta: 0.3, terminal_factor: 1.5}

limits:
  max_expanded_nodes: 300000
  timeout_ms: 10000
  ids_max_depth: 400
  explored_trace_cap: 50000
```

Traffic band গুলো দুটো data র উপর দাঁড়ানো: সর্বোচ্চ factor ≈ ৫ (২৫ ÷ ৪.৮ km/h) আর রাত ১০টা থেকে ভোর ৫টা কম traffic। মাঝের band গুলো অনুমান, calibration (১১ নম্বর অংশ) এর পর ঠিক করতে হবে।

## ৬. Cost engine (`cost.py`)

প্রতিটা search request এ scenario থেকে একবার cost function বানানো হয়, আর সব algorithm একই function ব্যবহার করে। MVP তে সব edge এর cost রওনা দেওয়ার সময় ধরে হিসাব হবে; প্রতিটা edge এ পৌঁছানোর সময় ধরে হিসাব (time-dependent) পরের ধাপের কাজ।

```latex
\begin{aligned}
\text{cost}(u,v,t) &= T(u,v,t) \times \big(1 + \beta \, U(u,v)\big) + \lambda \times \big(R_{crime}(t) + R_{accident}(t)\big) \times \frac{L(u,v)}{L_{ref}} \\
T(u,v,t) &= \frac{L(u,v)}{v_{free}(u,v)} \times F_{traffic}(t, day) \times F_{rain} \times F_{work}
\end{aligned}
```

### Reference implementation

```python
INF = float("inf")

def edge_cost(e, s: Scenario, p: Profile, w: Weights) -> float:
    if e.u in s.blocked_nodes or e.v in s.blocked_nodes:
        return INF                                   # অবরোধ

    base_min = (e.length_m / 1000) / e.v_free_kmh * 60   # মিনিট

    f_traffic = traffic_factor(s.time, s.day, e.road_class, w)
    if e.id in s.spillover_edges:
        f_traffic *= w.blockade_spillover
    if p.name == "ambulance" and f_traffic < p.gridlock_threshold:
        f_traffic = max(1.0, f_traffic / 2)          # উল্টো lane এর সুবিধা, gridlock এ না

    f_rain = rain_factor(s.rain_mm, s.hours_since_rain, e.flood_hotspot, w)
    if f_rain == INF:
        return INF
    if p.name == "ambulance" and f_rain >= p.avoid_rain_factor:
        return INF                                   # ambulance পানি জমা রাস্তা এড়ায়

    f_work = w.work_zone_factor if e.id in s.work_zone_edges else 1.0
    if p.name == "ambulance" and f_work > 1.0:
        f_work *= p.work_zone_extra
    if p.name == "bus_truck" and e.terminal_zone:
        f_work *= p.terminal_factor

    T = base_min * f_traffic * f_rain * f_work
    U = uncertainty(e, s.month, w)                   # 0, 0.5 বা 1
    R = risk(e, s.time, w)                           # hotspot না হলে 0
    exposure = e.length_m / w.risk_ref_length_m      # edge কত ছোট করে কাটা তার উপর নির্ভর না করতে
    return T * (1 + p.beta * U) + p.lam * R * exposure


def heuristic(n, goal, g) -> float:
    d_km = haversine_km(g.nodes[n], g.nodes[goal])
    return d_km / g.graph["v_max_kmh"] * 60          # মিনিট
```

### যে নিয়মগুলো ভাঙা যাবে না

- `F_traffic`, `F_rain`, `F_work` সবসময় ১ বা বেশি; `U` আর `R` সবসময় ০ বা বেশি। এতে heuristic admissible ও consistent থাকে।
- Cost ∞ মানে edge টা নেই; সব algorithm, BFS আর DFS সহ, এই edge বাদ দেবে।
- `19:00` থেকে `03:00` এর মত মধ্যরাত পার হওয়া band ঠিকভাবে handle করতে হবে।
- `rain_factor` বৃষ্টি চলাকালে আর থামার পর `flood_recovery_hours` পর্যন্ত কাজ করবে।
- `spillover_edges` হলো বন্ধ node থেকে `spillover_radius_m` এর মধ্যে থাকা edge, যা scenario বানানোর সময় একবার হিসাব হবে।
- Final path এর প্রতিটা edge এর জন্য factor গুলো আলাদা করে ফেরত দেওয়ার একটা `edge_breakdown()` function থাকবে, যা frontend এর hover এ দেখাবে।
- `weights.yaml` এর `lambda` Python এ keyword, তাই code এ `lam` নামে load করো।
- Risk সবসময় `length_m / risk_ref_length_m` দিয়ে গুণ হবে। OSM একটা hotspot কে অনেক edge এ ভাগ করে; প্রতি edge এ পুরো R যোগ করলে একই রাস্তা কয়টা edge এ কাটা তার উপর penalty বদলে যেত।

## ৭. Search engine (`search/`)

সাতটা algorithm একই interface মানবে, তাই frontend আর test সবাইকে একভাবে চালাতে পারে। তুলনা fair রাখতে BFS, DFS আর IDS যে path দেয়, তার cost ও একই `edge_cost` দিয়ে হিসাব হবে।

```python
@dataclass
class SearchLimits:
    max_expanded: int = 300_000
    timeout_ms: int = 10_000
    ids_max_depth: int = 400
    trace_cap: int = 50_000

@dataclass
class SearchResult:
    algorithm: str
    status: Literal["found", "not_found", "limit_reached", "timeout"]
    path: list[int]            # OSM node id, start থেকে goal
    cost_min: float            # path এর edge_cost যোগফল
    distance_m: float
    nodes_expanded: int
    max_frontier: int
    runtime_ms: float
    explored: list[int]        # expand হওয়ার ক্রমে, trace_cap পর্যন্ত

def search(graph, start, goal, cost_fn, h_fn, limits) -> SearchResult: ...
```

| Algorithm | Frontier | নিয়ম |
| --- | --- | --- |
| BFS | FIFO queue | Generate করার সময় goal test; visited set |
| DFS | Stack (iterative, recursion না) | Visited set; neighbor ক্রম node id অনুযায়ী, যাতে ফল প্রতিবার একই হয় |
| IDS | Depth-limited DFS, depth 0 থেকে `ids_max_depth` | প্রতি iteration এ path এর ভেতরে cycle check; সব iteration এর expanded যোগ করে report |
| UCS | Min-heap (g) | Pop করার সময় goal test; পুরনো heap entry skip |
| Bidirectional | দুটো min-heap: forward graph আর reverse graph | Stop যখন দুই দিকের heap এর top এর যোগফল ≥ এ পর্যন্ত পাওয়া সেরা মিলন cost (μ) |
| Greedy | Min-heap (h) | Visited set; optimal না |
| A\* | Min-heap (g + h) | h consistent, তাই closed node আবার খুলতে হয় না; সমান f হলে বড় g আগে |

### Real map এর জন্য সাবধানতা

- হাজার হাজার node এ DFS অদ্ভুত লম্বা পথ দেবে আর IDS অনেক ধীর হবে। এটা demo তে দেখানোর মত, তবে `max_expanded` বা `timeout_ms` পার হলে search থেমে `limit_reached` বা `timeout` status দেবে।
- Bidirectional এর backward search এ edge এর উল্টো দিক (incoming edge) ব্যবহার হবে, কারণ one-way রাস্তা আছে।
- Recursion ব্যবহার করা যাবে না, Python এর recursion limit এ crash করবে।
- `explored` বেশি বড় হলে প্রথম `trace_cap` টা node পাঠানো হবে, আর `nodes_expanded` এ আসল সংখ্যা থাকবে।

## ৮. Backend API

সব endpoint `/api` এর নিচে, JSON এ কথা বলে। Server চালু হওয়ার সময় graph একবার memory তে load হবে, প্রতি request এ না।

| Method | Path | কাজ |
| --- | --- | --- |
| GET | `/api/health` | Server চলছে কিনা |
| GET | `/api/graph/meta` | Node ও edge সংখ্যা, map এর সীমানা, `v_max_kmh` |
| GET | `/api/hotspots` | Map এ দেখানোর জন্য সব hotspot |
| GET | `/api/nearest-node?lat=&lng=` | Click করা জায়গার সবচেয়ে কাছের node |
| GET | `/api/config/weights` | বর্তমান weights, UI তে দেখানোর জন্য |
| POST | `/api/search` | এক বা একাধিক algorithm চালানো |
| POST | `/api/replan` | চলমান যাত্রায় নতুন ঘটনার পর route আবার হিসাব (১০ নম্বর অংশ) |

### POST /api/search: request

নিচের coordinate গুলো Mirpur 10 থেকে Dhaka Medical College এর আনুমানিক উদাহরণ। day এর মান SAT, SUN, MON, TUE, WED, THU বা FRI; month ১ থেকে ১২।

```json
{
  "start": {"lat": 23.8069, "lng": 90.3687},
  "goal":  {"lat": 23.7259, "lng": 90.3976},
  "algorithms": ["astar", "ucs", "greedy", "bfs"],
  "scenario": {
    "time": "17:30",
    "day": "SUN",
    "month": 7,
    "rain_mm": 40,
    "hours_since_rain": 0,
    "profile": "ambulance",
    "blocked_nodes": [],
    "work_zone_edges": []
  },
  "include_explored": true
}
```

### POST /api/search: response

সংখ্যাগুলো শুধু format দেখানোর জন্য, আসল ফল না।

```json
{
  "results": [
    {
      "algorithm": "astar",
      "status": "found",
      "path": [[23.8069, 90.3687], [23.8012, 90.3701]],
      "path_edges": [
        {"from": 1, "to": 2, "base_min": 0.9, "f_traffic": 2.5, "f_rain": 1.0,
         "f_work": 1.0, "U": 0.0, "R": 0.0, "cost_min": 2.25}
      ],
      "cost_min": 48.6,
      "distance_m": 11230,
      "nodes_expanded": 18234,
      "max_frontier": 2210,
      "runtime_ms": 142.5,
      "explored": [[23.8069, 90.3687]]
    }
  ],
  "warnings": []
}
```

Frontend যাতে সরাসরি আঁকতে পারে, তাই `path` আর `explored` lat/lng জোড়া হিসেবে আসবে। Start থেকে goal এ পৌঁছানোর কোনো পথ না থাকলে `status` হবে `not_found`, আর `warnings` এ কারণ লেখা থাকবে।

## ৯. Frontend

বাম পাশে control panel (প্রায় ৩২০px), ডানে পুরো map, আর নিচে ভাঁজ করা যায় এমন result টেবিল। Light আর dark দুই theme থাকবে।

### Control panel

- **Start ও goal:** map এ প্রথম click start (সবুজ marker), দ্বিতীয় click goal (লাল marker); marker টেনে বদলানো যাবে
- **Preset route button:** Mirpur 10 → Dhaka Medical College, Uttara → Motijheel, Mohammadpur → Gulshan 1, demo তে দ্রুত দেখানোর জন্য
- **সময় ও দিন:** ১৫ মিনিট step এর slider, আর শনি থেকে শুক্র dropdown
- **বৃষ্টি:** ০ থেকে ১৫০ mm slider, সাথে মাস বাছাই (বর্ষাকাল বোঝার জন্য)
- **যাত্রী:** Ambulance, জরুরি meeting, রাতে একা যাত্রী, সাধারণ যাত্রী, Bus/truck
- **Algorithm:** ৭টা checkbox আর একটা "সব তুলনা করো" button
- **Map mode:** "Route ঠিক করো", "অবরোধ দাও" (click করা মোড় বন্ধ, লাল ✕), "খোঁড়াখুঁড়ি দাও"
- **Animation:** Play, Pause, Skip আর speed slider

### Map এ যা দেখা যাবে

- প্রতিটা algorithm এর নিজস্ব স্থির রঙ; explored node ছোট বিন্দু, final path মোটা লাইন
- Explored animation `explored` এর ক্রম ধরে চলবে, যাতে BFS এর ছড়িয়ে পড়া আর A\* এর সোজা goal এর দিকে যাওয়া চোখে পড়ে
- Hotspot layer on/off: জলাবদ্ধতা, অবরোধ-প্রবণ, ছিনতাই, দুর্ঘটনা, terminal আলাদা রঙ ও icon এ, সাথে legend
- Path এর edge এ hover করলে `path_edges` থেকে factor গুলো দেখাবে (যেমন F\_traffic ২.৫, F\_rain ১.০, cost ২.২৫ মিনিট)
- Leaflet এর Canvas renderer (`preferCanvas`) চালু থাকবে, নইলে হাজার হাজার বিন্দুতে map ধীর হয়ে যাবে

### Result টেবিল

Column: algorithm, status, cost (মিনিট), cost ÷ সেরা cost, distance (km), nodes expanded, max frontier, runtime (ms)। "cost ÷ সেরা cost" হলো ওই run এর optimal algorithm (UCS, A\* বা Bidirectional) এর cost দিয়ে ভাগ; UCS না চালালেও A\* বা Bidirectional থাকলে হিসাব হবে, কোনোটাই না থাকলে "–"। সবচেয়ে কম cost এর row highlight হবে, আর optimal না হওয়া algorithm (BFS, DFS, IDS, Greedy) এর পাশে ছোট চিহ্ন থাকবে।

### UX এর ছোট নিয়ম

- Search চলাকালে loading অবস্থা দেখাবে, আর backend error হলে পরিষ্কার বাংলা বার্তা
- `limit_reached` বা `timeout` হলে টেবিলে কারণসহ দেখাবে, crash করবে না
- সব UI লেখা এক জায়গায় (`strings.ts`) রাখবে, যাতে বাংলা বা ইংরেজি বদলানো সহজ হয়

## ১০. Live replanning simulation

এটা demo র সবচেয়ে চোখে পড়ার মত অংশ: গাড়ি চলার মাঝে অবরোধ পড়লে route বদলে যায়। MVP তে বর্তমান node থেকে নতুন করে A\* চালানো হবে, যা real map এও যথেষ্ট দ্রুত; D\* Lite পরের ধাপে।

1. User "যাত্রা শুরু" চাপলে vehicle marker path ধরে চলবে। Simulation clock এ ১ সেকেন্ড = ১ মিনিট, speed বদলানো যাবে।
2. চলার মাঝে user কোনো মোড়ে অবরোধ দেয়, বৃষ্টি বাড়ায় বা খোঁড়াখুঁড়ি যোগ করে।
3. Frontend `POST /api/replan` পাঠায়: বর্তমান node, বাকি path, আর scenario এর সময় এ পর্যন্ত কাটানো সময় যোগ করে আপডেট করা।
4. Backend বাকি path এর cost নতুন scenario তে হিসাব করে। বাকি path এ কোনো edge ∞ হলে, বা নতুন route বেশি ভালো হলে, নতুন route দেয়।
5. Map এ পুরনো বাকি route ধূসর dashed লাইন, নতুন route উজ্জ্বল। উপরে একটা banner: কেন বদলালো আর কত মিনিট বাড়লো বা কমলো।

```json
POST /api/replan
{
  "current_node": 987654321,
  "goal": {"lat": 23.7259, "lng": 90.3976},
  "remaining_path": [987654321, 555, 666],
  "scenario": {"time": "17:52", "day": "SUN", "month": 7, "rain_mm": 40,
               "hours_since_rain": 0, "profile": "ambulance",
               "blocked_nodes": [555], "work_zone_edges": []},
  "algorithm": "astar"
}
```

Response এ থাকবে `changed` (true বা false), `reason` (যেমন `blocked_node_on_path`), `old_remaining_cost_min`, `new_cost_min`, আর নতুন route এর পুরো `SearchResult`।

## ১১. Testing ও calibration

Test গুলো প্রমাণ করবে algorithm ঠিক কাজ করছে, আর calibration দেখাবে model এর সময় বাস্তবের কাছাকাছি কিনা। দুটোই viva তে বড় শক্তি।

### Backend test (pytest)

- **Cost:** হাতে বানানো ছোট graph এ প্রতিটা factor আলাদা করে test: rain band এর সীমা, অবরোধে ∞, ambulance এর gridlock নিয়ম, weekend scale, মধ্যরাত পার হওয়া band, আর একটা hotspot edge কে দুই ভাগ করলে মোট risk penalty একই থাকে
- **Admissibility:** random ১,০০০ node pair এ h(start) ≤ UCS এর আসল cost
- **Consistency:** random edge sample এ h(u) ≤ cost(u, v) + h(v)
- **Optimality:** random ২০০ pair এ UCS, A\* আর Bidirectional এর cost সমান (tolerance 1e-6)
- **BFS:** BFS path এর edge সংখ্যা অন্য কোনো algorithm এর path এর চেয়ে বেশি না
- **Blocked edge:** কোনো algorithm এর path এ ∞ cost এর edge নেই
- **Limits:** `max_expanded` পার হলে status `limit_reached`, ছোট timeout এ `timeout`
- **API:** `/api/search` আর `/api/replan` এর request ও response schema test

Random test এর seed fix রাখতে হবে, যাতে ফল প্রতিবার একই আসে।

### Experiment runner (`run_experiments.py`)

Website demo এর জন্য, কিন্তু report এর research question (`PROBLEM_STATEMENT.md` এর ৮ নম্বর অংশ) এর উত্তর আসবে এই script থেকে। এটা API ছাড়াই সরাসরি `cost.py` আর `search/` ব্যবহার করবে।

- **Scenario:** স্বাভাবিক দুপুর, peak hour, ভারী বৃষ্টি (৭০ mm), মিছিল (Shahbagh ও Paltan বন্ধ); সংজ্ঞা `weights.yaml` এর মত একটা `experiments.yaml` এ, code এ না
- **Route:** নিচের calibration টেবিলের ৫টা route, আর fixed seed এ random ৫০টা node pair (seed আর সংখ্যা `experiments.yaml` এ)
- **Run:** ৭ algorithm × ৪ scenario × ৫ profile × প্রতিটা route, `limits` মেনে
- **Output:** `results/runs.csv` এ প্রতিটা run এর এক row (algorithm, scenario, profile, route, status, cost, cost ÷ UCS cost, distance, nodes expanded, max frontier, runtime); `results/summary.csv` এ algorithm × scenario অনুযায়ী median ও success rate
- Random pair থেকে start আর goal এর মধ্যে কোনো পথ না থাকলে সেই pair বাদ দিয়ে নতুন pair নেবে, আর কয়টা বাদ গেল তা log করবে

### Calibration টেবিল

প্রতিটা route এ Google Maps এর দেখানো সময় আর model এর সময় পাশাপাশি লেখো। গড় পার্থক্য ৩০% এর বেশি হলে `weights.yaml` এর `traffic_bands` ঠিক করো, তারপর আবার মেলাও।

| Route | সময় ও দিন | Google Maps (মিনিট) | Model (মিনিট) | পার্থক্য (%) |
| --- | --- | --- | --- | --- |
| Mirpur 10 → Dhaka Medical College | রবিবার ১৭:৩০ |  |  |  |
| Uttara → Motijheel | সোমবার ০৯:০০ |  |  |  |
| Mohammadpur → Gulshan 1 | মঙ্গলবার ১৩:০০ |  |  |  |
| Dhanmondi 27 → Banani | শুক্রবার ১১:০০ |  |  |  |
| Jatrabari → Farmgate | বুধবার ২০:০০ |  |  |  |

## ১২. Limitations

এই system একটা data-ভিত্তিক simulation, live navigation app না। Sir জিজ্ঞেস করার আগেই এগুলো স্বীকার করলে কাজটা বেশি বিশ্বাসযোগ্য লাগে।

- Weight গুলো খবর ও গবেষণা থেকে নেওয়া অনুমান, কোনো live sensor data না।
- Live traffic feed নেই; সময় অনুযায়ী গড় pattern ধরা হয়েছে।
- অবরোধ আগে থেকে জানা যায় না, তাই user কে হাতে চালু করতে হয়।
- Hotspot তালিকা সময়ের সাথে বদলায়; `hotspots.json` এ version আর source রাখা হয়েছে আপডেটের জন্য।
- Signal, রিকশা, বা ambulance কে অন্য গাড়ি রাস্তা ছেড়ে দেওয়া আলাদা করে model করা হয়নি।
- OSM এ কিছু রাস্তা বা one-way তথ্য ভুল থাকতে পারে। যেমন উত্তরের BRT Line 3 এর lane OSM এ `motorway` আর কোনো access বাধা ছাড়া, তাই graph এ সাধারণ গাড়িও সেটা ব্যবহার করতে পারে।
- MVP তে cost রওনা দেওয়ার সময় ধরে হিসাব হয়, তাই লম্বা যাত্রায় মাঝপথের সময়ের traffic পুরোপুরি ধরা পড়ে না।

## ১৩. Claude Code দিয়ে build plan

পুরো project একবারে না বানিয়ে পাঁচটা phase এ ভাগ করো। প্রতিটা phase শেষে Claude Code কে test চালাতে বলো, নিজে চালিয়ে দেখো, তারপর git commit করে পরের phase এ যাও।

### Phase 1: Data ও graph

- [x] `docs/`, `CLAUDE.md`, `README.md`, `.gitignore`
- [ ] বাকি repo structure বানানো (৪ নম্বর অংশ)
- [x] `prepare_graph.py`: OSMnx দিয়ে Dhaka drive network download, `v_free_kmh` আর `road_class` যোগ, `v_max_kmh` metadata, GraphML এ save
- [x] `hotspots.json`: `docs/CONCEPT.md` এর ২ক অংশের সব hotspot, coordinate যাচাই করে, source সহ
- [x] `map_hotspots.py`: hotspot থেকে edge flag
- [x] `weights.yaml` (prepare_graph.py এর road speed লাগে বলে Phase 1 এ), `config.py`, `graph_store.py`, `geo.py` (haversine), Phase 1 test

### Phase 2: Cost ও search engine

- [ ] `weights.yaml`, `config.py`, `scenario.py`, `cost.py` (৬ নম্বর অংশ)
- [ ] ৭টা algorithm, একই interface (৭ নম্বর অংশ)
- [ ] ১১ নম্বর অংশের সব backend test pass

### Phase 3: Backend API

- [ ] FastAPI endpoint, Pydantic schema, frontend এর জন্য CORS
- [ ] `path_edges` breakdown আর `explored` এর lat/lng

### Phase 4: Frontend

- [ ] Map, control panel, algorithm picker, preset route
- [ ] Explored animation, path, hotspot layer আর legend
- [ ] Result টেবিল, "সব তুলনা করো" mode, edge hover breakdown

### Phase 5: Replanning ও polish

- [ ] Trip simulation আর `/api/replan`
- [ ] Dark mode, loading অবস্থা, error বার্তা
- [ ] `run_experiments.py` চালিয়ে `results/` এর CSV বানানো
- [ ] Calibration টেবিল পূরণ, `README.md` এ চালানোর নিয়ম

### Claude Code কে প্রথম prompt

Repo খুলে নিচের লেখাটা Claude Code এ paste করো।

```text
docs/SPEC.md পড়ো। এটা Dhaka Smart Route Finder project এর পুরো spec।

নিয়ম:
1. Search algorithm গুলো নিজে লিখবে। networkx এর shortest_path বা অন্য কোনো
   ready-made pathfinding ব্যবহার করবে না। NetworkX/OSMnx শুধু graph load এর জন্য।
2. সব weight weights.yaml থেকে আসবে, code এ কোনো সংখ্যা hardcode করবে না।
3. Spec এর বাইরে কিছু করার দরকার হলে আগে আমাকে জিজ্ঞেস করবে।
4. প্রতিটা phase শেষে test চালিয়ে ফল দেখাবে, আমার confirmation নিয়ে পরের phase এ যাবে।

এখন Phase 1 শুরু করো। কাজ শুরুর আগে তোমার plan সংক্ষেপে বলো।
```

পরের phase গুলোর জন্য শুধু লিখলেই হবে: "SPEC.md এর Phase 2 শুরু করো, আগে plan বলো।"

নিয়মগুলো স্থায়ী রাখতে repo root এ `CLAUDE.md` file বানিয়ে উপরের ১ থেকে ৪ নম্বর নিয়ম সেখানে লিখে রাখো; Claude Code প্রতিটা conversation এ এই file পড়ে। প্রতিটা phase শুরুর আগে prompt box এর নিচ থেকে Plan mode চালু করো, তাহলে Claude Code আগে plan দেখাবে আর তুমি অনুমোদন দিলে তবেই code লিখবে ([docs](https://code.claude.com/docs/en/vs-code.md))।
