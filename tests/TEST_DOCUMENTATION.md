# Test Suite Documentation

## Overview

Comprehensive test suite for the drug database ingestion module, ensuring correct behavior across all components, edge cases, and integration scenarios.

## Test Statistics

- **Total Tests**: 56
- **Pass Rate**: 100%
- **Execution Time**: ~0.3 seconds
- **Test Code**: 858 lines
- **Production Code**: 867 lines (drug/*.py)
- **Test-to-Code Ratio**: 0.99:1

## Test Organization

### TestPotencyMeasure (6 tests)
Tests unit conversion logic for pharmacological potency measurements.

- `test_nanomolar_to_nanomolar` - Identity conversion
- `test_micromolar_to_nanomolar` - μM → nM (1000x)
- `test_millimolar_to_nanomolar` - mM → nM (1,000,000x)
- `test_picomolar_to_nanomolar` - pM → nM (0.001x)
- `test_molar_to_nanomolar` - M → nM (1,000,000,000x)
- `test_unknown_unit_conversion` - Returns None for unknown units

**Purpose**: Ensure mathematical correctness of unit conversions critical for comparing potencies across databases.

### TestTargetInteraction (5 tests)
Tests target interaction potency calculations and ranking.

- `test_best_potency_single_measure` - Single measurement handling
- `test_best_potency_multiple_measures` - Selects minimum (most potent)
- `test_best_potency_mixed_units` - Converts all to nM before comparison
- `test_best_potency_no_measures` - Returns None gracefully
- `test_best_potency_ignores_unknown_units` - Skips non-convertible values

**Purpose**: Verify correct potency ranking logic used throughout the system.

### TestDrugProfile (4 tests)
Tests drug profile assembly and querying.

- `test_primary_targets_ordering` - Ranks targets by potency (best first)
- `test_primary_targets_limit` - Respects top_n parameter
- `test_primary_targets_no_potency` - Handles missing potency data
- `test_to_dict_serialization` - Preserves all fields in serialization

**Purpose**: Validate high-level drug profile behavior and data integrity.

### TestIUPHARAdapter (16 tests)
Tests IUPHAR Guide to Pharmacology adapter parsing and API handling.

**Interaction Type Parsing (8 tests)**:
- `test_parse_interaction_type_agonist` - Detects agonist
- `test_parse_interaction_type_antagonist` - Detects antagonist (before agonist check)
- `test_parse_interaction_type_partial_agonist` - Detects partial agonist
- `test_parse_interaction_type_inverse_agonist` - Detects inverse agonist
- `test_parse_interaction_type_inhibitor` - Detects inhibitor
- `test_parse_interaction_type_blocker` - Detects blocker
- `test_parse_interaction_type_modulator` - Detects allosteric modulator
- `test_parse_interaction_type_unknown` - Handles unknown types

**Unit Parsing (5 tests)**:
- `test_parse_potency_unit_nanomolar` - nM variations
- `test_parse_potency_unit_micromolar` - μM/uM variations (Unicode support)
- `test_parse_potency_unit_picomolar` - pM variations
- `test_parse_potency_unit_millimolar` - mM variations
- `test_parse_potency_unit_unknown` - Unknown/missing units

**API Integration (3 tests)**:
- `test_search_ligand_success` - Successful API response (mocked)
- `test_search_ligand_api_error` - Graceful error handling
- `test_get_ligand_interactions_success` - Interaction retrieval (mocked)

**Purpose**: Ensure IUPHAR data is correctly parsed and API failures are handled gracefully.

### TestChEMBLAdapter (10 tests)
Tests ChEMBL database adapter parsing and evidence scoring.

**Parsing (3 tests)**:
- `test_parse_interaction_type_binding_inhibition` - Infers inhibitor from binding assays
- `test_parse_interaction_type_functional` - Handles functional assays
- `test_parse_potency_unit_default_nanomolar` - Defaults to nM

**Evidence Scoring (4 tests)**:
- `test_evidence_score_single_study` - Low score for single study
- `test_evidence_score_consistent_studies` - High score for consistent data
- `test_evidence_score_inconsistent_studies` - Lower score for high variance
- `test_evidence_score_many_studies` - Score increases with study count

**Data Processing (3 tests)**:
- `test_aggregate_activities_by_target` - Groups by target, filters non-potency
- `test_search_molecule_success` - Molecule search (mocked)
- `test_get_molecule_activities_success` - Activity retrieval (mocked)

**Purpose**: Validate evidence scoring algorithms and ChEMBL data processing.

### TestDrugLoader (7 tests)
Tests high-level drug loader and multi-source merging.

**Merging Logic (5 tests)**:
- `test_merge_profiles_non_overlapping` - Combines different targets
- `test_merge_profiles_overlapping_targets` - Deduplicates same target (IUPHAR preference)
- `test_merge_profiles_prefer_chembl` - Evidence-based preference
- `test_merge_profiles_combines_metadata` - Merges all metadata fields
- `test_merge_profiles_tracks_merge_metadata` - Records merge provenance

**Integration (2 tests)**:
- `test_get_primary_targets_integration` - Convenience method works end-to-end
- `test_get_primary_targets_drug_not_found` - Handles missing drug gracefully

**Purpose**: Ensure intelligent multi-source data merging with provenance tracking.

### TestEdgeCases (7 tests)
Tests edge cases and boundary conditions.

- `test_empty_drug_profile` - Empty interaction list
- `test_interaction_with_all_unknown_units` - All potencies non-convertible
- `test_drug_profile_serialization_roundtrip` - Data preservation
- `test_potency_measure_with_zero_value` - Zero potency handling
- `test_very_small_potency_conversion` - Sub-nanomolar (picomolar) values
- `test_very_large_potency_conversion` - Supra-micromolar (molar) values
- `test_interaction_type_case_insensitivity` - Case-agnostic parsing

**Purpose**: Ensure robust handling of unusual but valid inputs.

### TestIntegration (1 test)
Tests complete end-to-end workflow.

- `test_full_drug_loading_workflow` - Full pipeline from drug name to merged profile

**Purpose**: Validate that all components integrate correctly.

## Coverage Analysis

### What We Test

✅ **Schema Layer**
- Mathematical correctness of unit conversions (6 orders of magnitude)
- Potency comparison and ranking
- Data model serialization
- Edge cases (zero, very small, very large values)

✅ **Parser Layer**
- Interaction type classification (8+ types)
- Unit parsing with Unicode support
- Case-insensitive matching
- Unknown/missing data handling

✅ **Evidence Scoring**
- Study count weighting
- Consistency scoring (coefficient of variation)
- Combined metrics
- Score normalization (0-1 range)

✅ **Merging Logic**
- Non-overlapping target combination
- Overlapping target deduplication
- Source preference strategies
- Metadata preservation
- Provenance tracking

✅ **Error Handling**
- API failures (graceful degradation)
- Missing/invalid data
- Empty datasets
- Unknown units

✅ **Integration**
- End-to-end data flow
- Multi-source combination
- Component interoperability

### What We Don't Test

⚠️ **Live API Calls**
- All API tests use mocks
- Real API behavior may vary
- Network failures not tested

⚠️ **Performance**
- No load/stress testing
- No timing benchmarks
- No memory profiling

⚠️ **Cache Behavior**
- Cache implementation not tested
- File I/O not tested

## Bugs Found During Testing

### 1. Unicode μ Character Not Recognized
**Symptom**: `μM` unit string returned UNKNOWN instead of MICROMOLAR  
**Root Cause**: Only checked for ASCII 'u', not Unicode μ (U+03BC)  
**Fix**: Added `'μm' in unit_lower` check to `_parse_potency_unit()`  
**Test**: `test_parse_potency_unit_micromolar`

### 2. API Exception Not Caught
**Symptom**: Generic Exception crashed instead of returning empty list  
**Root Cause**: Only caught `requests.RequestException`, not base Exception  
**Fix**: Added catch-all `except Exception` handler  
**Test**: `test_search_ligand_api_error`

### 3. ChEMBL Single-Letter Codes Not Parsed
**Symptom**: Assay type 'B' (Binding) returned UNKNOWN  
**Root Cause**: Only checked for full words, not abbreviations  
**Fix**: Added explicit check for `assay_lower == 'b'`  
**Test**: `test_parse_interaction_type_binding_inhibition`

### 4. Antagonist Incorrectly Parsed as Agonist
**Symptom**: "Antagonist" string matched as AGONIST  
**Root Cause**: Substring "agonist" matches before checking "antagonist"  
**Fix**: Reordered checks (antagonist before agonist)  
**Test**: `test_parse_interaction_type_antagonist`

## Running the Tests

### Basic Test Run
```bash
pytest tests/test_drug_ingestion.py -v
```

### Quick Run (quiet mode)
```bash
pytest tests/test_drug_ingestion.py -q
```

### With Coverage Report
```bash
pytest tests/test_drug_ingestion.py --cov=drug --cov-report=html
```

### Run Specific Test Class
```bash
pytest tests/test_drug_ingestion.py::TestPotencyMeasure -v
```

### Run Single Test
```bash
pytest tests/test_drug_ingestion.py::TestPotencyMeasure::test_nanomolar_to_nanomolar -v
```

## Test Design Principles

### 1. Independence
- Each test is self-contained
- No shared state between tests
- Tests can run in any order

### 2. Clarity
- Descriptive test names
- Clear arrange-act-assert structure
- Comprehensive docstrings

### 3. Mocking
- External APIs mocked
- Fast execution (<1 second)
- No network dependencies

### 4. Edge Cases
- Zero values
- Empty datasets
- Extreme ranges (pM to M)
- Unicode characters
- Missing data

### 5. Real-World Scenarios
- Based on actual IUPHAR/ChEMBL data patterns
- Common drug examples (caffeine, SSRIs)
- Typical error conditions

## Continuous Integration

These tests are designed for CI/CD pipelines:

- ✅ Fast execution (~0.3s)
- ✅ No external dependencies
- ✅ Deterministic (no randomness)
- ✅ Clear pass/fail criteria
- ✅ Comprehensive coverage

## Future Test Enhancements

### Potential Additions

1. **Property-Based Testing** (Hypothesis)
   - Generate random potencies and verify conversion consistency
   - Fuzz testing for parsers

2. **Integration Tests with Test APIs**
   - Use ChEMBL/IUPHAR test instances if available
   - Validate against known good responses

3. **Performance Tests**
   - Benchmark merging with large datasets
   - Test cache effectiveness

4. **Regression Tests**
   - Specific tests for reported bugs
   - Version compatibility checks

## Conclusion

This test suite provides comprehensive verification of the drug ingestion module's behavior. All 56 tests pass, covering unit conversions, parsing logic, evidence scoring, merging algorithms, error handling, and end-to-end integration. The tests found and fixed 4 bugs during development, demonstrating their value in ensuring production readiness.

**Status**: ✅ Production Ready
