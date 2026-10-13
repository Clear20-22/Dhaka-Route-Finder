# Dhaka City Route Finding Using Search Algorithms

Oct 12, 2026 · @Jubayer Ahmed Sojib

এই file এ ধারণা আর গবেষণা; website বানানোর পুরো নির্দেশনা আছে [`SPEC.md`](SPEC.md) এ।

## Problem Statement

আনুষ্ঠানিক problem statement, research question আর experiment design আছে [`PROBLEM_STATEMENT.md`](PROBLEM_STATEMENT.md) এ। এই file এ আছে তার পেছনের ধারণা, বাস্তব data আর source।

## ১. Dhaka কে graph হিসেবে দেখা

প্রতিটা গুরুত্বপূর্ণ মোড় বা জায়গা হবে একটা node, আর দুটো মোড়ের মাঝের রাস্তা হবে একটা edge। Node এর উদাহরণ: Farmgate, Shahbag, Mohakhali, Gulistan, Motijheel, Jatrabari, Dhanmondi 27, Mirpur 10, Uttara, Rampura।

ছোট demo র জন্য ১৫ থেকে ২৫টা node যথেষ্ট হত, কিন্তু আমরা real map ব্যবহার করবো। Python এর OSMnx library দিয়ে OpenStreetMap থেকে Dhaka এর আসল road network নামানো হবে।

Real map এ হাজার হাজার node থাকবে, তাই algorithm গুলোর পার্থক্য আরও স্পষ্ট বোঝা যাবে। প্রতিটা edge এর weight বাস্তব data থেকে কীভাবে আসবে, তা ২ক অংশে আছে।

## ২. আসল চ্যালেঞ্জ: cost টা fixed না

সাধারণ shortest path এ edge cost মানে শুধু distance। কিন্তু Dhaka তে একই রাস্তার সময় পরিস্থিতি অনুযায়ী অনেক বদলায়।

উদাহরণ: Farmgate থেকে Karwan Bazar এর এক কিলোমিটার রাস্তা দুপুরে হয়তো ৪ মিনিট লাগে, অফিস ছুটির সময় ২০ মিনিট। বৃষ্টিতে পানি জমলে হয়তো যাওয়াই যায় না।

তাই প্রতিটা edge এ এই তথ্যগুলো রাখতে হবে:

- distance (km)
- স্বাভাবিক speed (km/h)
- কোন সময়ে কতটা jam হয় (traffic factor)
- বৃষ্টিতে পানি জমে কিনা (যেমন শান্তিনগর, মালিবাগ বা গ্রিন রোডের মত এলাকা)
- নিরাপত্তা ঝুঁকি (risk score)

Scenario অনুযায়ী এই তথ্য থেকে cost হিসাব হবে। মিছিল বা মিটিংয়ের কারণে কোনো রাস্তা বন্ধ থাকলে সেই edge পুরোপুরি বাদ দিতে হবে।

## ২ক. বাস্তব data থেকে dynamic weight

Real map এর প্রতিটা edge এর weight আসবে আটটা বাস্তব সমস্যা থেকে, প্রতিটার পেছনে খবর বা গবেষণার data আছে। টেবিলের "বাস্তব data" কলাম source থেকে নেওয়া। "Weight" কলামের সংখ্যাগুলো সেই data থেকে আমাদের শুরুর অনুমান, যা পরে calibrate করতে হবে।

| সমস্যা | বাস্তব data | Weight (শুরুর অনুমান) | কোন edge এ |
| --- | --- | --- | --- |
| Traffic jam | মূল রাস্তায় গড় গতি ৪.৮ km/h (এপ্রিল ২০২৩ গবেষণা), ১৯৯০ এর দশকের শেষে ছিল ২৫ km/h ([TBS](https://www.tbsnews.net/features/panorama/beyond-flyovers-and-expressways-what-can-solve-dhakas-traffic-crisis-1074471)) | F\_traffic সর্বোচ্চ ≈ ৫ (২৫ ÷ ৪.৮) | মূল রাস্তা, বিশেষ করে মোড়ের কাছে |
| সময় ও দিন | রাত ১০টা থেকে ভোর ৫টা traffic কম, শুক্র-শনি weekday এর চেয়ে কম ([arXiv](https://arxiv.org/pdf/2308.08501)) | রাতে ১.১; শুক্র-শনি তে বাড়তি jam অর্ধেক: 1 + (F − 1) × 0.5 | সব edge |
| বৃষ্টি ও জলাবদ্ধতা | ১৪১টা hotspot (উত্তরে ১০৮, দক্ষিণে ৩৩) ([FE](https://thefinancialexpress.com.bd/national/projects-roll-on-billions-are-spent-on-drains-and-canals-but-dhakas-rainwater-still-struggles-to-escape)); দক্ষিণের pump ২৫–৩০ mm দ্রুত সরাতে পারে ([Prothom Alo](https://en.prothomalo.com/amp/story/bangladesh/city/usi0knq887)); উত্তরের drain ৬০ mm এর জন্য বানানো, ৩ ঘণ্টার বেশি পানি থাকলে জলাবদ্ধতা ধরা হয় ([TBS](https://www.tbsnews.net/node/253957)) | hotspot এ: ২৫ mm এর কম → ১.৩; ২৫–৬০ mm → ৩; ৬০ mm এর বেশি → ∞, বৃষ্টি থামার পর ৩ ঘণ্টা পর্যন্ত | hotspot এর edge (যেমন New Market, Green Road, Shantinagar, West Malibagh, Kazipara) |
| মিছিল ও অবরোধ | বারবার বন্ধ হয় Shahbagh, Press Club–Paltan, Science Lab, Farmgate–Karwan Bazar, Mohakhali, Manik Mia Avenue ([ANN](https://asianews.network/?p=249281), [DT](https://www.dhakatribune.com/bangladesh/415141/student-protests-leave-dhaka-in-traffic-gridlock), [Ittefaq](https://en.ittefaq.com.bd/14056/road-blockades-cause-severe-traffic-congestion-in)) | চলাকালে ∞; আশেপাশের edge এ ×২ | ঘটনার মোড় ও আশেপাশে |
| রাস্তা খোঁড়াখুঁড়ি | WASA ৫০০ km এর বেশি রাস্তা খুঁড়ছে, প্রায় ২৩টা সংস্থা রাস্তায় কাজ করে ([Observer](https://observerbd.com/news/581142)); এক lane কমলে জ্যাম কয়েক গুণ বাড়ে ([FE](https://thefinancialexpress.com.bd/national/paltan-ramna-traffic-grinds-to-halt-over-road-digging)) | এক lane বন্ধ হলে F\_work = ২ | চলমান কাজের edge |
| ছিনতাই | পুলিশের তালিকায় ৩৪২টা hotspot ([DT](https://www.dhakatribune.com/bangladesh/418118/muggings-surge-across-dhaka-as-residents-live-in)); ভোররাতে Sadarghat, Gabtoli, Gulistan, Sayedabad, Mohakhali, Kamalapur বেশি ঝুঁকিপূর্ণ ([DT](https://www.dhakatribune.com/bangladesh/crime/418704/dhaka%E2%80%99s-pre-dawn-streets-become-hotspots-for)) | R\_crime: দিনে ১, রাতে ৩, ভোররাতে ৫ | hotspot এর edge |
| দুর্ঘটনা | ২০২৫ এ ঢাকায় ৪০৯টা দুর্ঘটনায় ২১৯ জন মৃত; Jatrabari, Demra, Mohammadpur, Kuril Bishwaroad, Airport Road এ বেশি; রাতে truck চলায় রাতের ঝুঁকি বেড়েছে ([Prothom Alo](https://en.prothomalo.com/bangladesh/accident/yv5tz64e2x)) | R\_accident: দিনে ১, রাতে ২ | ওই এলাকার edge |
| চাঁদাবাজি | Gulistan, Sayedabad, Mirpur, Mohakhali, Fulbaria terminal কেন্দ্রিক অভিযোগ ([Prothom Alo](https://en.prothomalo.com/bangladesh/Tk-16.5m-extorted-from-Dhaka-s-transport-sector)) | শুধু bus/truck এর জন্য: terminal এর edge এ ×১.৫ | terminal এর আশেপাশের edge |

### Ambulance এর বিশেষ নিয়ম

Ambulance চালকরা জ্যামে উল্টো lane ব্যবহার করে, কিন্তু দুই lane ই আটকে গেলে অপেক্ষা ছাড়া উপায় থাকে না ([TBS](https://www.tbsnews.net/bangladesh/stuck-between-life-and-traffic-407746))। তাই ambulance এর সুবিধা শুধু মাঝারি জ্যামে দেওয়া হবে:

```latex
F_{amb} = \begin{cases} F_{traffic} & \text{if } F_{traffic} \ge 4 \text{ (gridlock)} \\ \max(1, F_{traffic} / 2) & \text{otherwise} \end{cases}
```

Factor কখনো ১ এর নিচে নামে না, তাই A\* এর heuristic admissible থাকে। আগস্ট ২০২৬ এ Dhaka–Chattogram highway তে মেরামতের জ্যামে প্রায় চার ঘণ্টা আটকে ambulance এ এক রোগী মারা যান ([Prothom Alo](https://en.prothomalo.com/bangladesh/local-news/up21ucr8pu))। তাই ambulance profile এ খোঁড়াখুঁড়ির edge এর penalty বেশি রাখা উচিত।

### নতুন cost formula

```latex
\begin{aligned}
\text{cost}(u,v,t) &= T(u,v,t) \times \big(1 + \beta \, U(u,v)\big) + \lambda \times \big(R_{crime}(t) + R_{accident}(t)\big) \times \frac{L(u,v)}{L_{ref}} \\
T(u,v,t) &= \frac{L(u,v)}{v_{free}(u,v)} \times F_{traffic}(t, day) \times F_{rain} \times F_{work}
\end{aligned}
```

অবরোধ চললে বা বৃষ্টির band গাড়ির সীমা ছাড়ালে cost = ∞।

Risk কে L / L\_ref দিয়ে গুণ করা হয়েছে, কারণ OSM একটা hotspot এলাকাকে অনেক ছোট ছোট edge এ ভাগ করে। প্রতি edge এ একবার করে risk যোগ করলে penalty নির্ভর করত edge কয়টা তার উপর, আসল ঝুঁকিপূর্ণ দূরত্বের উপর না। L\_ref = ৫০০ m, মানে মোটামুটি একটা hotspot (radius ২৫০–৩০০ m) একবার পার হওয়ার দূরত্ব। U হলো edge এর অনিশ্চয়তা: অবরোধ-প্রবণ মোড়ের edge এ ১, বর্ষাকালে জলাবদ্ধতা hotspot এ ০.৫, বাকি সব ০। v\_free আসবে OSM এর road type থেকে (যেমন primary ৩০ km/h, residential ১৫ km/h), এটাও অনুমান।

### Website এ weight গুলো কীভাবে dynamic থাকবে

- **সময় ও দিনের slider** → সব edge এর F\_traffic বদলায়
- **বৃষ্টির mm slider** → hotspot edge এর F\_rain বদলায়
- **Map এ মোড়ে click** → অবরোধ on/off, ওই edge গুলো ∞
- **যাত্রী dropdown** → λ আর ambulance নিয়ম বদলায়
- **প্রতিটা পরিবর্তনের পর** সব edge এর cost নতুন করে হিসাব, তারপর বাছাই করা algorithm আবার চালানো আর explored node animate করা

Road graph আসবে OSMnx থেকে, আর hotspot গুলো উপরের source থেকে হাতে geocode করে JSON এ রাখা যায়। Calibration এর জন্য কয়েকটা route এ model এর সময় Google Maps এর সাথে মিলিয়ে দেখো; ঢাকার এক বছরের traffic pattern এভাবে Google Maps data দিয়েই বের করা হয়েছে ([TTJ 2024](https://reference-global.com/article/10.2478/ttj-2024-0030))।

## ৩. যাত্রী অনুযায়ী priority আলাদা

সবার জন্য "ভালো রাস্তা" একই রকম না। λ (safety weight), β (reliability weight) আর edge বাদ দেওয়ার নিয়ম দিয়ে এটা নিয়ন্ত্রণ করা হবে।

| যাত্রী | সবচেয়ে গুরুত্বপূর্ণ | λ (মিনিট প্রতি risk unit) | β | বিশেষ নিয়ম |
| --- | --- | --- | --- | --- |
| Ambulance | সময় | 0.5 | 0.5 | F\_amb নিয়ম (২ক অংশ); F\_rain ৩ বা বেশি এমন edge বাদ; খোঁড়াখুঁড়ির edge এ অতিরিক্ত ×১.৫ |
| জরুরি meeting | সময় + নির্ভরযোগ্যতা | 1 | 1.0 | অনিশ্চিত edge এ বেশি penalty |
| রাতে একা যাত্রী | নিরাপত্তা | 5 | 0.3 | ছিনতাই hotspot এড়ায় |
| সাধারণ যাত্রী | সময় | 1 | 0.3 | কোনো বিশেষ নিয়ম নেই |
| Bus/truck | সময় | 1 | 0.3 | terminal এর edge এ ×১.৫ |

λ এর unit মিনিট প্রতি risk unit, তাই λ × R সরাসরি সময়ের সাথে যোগ হয়। যেমন রাতে একা যাত্রী ভোররাতের ছিনতাই hotspot (R\_crime = ৫) এর ভেতর দিয়ে ৫০০ m গেলে ৫ × ৫ × (৫০০ ÷ ৫০০) = ২৫ মিনিটের সমান penalty পায়।

β নির্ভরযোগ্যতা নিয়ন্ত্রণ করে: U = ১ এমন edge এ meeting যাত্রীর সময় দ্বিগুণ ধরা হয়। সব সংখ্যা শুরুর অনুমান, `weights.yaml` থেকে বদলানো যাবে।

## ৪. কোন algorithm এখানে কেমন কাজ করবে

এই problem এর জন্য A\* সবচেয়ে উপযুক্ত, কারণ এটা আসল cost আর goal এর দূরত্ব দুটোই দেখে।

| Algorithm | কী দেখে সিদ্ধান্ত নেয় | Optimal? | এই problem এ আচরণ |
| --- | --- | --- | --- |
| BFS | কয়টা মোড় পার হলো | না (cost অসমান হলে) | কম মোড়ের রাস্তা দেয়, jam পুরোপুরি ignore করে |
| DFS | প্রথম যে পথ পায় | না | অনেক ঘুরপথ দিতে পারে, তুলনার baseline হিসেবে ভালো |
| IDS | BFS এর মতই, কিন্তু কম memory | না (weighted graph এ) | memory তুলনা দেখানোর জন্য |
| UCS | এ পর্যন্ত মোট cost, g(n) | হ্যাঁ | সঠিক উত্তর দেয়, কিন্তু অনেক node ঘাঁটে |
| Bidirectional | দুই দিক থেকে একসাথে খোঁজে | সঠিকভাবে বানালে হ্যাঁ | node expansion অনেক কমে |
| Greedy | শুধু goal কত কাছে, h(n) | না | দ্রুত, কিন্তু সোজা jam এর দিকে চলে যেতে পারে |
| A\* | g(n) + h(n) | হ্যাঁ (admissible h হলে) | সবচেয়ে উপযুক্ত |

### Greedy এর দুর্বলতা: একটা উদাহরণ

Mirpur থেকে Motijheel যেতে Farmgate হয়ে যাওয়াটা মানচিত্রে সোজা আর কাছে মনে হয়। তাই Greedy সেদিকেই যাবে, অফিস ছুটির সময় সেখানে যত jam ই থাকুক।

A\* আসল cost হিসাব করে, তাই প্রয়োজনে অন্য পথ বেছে নেবে।

## ৫. A\* এর heuristic (viva তে অবশ্যই জিজ্ঞেস করবে)

```latex
h(n) = \frac{\text{straight-line (haversine) distance}(n, goal)}{v_{max}}
```

**কেন admissible:** সরলরেখার চেয়ে ছোট কোনো রাস্তা হয় না, আর কোনো গাড়ি v\_max এর চেয়ে দ্রুত চলতে পারে না। তাই h কখনো আসল সময়ের চেয়ে বেশি estimate করে না।

**কেন consistent:** সরলরেখা দূরত্ব triangle inequality মানে।

### তিনটা ভুল সাবধানে এড়াতে হবে

1. **Unit মেলানো:** h আর cost এর unit একই হতে হবে। cost যদি মিনিটে হয়, h কেও মিনিটে আনতে হবে, শুধু কিলোমিটার দিলে চলবে না।
2. **সব factor ≥ 1 রাখা:** কোনো factor ১ এর কম হলে heuristic এ সেই দ্রুততম speed ধরতে হবে। নইলে admissibility ভেঙে যাবে আর A\* এর উত্তর optimal নাও হতে পারে। এজন্যই ambulance এর factor ১ এর নিচে নামানো হয়নি (২ক অংশ)।
3. **v\_max = graph এর সবচেয়ে দ্রুত রাস্তার speed:** Real map এ Elevated Expressway এর মত দ্রুত রাস্তা থাকবে। v\_max সাধারণ রাস্তার speed ধরলে expressway দিয়ে আসল সময় h এর চেয়ে কম হতে পারে, তখন A\* optimal থাকে না। তাই v\_max = পুরো graph এর সর্বোচ্চ v\_free।

## ৬. Experiment কীভাবে সাজাবে

চারটা scenario তে একই source আর destination নিয়ে সব algorithm চালাতে হবে। Demo র জন্য এক জোড়া route যথেষ্ট, কিন্তু report এর তুলনা টেবিলের জন্য পাঁচটা নির্দিষ্ট route আর fixed seed এর random node pair নিয়ে প্রতিটা যাত্রী profile এ চালাও (বিস্তারিত [`PROBLEM_STATEMENT.md`](PROBLEM_STATEMENT.md) এর ৯ নম্বর অংশে)।

| Scenario | কী বদলায় |
| --- | --- |
| স্বাভাবিক দুপুর | traffic factor ৩ (১০:০০–১৬:০০), বৃষ্টি বা অবরোধ নেই |
| Peak hour | ১৬:০০–২১:০০, main road এ traffic factor ৫ |
| ভারী বৃষ্টি | যেমন ৭০ mm: hotspot এর edge বন্ধ (∞) |
| মিছিল | যেমন Shahbag বা Paltan এর edge বন্ধ |

প্রতিটা scenario এর জন্য এই টেবিলটা পূরণ করো:

| Algorithm | Path | Cost (মিনিট সমতুল্য) | Cost ÷ UCS cost | Nodes expanded | Runtime (ms) | Max frontier size |
| --- | --- | --- | --- | --- | --- | --- |
| BFS |  |  |  |  |  |  |
| DFS |  |  |  |  |  |  |
| IDS |  |  |  |  |  |  |
| UCS |  |  | 1.00 |  |  |  |
| Bidirectional |  |  |  |  |  |  |
| Greedy |  |  |  |  |  |  |
| A\* |  |  |  |  |  |  |

"Cost ÷ UCS cost" হলো suboptimality ratio: ১.০০ মানে optimal, ১.৩০ মানে ৩০% খারাপ।

### যে observation গুলো আশা করা যায়

- BFS আর DFS শুধু ∞ হওয়া edge (অবরোধ, ডুবে যাওয়া রাস্তা) এড়ায়; jam বাড়লে বা কমলে তাদের path বদলায় না, কারণ তারা cost দেখেই না।
- UCS আর A\* পরিস্থিতি অনুযায়ী path বদলায়।
- UCS আর A\* একই cost এর path দেয়, কিন্তু A\* অনেক কম node ঘেঁটে সেখানে পৌঁছায়। এটাই heuristic এর আসল সুবিধা।

## ৭. বাড়তি নম্বরের জন্য extension

- **Dynamic replanning:** যাত্রাপথে হঠাৎ নতুন মিছিল শুরু হলে বর্তমান অবস্থান থেকে আবার A\* চালানো যায়। আরও উন্নত পদ্ধতি হলো D\* Lite। এটা এখন website এর মূল feature, বিস্তারিত [`SPEC.md`](SPEC.md) এর ১০ নম্বর অংশে।
- **Time-dependent cost:** ৫:৩০ এ রওনা দিলে যে রাস্তায় ৬টায় ঢুকবে, সেখানে ৬টার jam ধরতে হবে। এজন্য state এ location এর সাথে সময়ও রাখতে হবে।

## Sources

- [Beyond flyovers and expressways: What can solve Dhaka's traffic crisis?](https://www.tbsnews.net/features/panorama/beyond-flyovers-and-expressways-what-can-solve-dhakas-traffic-crisis-1074471) — The Business Standard
- [Understanding Dhaka City Traffic Intensity and Traffic Expansion Using Gravity Model](https://arxiv.org/pdf/2308.08501) — arXiv
- [Inferring Traffic Patterns of Dhaka City: A Spatio-Temporal Analysis Over a Year](https://reference-global.com/article/10.2478/ttj-2024-0030) — Transport and Telecommunication Journal, Nov 2024
- [Billions are spent on drains and canals but Dhaka's rainwater still struggles to escape](https://thefinancialexpress.com.bd/national/projects-roll-on-billions-are-spent-on-drains-and-canals-but-dhakas-rainwater-still-struggles-to-escape) — The Financial Express
- [Govt takes various steps to ease Dhaka waterlogging](https://www.bssnews.net/js-session/401176/news) — BSS, 30 June 2026
- [Waterlogging persists in parts of Dhaka even after 33 hours](https://en.prothomalo.com/amp/story/bangladesh/city/usi0knq887) — Prothom Alo, July 2026
- [Dhaka city faces waterlogging, traffic tangles after rain](https://www.tbsnews.net/node/253957) — The Business Standard
- [Protests bring key Dhaka roads to a standstill](https://asianews.network/?p=249281) — Asia News Network, 5 January 2026
- [Student protests leave Dhaka in traffic gridlock](https://www.dhakatribune.com/bangladesh/415141/student-protests-leave-dhaka-in-traffic-gridlock) — Dhaka Tribune, 14 July 2026
- [Road blockades cause severe traffic congestion in Dhaka](https://en.ittefaq.com.bd/14056/road-blockades-cause-severe-traffic-congestion-in) — The Daily Ittefaq, 2 November 2025
- [WASA's road digging plan to mount residents' sufferings, worsen Dhaka traffic](https://observerbd.com/news/581142) — The Daily Observer, 28 June 2026
- [Paltan–Ramna traffic grinds to halt over road excavation](https://thefinancialexpress.com.bd/national/paltan-ramna-traffic-grinds-to-halt-over-road-digging) — The Financial Express
- [Muggings surge across Dhaka as residents live in fear](https://www.dhakatribune.com/bangladesh/418118/muggings-surge-across-dhaka-as-residents-live-in) — Dhaka Tribune
- [Dhaka's pre-dawn streets become hotspots for mugging](https://www.dhakatribune.com/bangladesh/crime/418704/dhaka%E2%80%99s-pre-dawn-streets-become-hotspots-for) — Dhaka Tribune
- [Road Safety Foundation report: More accident casualties at night](https://en.prothomalo.com/bangladesh/accident/yv5tz64e2x) — Prothom Alo
- [Tk 16.5m extorted from Dhaka's transport sector every day](https://en.prothomalo.com/bangladesh/Tk-16.5m-extorted-from-Dhaka-s-transport-sector) — Prothom Alo
- [Stuck between life and traffic](https://www.tbsnews.net/bangladesh/stuck-between-life-and-traffic-407746) — The Business Standard
- [Traffic jam stretches 40km on Dhaka–Chattogram highway, patient dies in ambulance](https://en.prothomalo.com/bangladesh/local-news/up21ucr8pu) — Prothom Alo, August 2026
