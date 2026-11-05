# Trustworthy educational AI: public analysis materials

Materials supporting **Operationalising trustworthy educational AI: A stakeholder-informed lifecycle framework for systems-thinking support**.

## Data availability

**Participant-level data are under the EduGenZ project embargo and are not included in this release.** This repository makes the analysis methods, questionnaire documentation and aggregate results available for inspection. The data-release arrangements will be updated following expiry of the embargo and the applicable release authorisation. See [Data access](docs/DATA_ACCESS.md).

## Public contents

| Folder/file | Contents |
|---|---|
| `code/` | Descriptive statistics, corrected non-parametric comparisons, correlation/PCA/t-SNE, sensitivity checks and student-focused analyses |
| `matlab/run_mixed_effects.m` | CSV-based refitting of the source mixed-effects procedure, including model/formula exports |
| `matlab/original/` | Historical MATLAB source for provenance; see the historical-code note below |
| `data/` | Questionnaire item dictionary and variable/scoring dictionary; no response records |
| `reference_results/` | Aggregate numerical summaries, tests, model coefficient exports and sensitivity results |
| `figures/` | Aggregate requirement/subcategory priorities, relevance–importance, robustness and student summaries |
| `docs/` | Scoring, verification report, cross-context specifications and manuscript data-availability wording |
| `requirements.txt` | Pinned Python dependencies |
| `run_all.py` | Analysis runner, for use when an authorised dataset is available |

Individual response tables, demographic records, submission timestamps, PCA/t-SNE coordinates and individual-profile figures are excluded.

## Inspecting the public materials

The CSV tables, dictionaries and PNG figures can be read directly without running code. There are seven trustworthiness requirements, nineteen subcategories and 84 instrument statements. The RFPR manuscript abbreviation corresponds to PFPR in the original analysis. Both occurrences of the repeated statement (Q46 and Q50) are preserved in the item dictionary.

The reference mixed-effects files contain 37 requirement and 85 subcategory non-intercept coefficient rows. These are supplied numerical exports, not complete historical saved fitted-model objects. Cross-context tables describe author-constructed application specifications, not observations collected from further participants.

## Reanalysis with authorised data

The scripts require participant-level data. They cannot regenerate the results from the aggregate tables alone. Once an authorised `data/responses.csv` is available, use Python 3.12.14 or a compatible Python 3.12 environment:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py --quick
python run_all.py
python code/verify_reference_results.py
```

The quick command regenerates descriptive and non-parametric tables. The full command additionally runs the multivariate, sensitivity and student analyses with the documented seeds and resampling counts. Outputs go under `results/`, leaving reference tables unchanged. Without the embargoed dataset the runner exits with a data-access message.

For MATLAB R2026a and Statistics and Machine Learning Toolbox:

```matlab
addpath('matlab');
run_mixed_effects;
```

This runner tries the original candidate predictor order (Institution, Relation, Gender), proceeding from the full additive set to smaller combinations when fitting fails, with participant and item random intercepts. It saves model objects, retained formulas and coefficients in `results/mixed_effects/`. MATLAB refitting was not executed during preparation of this release; compare new results against the reference exports before replacing manuscript values.

## Verification and historical-code note

Before the participant dataset was excluded from this release, the full Python pipeline was run using the timestamp-free data. All 19 regenerated numerical CSV tables matched their reference exports (relative tolerance 1e-8; absolute tolerance 1e-10). See `docs/verification_report.json`. This check covers Python numerical outputs, not MATLAB refitting.

`matlab/original/computeALTAI_full.m` is the supplied historical source, not the recommended analysis entry point. It includes the original lowercase gender-selection bug and independent-rating confidence intervals. The current manuscript uses the corrected Python gender comparisons and whole-participant bootstrap intervals.

## Interpretation

0 denotes a non-relevance judgement; 1, 2 and 3 denote low, medium and high importance. Conditional importance excludes 0 and multiplies by 10/3. Whole-participant bootstrap samples keep questionnaire items fixed. Mixed-effects models use non-zero ratings on the original 1–3 scale. Non-parametric comparisons are unadjusted; requirement-correlation tests use Benjamini–Hochberg correction. PCA/t-SNE describe profiles and do not establish latent psychological types. Student subsets are role-defined and do not establish generational membership.

## Repository upload

Extract this ZIP and upload its contents to the GitHub repository root using **Add file → Upload files**. Do not upload the earlier `CEAI_GitHub_Repository.zip`, which contains participant-level data. Replace the URL placeholder in `docs/DATA_AVAILABILITY.tex` with the actual public repository URL before copying that text into the manuscript.

## Attribution and reuse

The questionnaire is adapted from the High-Level Expert Group on Artificial Intelligence (2020), *The Assessment List for Trustworthy Artificial Intelligence (ALTAI) for self-assessment*, European Commission.

No open-source or data licence has been selected on behalf of the authors. Public access does not itself grant a licence; rights in third-party questionnaire material remain with their respective holders.
