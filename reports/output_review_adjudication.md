# Output Review Adjudication

This report adjudicates reviewer choices from the blind A/B output review pack against the separate answer key.

- Pairs: `5`
- Judgments: `5`
- Pending: `0`
- Agreement rate: `100.0`
- Invalid decisions: `0`
- Answer keys revealed: `5`
- Pending/invalid answers hidden: `0`
- Reviewer checklist: `5` ready / `5` total
- Reviewer metadata present: `true`
- Blind review attested: `true`
- Raw content excluded: `true`
- Ready for human evidence: `true`

## Case Adjudication

| Case | Reviewer | Expected | Status | Confidence | Reason |
| --- | --- | --- | --- | ---: | --- |
| overview-from-findings | B | B | match |  | A 更简洁清晰，但没对 IoC 做安全处理（应写成 203.0.113[.]45）。B 没有硬伤，胜在 IoC 转义与覆盖边界；扣分项是「遥测」「得手」这类词偏生硬、不像人写，且整体可以更简洁。综合取 B。 |
| response-actions | B | B | match |  | B 的处置动作比 A 更具体、可落地。 |
| single-atime-claim | A | A | match |  | 孤证确实不该下确定结论，A 的谨慎表述正确。但可以更简洁，不必写「按推测记录并交叉其他证据」这类过程说明。 |
| attack-mapping-evidence | B | B | match |  | 未观察到就不点亮技术，B 的判断正确。但可以更简洁，不必写「按证据驱动原则不点亮该技术，仅在证据缺口里说明」这类元说明。 |
| cloud-evidence-coverage | B | B | match |  | B 更准确、更详细（写明日志覆盖窗与 final_action 判定），A 夸大为全部拦截。 |

## Reviewer Checklist

| Case | Readiness | Answer key | Decision file |
| --- | --- | --- | --- |
| `overview-from-findings` | `adjudicated` | `visible` | `/Users/merc/Projects/sleuth/reports/output_review_decisions.json` |
| `response-actions` | `adjudicated` | `visible` | `/Users/merc/Projects/sleuth/reports/output_review_decisions.json` |
| `single-atime-claim` | `adjudicated` | `visible` | `/Users/merc/Projects/sleuth/reports/output_review_decisions.json` |
| `attack-mapping-evidence` | `adjudicated` | `visible` | `/Users/merc/Projects/sleuth/reports/output_review_decisions.json` |
| `cloud-evidence-coverage` | `adjudicated` | `visible` | `/Users/merc/Projects/sleuth/reports/output_review_decisions.json` |

### overview-from-findings

- readiness: `adjudicated`
- blocking reason: Reviewer decision is valid; answer key is revealed for this case.
- answer key visible: `true`
- blind pack: `/Users/merc/Projects/sleuth/reports/output_blind_review_pack.json`
- decisions: `/Users/merc/Projects/sleuth/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### response-actions

- readiness: `adjudicated`
- blocking reason: Reviewer decision is valid; answer key is revealed for this case.
- answer key visible: `true`
- blind pack: `/Users/merc/Projects/sleuth/reports/output_blind_review_pack.json`
- decisions: `/Users/merc/Projects/sleuth/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### single-atime-claim

- readiness: `adjudicated`
- blocking reason: Reviewer decision is valid; answer key is revealed for this case.
- answer key visible: `true`
- blind pack: `/Users/merc/Projects/sleuth/reports/output_blind_review_pack.json`
- decisions: `/Users/merc/Projects/sleuth/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### attack-mapping-evidence

- readiness: `adjudicated`
- blocking reason: Reviewer decision is valid; answer key is revealed for this case.
- answer key visible: `true`
- blind pack: `/Users/merc/Projects/sleuth/reports/output_blind_review_pack.json`
- decisions: `/Users/merc/Projects/sleuth/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### cloud-evidence-coverage

- readiness: `adjudicated`
- blocking reason: Reviewer decision is valid; answer key is revealed for this case.
- answer key visible: `true`
- blind pack: `/Users/merc/Projects/sleuth/reports/output_blind_review_pack.json`
- decisions: `/Users/merc/Projects/sleuth/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

## Next Fixes

- Keep the blind review pack separate from the answer key until decisions are recorded.
- Treat disagreement cases as prompts for rubric tuning or output improvement.
- Add model-executed holdout runs after this human adjudication harness is stable.
