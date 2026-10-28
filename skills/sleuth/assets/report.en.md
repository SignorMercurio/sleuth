---
date: 00000000
sir-seq: NN
version: X.Y
client: Client Name
---

<!-- Writing guide: write for the client's business owners and technical staff. State who did what and what it caused first, then explain only the technical detail the reader needs. Use plain words in the overview; put technical names, ATT&CK IDs, commands, and log excerpts in Technical Analysis. Explain a term briefly the first time it affects understanding, and do not explain it again. Name the specific object instead of vague words such as "related resources" or "sensitive data". Each section has its own comment with local requirements. Replace or delete every placeholder and example; none of them are incident facts. -->

<!-- Evidence wording: write "not observed" only after you checked the relevant evidence, and state the time window and scope. Write "cannot be confirmed" when logs are missing, not covered, or not sufficient. Write "ruled out" only when the evidence is sufficient to reject a specific hypothesis. Keep attempted actions, verified capability, and actual consequences apart, and do not treat a model's statement as an execution result. Do not guess unknown counts, times, or states. -->

<!-- Division of content: the conclusion gives the summary, Impact Assessment lists objects and scale, Technical Analysis explains evidence and causality, Response Actions records the specific actions, and the summary closes only the remaining issues and next steps. Repeat a short summary when necessary, but give evidence detail, counts, and the full attack chain only once. Before the final version, delete paragraphs that add no information, and check that every conclusion has support and every completion state is confirmed. -->

<!-- Replace the frontmatter with real values: date is an 8-digit date (for example 20250507), sir-seq is a two-digit sequence (use 01 for the first delivery when no sequence exists), and version is the version number (for example 1.0). -->

::: cover-hero
sev :: Severity · [ High / Medium / Low ]
title :: Security Incident\nResponse Report
:::

::: cover-meta
| k | v | sub |
| Service ID | SIR-{date} | {sir-seq} · Initial delivery |
| Issue Date | {date:slash-pad} | Version {version} |
| Lead | Ling Xing | Alibaba Cloud · Incident Response Engineer |
| Engagement | Remote response | Off-site delivery |
:::

<!-- rev: keep each "Description" entry under 12 words. Before final delivery, increase the minor version for each iteration (1.0→1.1→1.2…); do not go to 2.x. Keep the major version for significant revisions after the client received the formal version. The version must match the frontmatter `version` and cover-meta. -->

::: rev
| Date | Version | Description | Author |
| {date:slash} | 1.0 | Created: findings of the first response window. | Ling Xing |
| — | — | Pending client review and confirmation. | — |
:::

<!-- This chapter answers: which objects were investigated, how the incident was found, and what the final conclusion and current state are. Management must be able to read the core content in one minute. Mention technical evidence only briefly here; leave the detailed reasoning to Technical Analysis. -->

## Event Overview

### Incident Conclusion

<!-- After you write this section, check each item: the incident type, scope of impact, response status, and residual risk must each have evidence or an explanation later in the report. In the callout, give the incident and whether it is contained in one sentence. Add body only when that sentence needs a qualification; otherwise delete the field. The four fields below each give a short summary, without technical evidence or impact detail. Keep headline under 40 words and each field under 50 words; move extra content to the related chapter. -->

::: callout
label :: Headline · Key Finding
headline :: [ One sentence: nature of the incident + current response status, not the investigation process ]
body :: [ Only a qualification the headline cannot do without; delete this line when there is none ]
:::

Nature of Incident :: [ In plain words, the confirmed abnormal behavior and the nature of the incident ]
Scope of Impact :: [ One sentence on the confirmed impact and the key unknown limits; scale and detail go in Impact Assessment ]
Response Status :: [ Key actions that are complete / in progress / not started ]
Residual Risk :: [ 1-3 risks the client must still handle + the time window or condition (such as "until the fix is deployed"); do not invent a date when no deadline is known ]

### Assets in Scope

<!-- Each asset block is one investigated object. Use the first block for a host, instance, or container, and the second block for an identity such as an AccessKey, RAM user, or login account. For more hosts, copy the first block; do not use the identity block for a host. Fill only the identifier itself, without notes in parentheses after each value (put region, subnet, alias, and purpose together in "Role"). Delete the instance ID by default; keep it only when the client needs it to locate the instance for a response action. Put a name or alias the client recognizes in "Instance Name", and do not mix the two. Delete fields that do not apply or that the findings do not record; do not guess and do not leave empty fields. Delete the whole identity block when there is no identity. -->

::: asset
Public IP :: [ Public IP, masked as required ]
Private IP :: [ Private IP, optional ]
Instance ID :: [ Real resource ID of the ECS instance / container / database; delete when not necessary ]
Instance Name :: [ Asset name or business name ]
Role :: [ Business role, external entry point, exposed ports, reason for investigation ]
:::

::: asset
Identity :: [ AccessKey ID / RAM user / login account ]
Owner :: [ Client / business system / automated task / third-party service ]
Permissions :: [ Permissions at the time of the incident, IP allowlist, whether too broad, and the relation to the abnormal behavior ]
:::

### Discovery & Timeline

<!-- Keep 4-6 decisive points in the timeline, and only points inside the incident window. A point with ! is highlighted; mark only the points that affect the conclusion. Do not record a log of the investigation. Each point is one complete sentence by default: who did what through which channel, and with what result. Add a second sentence only when the cause or uncertainty cannot be stated otherwise. Do not put alert IDs, rule numbers, or HTTP status codes here; put them in Investigation Process or Coverage Notes. Give time offsets to the minute (for example "T + 2 min"), not to the second; across days write "T + 39 d 9 h". State the time zone once in a sentence before the timeline; do not add "CST" to each point or in the body, and write dates in the body the same way as in the timeline. -->

::: timeline
- T − [offset] · [YYYY/MM/DD HH:mm or time range] :: [Precursor signal]
  Earliest anomaly + log source; delete this point when there is no precursor.
- T0 · [YYYY/MM/DD HH:mm] :: [First confirmed key event] !
  The core alert or evidence that started the response.
- T + [duration] · [HH:mm] :: [Incident response started] !
  Response start and the key evidence collection actions.
- T + [duration] · [YYYY/MM/DD HH:mm] :: [Containment and root cause confirmed]
  Containment status, whether the root cause is confirmed, and evidence gaps.
:::

### Impact Assessment

<!-- Keep this section on its own. It answers which objects had what actual impact, at what scale, and which limits cannot be confirmed. For a simple incident, use one short paragraph and delete the table below. For a complex incident, use the table and add or remove rows for the actual impact; do not keep unrelated placeholders. Keep available permission, attempted operation, read, modified, exported, and confirmed exfiltration apart. Do not conclude actual damage or full data loss from permissions, file names, file sizes, or a model's statement alone. State how each figure was counted and the evidence source, in words the client understands (such as "two hosts in total"); do not describe the counting process. Write "cannot be confirmed" for an unknown count, not 0. Summarize only the impact here; keep technical reasoning and log excerpts in Investigation Process, and do not repeat conclusions or response advice. -->

| Affected Object | Confirmed Impact | Scope & Scale | Evidence & Limits |
| --- | --- | --- | --- |
| [ Asset / account / business / data ] | [ Observed behavior and its actual consequence ] | [ Time window, count, and how it was counted; state unknowns clearly ] | [ Supporting evidence and the impact limits not yet confirmed ] |

## Technical Analysis

<!-- This chapter answers: how the chain of evidence holds. Write in the order of lead, verification, confirmation, and exclusion. Each paragraph carries one core judgment; a complex incident can add meaningful subsections. -->

### Investigation Process

<!-- Organize paragraphs as "initial lead, key verification, confirmed behavior, exclusions or evidence gaps that affect the conclusion". Select by the actual material; do not apply the labels to every item. Usually use 3-5 evidence units; a complex incident can add subsections by confirmed stage. Each paragraph states one judgment, its strongest evidence, and what it means, and keeps time, actor, resource, command, or log source as needed. Leave out command-by-command logs, full logs, and routine negative results that do not affect the conclusion. Put coverage limits in a blockquote, apart from the evidence narrative. -->

<!-- Wording example (fictional, shows style only, do not reuse as fact): The logs show that the abnormal account read files in object storage. Because part of the download logs is missing, the full read scope cannot be confirmed. -->

<!-- When the findings record a console screenshot as evidence (such as a confirmed vulnerability or exposed credential), add an image reference `![](<report name>.assets/...){caption="Figure N | Subject (source/object)"}` after the paragraph it supports, and copy the path exactly. When there is no screenshot, add no image. The caption is one sentence about what the image shows; keep time, hashes, reasoning, and qualifications in the body. Put the image directly after the paragraph it supports; for several images in sequence, add a caption only to the last one. AI must not invent image content or create HTML/CSS/resource directories. -->

[ In paragraphs, state the key findings, supporting evidence, and security meaning; add or remove paragraphs to match the actual evidence. ]

### Sample Analysis

<!-- Always keep this section. When there is no sample, state in one natural sentence that none was found in the checked scope, that it could not be obtained, or that it was out of scope; do not expand the investigation process. -->

<!-- When there is a sample, write only the path, hash, type, behavior, outbound connections, or configuration that relate to the conclusion and response, and its relation to the incident. Give family background only when it affects the response. -->

[ With a sample, summarize its behavior and key identifiers; without one, give the reason based on the actual investigation scope. ]

### Intrusion Path

<!-- Prefer one attack chain diagram for the intrusion path (`![](…){caption="…"}`: when a diagram exists, reference `<report name>.assets/attack-chain.png`; a console screenshot does not replace the diagram), with one paragraph of text. Use a plain-text arrow chain only when there is no diagram, and do not write long sentences full of `[speculative]` tags. When the full path cannot be reconstructed, write only the confirmed chain, then one sentence on where it breaks. Do not repeat the reason and the data needed when Investigation Process already gives them, and do not draw a complete attack story. -->

<!-- Without a diagram, present the confirmed steps in one paragraph or a short arrow chain. Each step keeps only the behavior and one key object; do not force fixed stages. Do not repeat times, IoCs, commands, and evidence already given in Investigation Process. -->

[ The confirmed intrusion chain; when the chain is incomplete, add one sentence on where it breaks. ]

### ATT&CK Matrix · Techniques Observed {page slot=3.4}

<!-- The matrix has a fixed layout: keep the 12 tactics (in two rows) with 5 techniques each, exactly as given; do not add, remove, or reorder tactics or techniques. By default nothing is marked; add ` !` at the end of the line only for a technique with supporting evidence. Keep the common placeholders of the template in the other positions; do not delete them. Put the evidence limits in "Coverage Notes" below; do not leave tactics out of the matrix. -->

::: attack
- Initial Access
  - Valid Accounts
  - Phishing
  - Exploit Public App
  - External Remote Svc
  - Trusted Relationship
- Execution
  - Cmd Interpreter
  - User Execution
  - Scheduled Task
  - System Services
  - Container Admin
- Persistence
  - Account Manipulation
  - Boot Autostart
  - Web Shell
  - Cron
  - SSH Keys
- Privilege Escalation
  - Priv-Esc Exploit
  - Token Manipulation
  - Process Injection
  - Valid Accounts
  - Elevation Abuse
- Defense Evasion
  - Clear Logs
  - Obfuscated Files
  - Masquerading
  - Impair Defenses
  - Trust Policy Change
- Credential Access
  - Unsecured Creds
  - Brute Force
  - Keylogging
  - Credential Dumping
  - Adversary-in-Middle
- Discovery
  - Cloud Service Disc.
  - Cloud Accounts
  - Network Scanning
  - System Info
  - Process Discovery
- Lateral Movement
  - Remote Services
  - Internal Phishing
  - Tool Transfer
  - Alt Auth Material
  - Session Hijacking
- Collection
  - Local Data
  - Cloud Storage Data
  - Clipboard Data
  - Screen Capture
  - Audio/Video Capture
- Command & Control
  - App Layer Protocol
  - DNS
  - Web Service
  - Encrypted Channel
  - Non-Standard Port
- Exfiltration
  - Over C2 Channel
  - Alt Protocol
  - Over Web Service
  - Scheduled Transfer
  - Physical Medium
- Impact
  - Data Encrypted
  - Data Destruction
  - Account Removal
  - Denial of Service
  - Resource Hijacking
:::

#### Coverage Notes

<!-- Always keep this section. In one short paragraph, explain which evidence types the matrix uses, and which important stages are limited by logs or scope. Do not copy the evidence for each marked technique from Technical Analysis again. In the body, call them "the techniques marked in the matrix". -->

In one short paragraph, summarize the main evidence sources for the techniques marked in the matrix (log hits / command records / sample behavior / network connections / client confirmation) and why key tactics are not covered (no positive signal observed / logs not available / out of investigation scope). Do not restate Technical Analysis item by item.

## Response Actions

<!-- This chapter answers: what is already blocked, what is being cleaned up, and what the client must still do. Keep all three phases. The number of actions follows the evidence and actual needs; do not pad. Each action names the object and the specific action. Write client-run operations in their actual order, with each precondition before its operation. For an operation that interrupts the business or deletes data or evidence, state the consequence in that item. Add the verification result to a completed action; for open items, add the owner and deadline when known. Set the state from execution records or client confirmation: [x] complete, [/] in progress, [ ] not started. When the state cannot be confirmed, explain it in a plain sentence without a check mark. When a phase has no action, write only one sentence on its state. The placeholders below are plain paragraphs; use the state syntax when you fill in actual actions. -->

<!-- Containment lists only the immediate actions that stop the current risk. -->

::: phase Containment
[ The specific object contained, the action, and the confirmed state or result. ]
:::

<!-- Eradication lists the specific actions that remove the attacker's remaining capability and the root cause, such as cleanup, rebuild, patching, key rotation, or permission removal. -->

::: phase Eradication
[ The specific root cause or remaining item, the action, and the confirmed state or result. ]
:::

<!-- Recovery first states which business or access capability was restored, how it was verified, and what is not restored yet. Long-term hardening goes later in the report; do not repeat it here. -->

::: phase Recovery & Hardening
[ The restored object, the action, the verification result, and the recovery conditions not yet met; when recovery does not apply, say so briefly. ]
:::

## Summary & Advisory

<!-- This chapter only closes the earlier content. Do not add new facts, and do not replay the timeline, IoCs, ATT&CK, or the full attack chain. -->

### Event Summary

<!-- First close the incident in two or three sentences: the root cause, the result, and which key controls worked or failed; do not repeat impact detail or the attack process. Then, in one short paragraph, write the open issues and the next highest-priority work. State the object and action for any necessary long-term hardening. Write next investigation steps (such as checking a type of log) here; the product or service recommendations below cover only enabling and configuring products, and the two do not repeat each other. When nothing is open, say so briefly based on the verification results; do not add advice to fill space. -->

[ Open issues, next priorities, and necessary long-term hardening actions. ]

### Alibaba Cloud Security Recommendations

The recommendations below address the security control gaps this incident exposed, in order of response priority. Confirm the actual scope against existing subscriptions, asset scale, and a technical assessment.

<!-- This section is mandatory. The first item is always Agentic BAS; you can adapt risk and action to the incident. After it, recommend 0 to 2 Alibaba Cloud security products or services that relate directly to the incident risk or evidence gaps, and copy the block below in order of priority. priority is only P1/P2/P3, and type is only product/service. For a product the client already has, recommend better configuration or use first, not a new purchase by default. Do not invent capabilities, subscription states, or enablement results. -->

::: recommendation priority=P1 type=product
name :: Agentic BAS
risk :: There is no objective evidence, from the attacker's point of view, that the response and hardening measures actually work.
reason :: Agentic BAS uses LLM-driven planning, penetration, verification, and reporting agents to reproduce the attack chain, verify that vulnerabilities can be exploited, and produce reproducible request traces and verification reports.
action :: Start a verification task scoped to the exposure and hardening items of this incident, confirm that the fixes and controls work, then add it to periodic retesting.
:::

::: recommendation priority=P1 type=product
name :: [ Product or service name, such as Security Center ]
risk :: [ The risk or control gap that relates directly to this incident ]
reason :: [ Why this product or service closes the gap above ]
action :: [ The specific next step for the client to enable, configure, or evaluate ]
:::

### Further Reading

Framework :: MITRE ATT&CK for Enterprise: supports the technique mapping and tactic classification [https://attack.mitre.org/matrices/enterprise/](https://attack.mitre.org/matrices/enterprise/)
Baseline :: Cloud security best practices: support the identity, network, logging, and exposure hardening advice [https://help.aliyun.com/document_detail/101898.html](https://help.aliyun.com/document_detail/101898.html)
Service :: Alibaba Cloud · Managed Security Service: describes the service context of this report [https://www.aliyun.com/product/sos](https://www.aliyun.com/product/sos)
