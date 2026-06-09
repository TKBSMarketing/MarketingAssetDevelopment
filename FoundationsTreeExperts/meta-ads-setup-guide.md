# Meta Ads Manager — Step-by-Step Setup Guide

For Josh setting up Foundations Tree Experts campaigns.

---

## Prerequisites

- [ ] Access to Meta Business Suite for Foundations Tree Experts
- [ ] Facebook Page: https://www.facebook.com/FoundationsTreeExperts
- [ ] Meta Pixel verified (ID: 1673544533983863) — already on foundationstreeexperts.com
- [ ] Payment method added to Ad Account

---

## Step 1: Verify Pixel Lead Events

Pixel is already installed and tracking leads. Quick sanity check before launching ads:

1. Go to **Events Manager** > select Pixel **1673544533983863**
2. Confirm **Lead** events are showing in the event log
3. Verify the event is marked as a **conversion** (star icon should be filled)
4. If not already marked: click the event > toggle "Use as conversion" ON
5. Meta will use this Lead event to optimize ad delivery — it will show ads to people most likely to convert on the website

---

## Step 2: Create Campaign 1 — Lead Generation

### Campaign Level
1. Go to **Ads Manager** > **Create**
2. Campaign Objective: **Leads**
3. Campaign Name: "FTE - Lead Gen - Ann Arbor Core"
4. Special Ad Categories: **None** (tree service is not housing/credit/employment/politics)
5. Campaign Budget Optimization: **ON**
6. Daily Budget: **$12.00**
7. Bid Strategy: **Lowest cost** (default — don't change at this budget)

### Ad Set Level
1. Ad Set Name: "Ann Arbor - Homeowners 35-65"
2. Conversion Location: **Website**
3. Performance Goal: **Maximize number of conversions**
4. Conversion Event: **Lead** (from your pixel)
4. Audience:
   - **Location:** Ann Arbor, Michigan — **10 mile radius**
   - Location Type: "People living in this location" (NOT "recently in" — you want homeowners, not visitors)
   - **Age:** 35-65
   - **Detailed Targeting:**
     - Demographics > Home > Home Ownership > Homeowners
     - Interests > Home and Garden > Home improvement
     - Interests > Home and Garden > Gardening
     - Interests > Home and Garden > Do It Yourself (DIY)
   - **Exclude:** None for now (audience is already narrow enough)
5. Placements: **Advantage+ Placements** (let Meta optimize — it will find where your creative performs best)
6. Schedule: Run continuously (no end date)

### Ad Level — Create 3-4 Ads

For each ad from Ad Sets A (see ad-copy.md):

1. Ad Name: e.g., "A1 - Weight Off Your Shoulders - Video"
2. Identity: Foundations Tree Experts Facebook Page
3. Ad Setup: **Single image or video**
4. Media: Upload the image/video per the creative direction
5. Primary Text: Copy from ad-copy.md
6. Headline: Copy from ad-copy.md
7. Description: Copy from ad-copy.md
8. CTA Button: **Get Quote**
9. Website URL: `https://foundationstreeexperts.com/?utm_source=facebook&utm_medium=paid&utm_campaign=fte-leadgen&utm_content={{ad.name}}`
10. Display Link: foundationstreeexperts.com

**Repeat for ads A1, A2, A3, A4.**

---

## Step 3: Create Campaign 2 — Retargeting

### Campaign Level
1. Campaign Objective: **Leads**
2. Campaign Name: "FTE - Retargeting"
3. Campaign Budget Optimization: **ON**
4. Daily Budget: **$3.00**

### Custom Audiences (Create These First)

Go to **Audiences** > **Create Audience** > **Custom Audience**:

**Audience 1: Website Visitors**
- Source: Website
- Pixel: Foundations Tree Experts pixel
- Event: All website visitors
- Retention: 60 days
- Name: "FTE - Website Visitors 60d"

**Audience 2: Facebook/IG Engagers**
- Source: Facebook Page
- Event: Everyone who engaged with your Page
- Retention: 90 days
- Name: "FTE - Page Engagers 90d"

**Audience 3: Video Viewers**
- Source: Video
- Event: People who watched at least 25% of any video
- Retention: 60 days
- Name: "FTE - Video Viewers 25% 60d"

### Ad Set Level
1. Ad Set Name: "Retargeting - All Warm"
2. Audience: Use the 3 Custom Audiences above (combine them — Meta will deduplicate)
3. **Exclude:** People who already converted (if you have a thank-you page or conversion event, create a Custom Audience from Website > "People who triggered Contact/Lead event")
4. Location: Ann Arbor, MI — 15 mile radius (slightly wider for retargeting)
5. Age/Gender: Leave broad (these people already engaged)
6. Placements: Advantage+

### Ad Level
- Use retargeting ads R1 and R2 from ad-copy.md
- Website URL: `https://foundationstreeexperts.com/?utm_source=facebook&utm_medium=paid&utm_campaign=fte-retargeting&utm_content={{ad.name}}`
- CTA Button: **Get Quote**

---

## Step 4: Create Campaign 3 — Storm Response (PAUSED)

### Campaign Level
1. Campaign Objective: **Leads**
2. Campaign Name: "FTE - Storm Emergency"
3. Daily Budget: **$25.00** (only when active)
4. **Status: PAUSED** — do not turn on until a storm hits

### Ad Set Level
1. Audience: Ann Arbor — **15 mile radius** (wider during emergencies)
2. Age: 25-65 (broader — storm damage is urgent for everyone)
3. Homeowners targeting only
4. Placements: Advantage+

### Ad Level
- Use ad C1 from ad-copy.md
- CTA Button: **Call Now**
- Website URL: `https://foundationstreeexperts.com/?utm_source=facebook&utm_medium=paid&utm_campaign=fte-storm&utm_content={{ad.name}}`
- The ad copy itself has the phone number prominently — many storm leads will call directly from the ad without clicking through

### When to Activate
- Severe thunderstorm or ice storm warning for Washtenaw County
- Reports of tree damage on local news/social media
- Turn ON immediately, run for 5-7 days, then pause again
- During storm activation: consider pausing Campaign 1 and redirecting that $12/day here too (total $37/day surge)

---

## Step 5: Website Lead Tracking & Follow-Up

### Ensure the Website Captures Leads
Since all ads drive to foundationstreeexperts.com, the website is now the conversion point. Confirm:
1. Phone number **(734) 219-3612** is prominent and clickable on mobile (tap-to-call)
2. Quote request form is easy to find and works on mobile
3. Form submissions send an immediate email notification to David
4. Consider adding a phone call tracking number (CallRail, WhatConverts) to attribute calls specifically from Meta ads

### Connect GA4
1. Ensure Google Analytics (GA4) is installed on the site
2. Set up a **conversion event** for form submissions and phone clicks
3. In GA4 > Admin > Events, mark these as "key events"
4. Use UTM parameters from the ads to see which specific ad drove each visit in GA4 > Acquisition > Traffic Acquisition

---

## Step 6: Post-Launch Checklist

### Day 1
- [ ] Verify all ads are "Active" (not "In Review" or "Rejected")
- [ ] Click through each ad yourself — verify the website loads correctly with UTM params
- [ ] Test the quote form and tap-to-call on mobile
- [ ] Confirm David knows ad-driven leads are coming

### Day 3
- [ ] Check: Are impressions delivering? If 0, check audience size and bid
- [ ] Check: Any ads rejected? Fix creative or copy if flagged
- [ ] Verify Lead pixel events are registering in Events Manager

### Week 1
- [ ] Review CTR by ad — anything under 0.5% needs new creative
- [ ] Check Events Manager — are Lead events firing from ad traffic?
- [ ] If no Lead events yet, don't panic — at $12/day it may take a week or two

### Week 2
- [ ] Still in learning phase — don't make changes yet unless something is broken
- [ ] Ask David: "Have you gotten any calls or form fills mentioning the website or Facebook?"

### Month 1
- [ ] Identify top 1-2 performing ads by CPL and lead volume
- [ ] Pause bottom performer, replace with Ad Set B creative
- [ ] Review CPL — target under $60
- [ ] Calculate actual ROI: leads → estimates → closed jobs → revenue

---

## Naming Conventions

Keep names consistent for easy reporting:

| Level | Format | Example |
|-------|--------|---------|
| Campaign | "FTE - [Purpose]" | FTE - Lead Gen - Ann Arbor Core |
| Ad Set | "[Audience Description]" | Ann Arbor - Homeowners 35-65 |
| Ad | "[ID] - [Name] - [Format]" | A1 - Weight Off Shoulders - Video |

---

## Troubleshooting

**"Ad rejected"** — Tree service ads occasionally get flagged for "safety" language. Soften words like "dangerous," "hazard," "liability." Resubmit.

**Low impressions** — Audience may be too narrow. Remove one interest targeting layer (keep Homeowners, drop DIY).

**High CPL (over $70)** — Creative fatigue or audience saturation. Rotate ads, try a new angle.

**High clicks but no calls/forms** — The website isn't converting. Check: is the phone number visible above the fold on mobile? Is the form too long? Is the page loading slowly? Consider A/B testing the landing page.

**"Learning Limited"** — Budget is too low to generate 50 conversions/week. This is expected at $12/day. Performance will still be decent, just not fully optimized. Don't panic.
