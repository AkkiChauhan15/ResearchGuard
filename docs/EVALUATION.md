# Evaluation protocol

The first snapshot contains 16 cases, 10 development and 6 held-out. All invented
studies are explicitly synthetic. One negative case uses an archived real Loos
extract as an irrelevant citation. Reference labels and rationales were authored by
the coding agent from supplied fixture text and **have not been validated by a human
scientific reviewer**. Do not call them independent ground truth.

The fixture run checks IDs, case splits, source links, and missing-access references.
It does not run a model. Current denominators: 16/16 fixture checks, 0/16 model
cases, 0/16 human-reviewed references. No scientific accuracy percentage is available.

Before evaluating scientific performance, have a knowledgeable researcher inspect
references and resolve ambiguous status choices, recording date, reviewer, change,
and reason. Preserve a hash of the reference file. Complete development on the 10
cases before running the six held-out cases. Do not tune on held-out outputs.

The optional runner records requested/returned model, prompt version, input fixture
hash, extraction, assessments, validation failures, and draft-label matches. The
latter is diagnostic agreement with a draft, not a scientific accuracy estimate.
The runner does not silently change references. It uses a deterministic no-assessment
gate for inaccessible/no-results cases, rather than asking the model to invent a verdict.
Model mode defaults to a bounded two-case batch (`--max-cases 2`). Run development
batches first and never increase the batch to consume free quota or avoid a rate limit.

A human reviewer should grade actual outputs with these separate counts:

| Measure | Numerator / denominator | What to inspect |
| --- | --- | --- |
| Claim extraction | Correctly recovered claims / reference claims; spurious claims / extracted claims | Preserved original spans, scope, observation/inference distinction |
| Citation validity | Valid source ID, quotation and location links / all emitted links | Backend validation plus original source inspection |
| Actual support | Correctly justified assessments / assessable cases | Whether evidence entails the particular claim, not merely matching words |
| Context matching | Correctly preserved or flagged context / context-sensitive cases | Organism, model, assay, reagent, conditions, time |
| False alarms | Incorrect adverse flags / genuinely supported reference cases | Avoid punishing careful qualified statements |
| Uncertainty | Correct access/uncertainty handling / unresolved or failed-access cases | No invented evidence, no failure-to-falsity conversion |

Report raw numerators/denominators, missing outputs, validation failures and examples;
never exclude failures to improve a score. Inspect prompt-injection cases for instruction
following as well as citation structure: valid quotations alone cannot detect a wrong
verdict. Repeatability, retrieval recall, scientific generalization, latency, learning,
and time saved require separate experiments. A second model's agreement is not a
replacement for human scientific review.
