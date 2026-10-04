# content.json — schema (v2)

Lives at `SOURCE/CONFIG/content.json` → `SOURCE/JS/content-data.js` (`window.<G>_CONTENT`). Every module reads it, so the whole
system tells one story. Write it from the company overview; anything invented stays labelled with `_sample: true`.
Example (fictional): `assets/templates/content.example.json`.

| Key | Shape | Notes |
|---|---|---|
| `_sample`, `_note` | bool, string | true while any content is placeholder; modules then show a small "sample content" note |
| `brand` | `{name, legal_name, tagline, descriptor, mission, vision?, story?, values[{name, text, icon}], languages[]}` | |
| `labels` | `{units, offerings, projects, events, posts, people, cta_primary, cta_secondary}` | defaults from the profile ("Services", "Menu", "Courses"…) |
| `contact` | `{email, phone, address, city, country, website, hours?, social{platform: handle}}` | |
| `units[]` | `{key, name, name_local?, summary, icon}` | areas, departments, practices, collections, spaces |
| `offerings[]` | `{key, name, unit, summary, details?, price?, duration?, icon?, cta?}` | services, products, programmes, menu items, courses |
| `projects[]` | `{key, title, unit, year, status?, summary, metrics?[{label, value}]}` | case studies, portfolio, stories |
| `events[]` | `{key, title, date: "YYYY-MM-DD", time, place, unit?, summary?}` | weekdays are computed from the date |
| `posts[]` | `{key, title, date, category, excerpt?, author?}` | news, blog, insights, journal |
| `people[]` | `{name, role, bio?, initials}` | only real people with permission; otherwise clearly fictional |
| `stats[]` | `{label, value, unit, note?}` | value as display string ("12,400") |
| `testimonials[]` | `{quote, name, role}` | sample unless real and approved |
| `faq[]` | `{q, a}` | |
| `partners[]` | `{name}` | categories only unless real and approved |
| `i18n` | `{lang: {key: translated string}}` | optional second-language strings |

Icons referenced by `icon` keys must exist in the icon set (the icons module resolves aliases and always includes them).
