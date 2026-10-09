# UTM Links — Foundations Tree Experts

Destination: https://www.foundationstreeexperts.com/

## The one to use (dynamic — covers all 12 storm creatives)

Don't hand-build twelve links. Put the clean URL in **Website URL** and this string in the
**URL parameters** field just below it. Meta fills `{{ad.name}}` per ad automatically.

**Website URL**
```
https://www.foundationstreeexperts.com/
```

**URL parameters**
```
utm_source=facebook&utm_medium=paid_social&utm_campaign=storm_response_2026_09&utm_content={{ad.name}}&utm_term={{placement}}
```

Two rules so this stays clean:
- **Don't put UTMs in both fields.** Base URL up top, parameters below, never both — you'll
  get a doubled query string.
- **Name the ads the way the files are named** (`V01-tree-down`, `V11-tree-on-car`). Whatever
  you type as the ad name lands in `utm_content`, so spaces and punctuation become `%20` junk
  in GA4.

## Static version (one specific ad)

If you'd rather paste a full link per ad:

```
https://www.foundationstreeexperts.com/?utm_source=facebook&utm_medium=paid_social&utm_campaign=storm_response_2026_09&utm_content=v01_tree_down
```

Swap `utm_content` per creative: `v01_tree_down`, `v02_emergency_removal`, `v03_247_service`,
`v04_tree_down`, `v05_tree_on_house`, `v06_storm_damage`, `v07_limb_on_roof`,
`v08_blocked_driveway`, `v09_crew_tonight`, `v10_tree_emergency`, `v11_tree_on_car`,
`v12_tree_on_car_alt`.

## Other campaigns

Same pattern, change `utm_campaign` only:

| Campaign | utm_campaign |
|---|---|
| Storm Response (now) | `storm_response_2026_09` |
| 24/7 Emergency (always-on) | `emergency_always_on` |
| Lead Gen | `lead_gen_ann_arbor` |
| Retargeting | `retargeting` |

## Why `utm_source=facebook` is hardcoded

Meta offers `{{site_source_name}}`, which returns `fb` / `ig` / `an`. It splits Facebook from
Instagram, but GA4's default Paid Social channel grouping keys off `facebook`, and `fb` can
fall through into Unassigned. Keeping the source static and putting `{{placement}}` in
`utm_term` gets the platform split without breaking the channel report.

## One caveat for the storm ads

These run with a **Call Now** button. Most of the value is phone calls, which no UTM can see —
they never touch the website. Treat GA4 traffic from this campaign as the minority path and
judge the campaign on call volume. If you want the calls attributed, that has to come from
call tracking on the number itself, not from UTMs.
