# Company-type profiles

A profile (`assets/profiles/<key>.json`) tells the system what kind of company this is: what to call things, which deliverables
to make, which icon sets, social formats, print and event items, and how the DNA is biased. Pick one in intake; it is copied to
`SOURCE/CONFIG/profile.json`, where you can edit it per brand (add a page, drop merch, rename labels).

| Key | For | Typical fits | Offerings / units label | Display type tags | DNA bias | Deliverables |
|---|---|---|---|---|---|---|
| `education-culture` | Education, culture & events | school, university, course provider, academy, museum, gallery | Courses / Programmes | art, culture, editorial | balanced, upper case, motion 0.6 | 15 pages · 10 print · 8 merch |
| `health-wellness` | Health, care & wellness | clinic, hospital, dental practice, pharmacy, health app, fitness studio | Services / Departments | round, friendly, soft | airy, sentence case, motion 0.3 | 16 pages · 8 print · 5 merch |
| `hospitality-food` | Hospitality, food & drink | restaurant, café, bakery, bar, hotel, guesthouse | Menu / Spaces | warm, serif, elegant | airy, title case, motion 0.35 | 12 pages · 13 print · 6 merch · no charts |
| `industrial-energy` | Industrial, construction, logistics, energy | manufacturing, construction, engineering, logistics, energy, mining | Capabilities / Sectors | industrial, condensed, strong | dense, upper case, motion 0.45 | 15 pages · 8 print · 6 merch |
| `nonprofit-ngo` | Non-profit, NGO, foundation, association | NGO, charity, foundation, association, civic initiative, volunteer network | Programmes / Areas | civic, editorial, condensed | balanced, upper case, motion 0.5 | 17 pages · 9 print · 8 merch |
| `professional-services` | Professional & B2B services | consultancy, law firm, accounting, finance, agency, architecture | Services / Practices | editorial, serif, classic | airy, sentence case, motion 0.35 | 14 pages · 7 print · 5 merch |
| `retail-ecommerce` | Retail, consumer brand, e-commerce | shop, D2C brand, fashion, beauty products, homeware, marketplace | Products / Collections | expressive, bold, playful | dense, upper case, motion 0.8 | 13 pages · 9 print · 6 merch |
| `saas-tech` | Software, apps, platforms, tech | SaaS, mobile app, platform, AI product, developer tool, IT services | Features / Solutions | tech, geometric, modern | balanced, sentence case, motion 0.65 | 17 pages · 5 print · 7 merch |

## Fields
`fits`, `audiences`, `voice` {traits, avoid, cta}, `colour` (strategy notes), `type` {display[], sans[], mono, serif, hand} (font scoring),
`dna_bias` {density, display_case, motion_energy, imagery}, `labels` (offerings, units, projects, events, posts, people, cta_primary, cta_secondary),
`pages`, `icons`, `social`, `post_types`, `presentation`, `print`, `documents`, `events`, `merch`, `environment`, `dataviz`,
`modules` {module: enabled}, `sample` (tagline, mission, values, units, offerings, stats used for sample content).

## Choosing
- Mixed companies: choose by what the identity must sell first (a café that roasts and retails coffee → hospitality-food, then add retail items).
- Personal brands / creators: professional-services (consultants, coaches) or retail-ecommerce (makers), then edit labels.
- Public bodies and associations: nonprofit-ngo. Agencies and studios: professional-services. Real-estate developers: industrial-energy; agents: professional-services.

## Adding a profile
Copy the closest JSON, change `key`, `title`, labels, lists and `type` tags, keep every field. Lists may only use item names the
modules know (see each module's README) — unknown items fall back to generic layouts and are logged.
