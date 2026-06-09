# CDC PLACES Comparison Evaluation Dataset

## Purpose

This evaluation dataset tests whether AI agents correctly apply CDC PLACES guidance on comparing health estimates across geographic areas (counties, places, census tracts, and ZCTAs).

## Key Testing Areas

Based on CDC PLACES documentation, comparisons must consider three critical factors:

### 1. Confidence Intervals (5 questions: Q001-Q005, Q015)
- **Test:** Does the agent check confidence interval width and overlap before comparing?
- **Valid:** Non-overlapping, narrow CIs support comparison
- **Invalid:** Broad, overlapping CIs make comparison inappropriate
- **Key principle:** "It is not adequate to simply compare point estimates"

### 2. Population Characteristics (5 questions: Q005-Q009)
- **Test:** Does the agent consider demographic differences (age, race/ethnicity)?
- **Valid:** Agent acknowledges demographic context when interpreting differences
- **Invalid:** Agent ignores population characteristics that explain observed differences
- **Key principle:** "Consider differences in the population characteristics...which may also contribute to any differences observed"

### 3. Age-Adjusted vs Crude Estimates (5 questions: Q010-Q014)
- **Test:** Does the agent use appropriate estimate types for geographic level?
- **Valid:** Age-adjusted for county/place; crude for tract/ZCTA
- **Invalid:** Mixing estimate types or requesting unavailable adjustments
- **Key principle:** "Age-adjusted estimates...can be used for county- and place-level comparisons"

## Dataset Structure

**File:** `places-comparison-0.csv`

**Columns:**
- `question_id`: Unique identifier (Q001-Q015)
- `input`: The comparison question posed to the agent
- `expected_behavior`: What a correct response should address
- `comparison_validity`: Classification of comparison appropriateness
  - `valid`: Comparison is statistically and methodologically appropriate
  - `invalid`: Comparison should not be made or conclusion cannot be drawn
  - `requires_context`: Comparison is possible but requires demographic/methodological caveats
- `reasoning`: Why this classification is correct per CDC guidance
- `test_category`: Primary category being tested

## Question Distribution

| Category | Valid | Invalid | Requires Context | Total |
|----------|-------|---------|------------------|-------|
| Confidence Intervals | 2 | 3 | 0 | 5 |
| Population Characteristics | 0 | 1 | 4 | 5 |
| Age Adjustment | 3 | 2 | 0 | 5 |
| **Total** | **5** | **6** | **4** | **15** |

## Scoring Criteria

An ideal agent response should:

### For Valid Comparisons:
- ✅ Compare point estimates
- ✅ Check and mention confidence intervals
- ✅ Note whether CIs overlap or not
- ✅ Recommend age-adjusted estimates for county/place level when applicable
- ✅ Acknowledge demographic considerations

### For Invalid Comparisons:
- ✅ Refuse to make definitive comparison
- ✅ Explain why (broad CIs, overlap, demographic confounding, methodology mismatch)
- ✅ Cite specific statistical or methodological reasons
- ✅ Suggest what additional information would be needed

### For Context-Required Comparisons:
- ✅ Provide statistical comparison if CIs support it
- ✅ Explicitly note limitations and caveats
- ✅ Discuss demographic factors that may explain differences
- ✅ Recommend age-adjusted estimates when available
- ✅ Explain uncertainty or confounding factors

## Example Evaluation Dimensions

For each response, evaluate:

1. **CI Awareness** (0-3 points)
   - 0: Ignores CIs entirely
   - 1: Mentions CIs but doesn't interpret correctly
   - 2: Correctly interprets CI overlap/width
   - 3: Correctly interprets CIs and explains implications

2. **Demographic Consideration** (0-3 points)
   - 0: Ignores population characteristics
   - 1: Mentions demographics generically
   - 2: Identifies specific relevant demographic factors
   - 3: Explains how demographics affect interpretation

3. **Methodology Awareness** (0-3 points)
   - 0: Doesn't distinguish estimate types
   - 1: Mentions age-adjustment
   - 2: Correctly identifies when to use age-adjusted vs crude
   - 3: Correctly applies methodology to geographic level

4. **Appropriate Caution** (0-3 points)
   - 0: Makes unjustified definitive claims
   - 1: Shows some caution
   - 2: Appropriately qualifies conclusions
   - 3: Refuses invalid comparisons with clear reasoning

**Maximum Score: 12 points per question**

## Usage

This dataset is designed for use with Phoenix or similar LLM evaluation frameworks. Load the CSV and evaluate agent responses against the `expected_behavior` and `comparison_validity` fields.

### Example Evaluation Code Structure:

```python
import pandas as pd

df = pd.read_csv('places-comparison-0.csv')

for _, row in df.iterrows():
    response = agent.query(row['input'])
    
    # Evaluate response against expected_behavior
    score = evaluate_response(
        response=response,
        expected_behavior=row['expected_behavior'],
        comparison_validity=row['comparison_validity'],
        reasoning=row['reasoning']
    )
```

## References

- CDC PLACES: Local Data for Better Health
- CDC PLACES Comparison Guidance (Documentation Section on Geographic Comparisons)
- PLACES Methodology: https://www.cdc.gov/places/methodology/index.html

## Version

- **Version:** 0.1.0
- **Created:** 2026-06-09
- **Questions:** 15
- **Format:** CSV

## Future Enhancements

Potential additions for version 0.2.0:
- Questions involving specific statistical tests
- Multi-step comparison scenarios
- Questions requiring data retrieval via MCP server
- Time-series comparison questions
- Questions involving small number suppression
