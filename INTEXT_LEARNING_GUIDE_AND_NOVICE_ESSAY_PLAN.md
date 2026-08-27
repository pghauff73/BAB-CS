# BAB-CS In-Text Learning Guide and Novice Essay Plan

## Objective

Replace the separate per-document learning-guide panel with explanations that
appear in the reading flow at the first visible introduction of each recognized
concept. Review the complete HTML document tree, then rewrite the most technical
essays so a novice engineer can follow the engineering decision before learning
the detailed mathematics or software terminology.

## Current-State Review

The generated HTML tree currently contains 27 Markdown documents in seven
navigation groups. Every document has deterministic glossary coverage, with
between 6 and 43 recognized concepts. The current `Document Learning Guide`
appears before the prose as an expandable card. It is complete, but it creates
three educational problems:

1. definitions are separated from the sentence that introduces the term;
2. a large guide asks the reader to learn vocabulary before understanding why it
   matters; and
3. the guide can occupy substantial vertical space before short documents.

The existing dotted first-occurrence annotation helps, but its full definition
is available mainly through hover, focus, or the separate guide. The redesign
must make the explanation visible in the reading flow without requiring a
pointer device.

## In-Text Educational Contract

For every recognized concept used in visible prose:

- mark its first visible occurrence with an accessible abbreviation element;
- attach a visible `Plain words` note to the paragraph, list item, table cell, or
  heading that introduced it;
- group multiple new concepts from one text block into one compact note;
- keep code blocks, links, identifiers, formulas, and source Markdown unchanged;
- skip the hidden Markdown level-one heading and annotate the first visible
  introduction instead; and
- preserve keyboard focus and screen-reader association between the marked term
  and its explanation.

The separate top-of-document glossary panel will be removed. The deterministic
glossary remains the canonical explanation owner and continues to support
acronym coverage tests.

## Selected Essay Rewrite

The following essays receive additional novice-engineer restructuring because
they contain the highest concentration of mathematical, implementation, and
release-governance concepts:

1. `docs/NUMERICAL_METHODS_ESSAY.md`
   - begin with the engineering decisions the reader is trying to make;
   - add one concrete timestep walkthrough; and
   - connect each mathematical control to a visible failure it prevents.
2. `docs/ENGINEERING_AND_PERFORMANCE_ESSAY.md`
   - explain one timestep as it moves through model, candidate, authority,
     simulator, and evidence owners;
   - distinguish faster kernels from faster complete simulations; and
   - explain retained and rejected optimizations as engineering decisions.
3. `docs/VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md`
   - introduce an evidence ladder from formula test to human release approval;
   - show why each rung answers a different question; and
   - separate validation, qualification, certification, and publication in
     novice language.

The two remaining current-work essays already use project-led and application-
led structures and will retain their present rewrites unless the browser review
finds a specific readability problem.

## Implementation Phases

### Phase 1: Renderer

- remove `renderDocumentLearningGuide` from the document layout;
- extend first-introduction annotation to collect definitions by visible text
  block;
- render one in-text note immediately after, or inside, the introducing block;
- connect each marked term to its note with `aria-describedby`; and
- retain native hover text as a secondary aid.

### Phase 2: Visual Design

- style in-text notes as compact editorial annotations rather than cards;
- use a restrained left rule, small `Plain words` label, and readable wrapping;
- avoid breaking tables, lists, headings, print, or mobile flow; and
- keep the marked term visible without making every paragraph look interactive.

### Phase 3: Essay Rewrite

- implement the selected essay changes above;
- retain formulas, references, claim boundaries, and exact technical meaning;
- use shorter paragraphs and concrete engineering questions; and
- define unavoidable specialist language at first introduction.

### Phase 4: Verification

- prove all 27 Markdown documents still appear exactly once;
- prove every document retains nonempty deterministic concept coverage;
- prove the prose acronym audit remains empty;
- test that the separate learning-guide panel is absent;
- test that paragraph-level in-text notes and accessibility links are present;
- regenerate the deterministic payload and six SVG assets;
- run the complete repository suite; and
- inspect desktop, mobile, long technical, table-heavy, and print-oriented views.

## Problem and Fix Loop

| Iteration | Problem | Correction plan | Proof or current status |
|---|---|---|---|
| 1 | The separate glossary interrupts the reading sequence. | Remove it and attach definitions to the introducing text block. | Verified: desktop documents begin with the essay, not a separate glossary panel. |
| 2 | Hover-only definitions are weak on touch devices and for keyboard-first reading. | Render visible notes and connect marked terms with `aria-describedby`. | Verified: mobile captures show visible notes; static tests prove the accessibility association. |
| 3 | Several new terms can occur in one paragraph. | Group them into one ordered `Plain words` note rather than inserting repeated parentheses. | Verified in the architecture and engineering captures. |
| 4 | Definitions inserted directly inside a table row or list can produce invalid or cramped layout. | Keep list notes inside their list item, but group table definitions before the complete table wrapper. | Verified in long engineering and release-audit captures. |
| 5 | Rewriting too many documents could blur normative or audit evidence. | Restrict source prose changes to the three selected essays and use the generated learning layer elsewhere. | Verified by the focused source diff and unchanged formulas, references, and claim boundaries. |
| 6 | Focused tests found that `documents.js` and the qualification-surface SVG still represented the pre-rewrite sources and pre-test count. | Regenerate all deterministic HTML payload and SVG outputs only after the prose, glossary-detection, renderer, and test changes settle. | Fixed: generator `--check` passes with 27 documents and six SVG assets. |
| 7 | Desktop browser review showed the generated hero summary repeated as the first paragraph of the document body, forcing a novice to read the same statement twice before reaching new material. | Remove the body paragraph only when its normalized rendered text matches the generated hero summary; retain the hero copy as the visible introduction. | Fixed and rechecked in architecture, numerical-method, and validation pages. |
| 8 | Removing the duplicate paragraph also removed the earliest visible glossary annotation, so a mobile reader could reach a diagram before seeing the meaning of BAB-CS or candidate method. | Annotate concepts in the hero summary first, carry the introduced-concept set into the body, and assign unique note identifiers across both regions. | Fixed and rechecked on desktop and mobile architecture pages. |
| 9 | Browser review annotated the ordinary word “be” as the acronym `BE` for backward Euler because all aliases were matched without case sensitivity. | Match all-uppercase acronym aliases with exact case in both Python concept discovery and JavaScript annotation, while retaining case-insensitive matching for normal phrases. | Fixed by regression tests and validation-page browser recheck. |
| 10 | The long release-audit capture showed that definitions appended inside table headers and cells made rows excessively tall and obscured the comparison structure. | Group all first introductions from one table into a single note and place it immediately before the table wrapper; retain `aria-describedby` links from each marked table term. | Fixed: the release requirement matrix retains compact rows with one note before the table. |
| 11 | A long hero summary was truncated inside the word “agrees,” producing an unprofessional fragment before the ellipsis. | Shorten generated summaries at the last complete word that fits the limit, then append one ellipsis. | Fixed by a word-boundary regression test and validation-page browser recheck. |

## Completion Criteria

The objective is complete only when the separate learning-guide panel has been
removed, first concept explanations are visible in context across the document
tree, the three selected essays have concrete novice-engineer structures, all
reported rendering issues are fixed and recorded, deterministic generation is
current, and the complete test plus browser audit passes.

## Completion Audit

Completed on August 27, 2026.

- **Document tree:** all 27 Markdown documents appear exactly once across seven
  generated navigation categories.
- **Learning layer:** 88 deterministic glossary concepts provide between three
  and 42 relevant in-text explanations per document, with zero unexplained prose
  acronyms in the audit.
- **Renderer:** the separate learning-guide panel is absent; first introductions
  in hero summaries, paragraphs, lists, headings, and tables use visible grouped
  notes, hover text, keyboard focus, and `aria-describedby` associations.
- **Table behavior:** table concepts are grouped before the table wrapper rather
  than expanding individual rows or headers.
- **Essay rewrites:** the numerical essay now begins with engineering questions
  and a timestep walkthrough; the engineering essay follows one timestep through
  software owners and separates kernel speed from complete-run speed; the
  validation essay uses an evidence ladder and separates validation,
  qualification, certification, and publication.
- **Deterministic artifacts:** `documents.js` and all six SVG diagrams regenerate
  byte deterministically, and generator `--check` passes.
- **Automated validation:** all 18 documentation tests pass; the complete suite
  passes 294 tests with two intentionally scheduled long-horizon tests skipped;
  JavaScript syntax and `git diff --check` also pass.
- **Browser validation:** Firefox headless captures pass for the home page,
  architecture page, all three rewritten essays, long list-heavy content, the
  release requirement table, and a 390-pixel mobile viewport.
- **Print validation limit:** print-media rules were inspected statically and
  keep in-text notes visible, but an interactive system print dialog was not
  automated in this environment.

No blocking implementation problem remains within this plan's scope.
