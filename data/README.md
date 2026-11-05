# Data documentation

This folder contains questionnaire and variable dictionaries only. Participant-level responses, submission timestamps and respondent identifiers are not included.

The analysis scripts expect an authorised `responses.csv` with columns:

```text
participant_id,institution,project_role,gender,Q01,...,Q84
```

The full field definitions are in `variable_dictionary.csv`. Item codes, grouping and wording are in `item_dictionary.csv`. The public release does not include a synthetic substitute or fabricated participant data.

See `../docs/DATA_ACCESS.md` for the embargo statement.
