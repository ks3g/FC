# Dependency Issues Analysis

## Critical Issues Identified

### 🔴 Issue #1: Segmentation Fault with Docling 2.44.0

**Severity:** HIGH - Crashes tests and potentially production
**Affected Component:** RAG/PDF Processing
**Status:** ⚠️ REQUIRES IMMEDIATE ATTENTION

#### Root Cause Analysis

1. **Version Constraint Too Loose**
   - Current: `docling>=1.0.0` in requirements-rag.txt
   - Installed: Docling 2.44.0 (latest)
   - Problem: Breaking changes between major versions

2. **Binary Incompatibility**
   - Docling includes C/C++ extensions for PDF parsing
   - Version 2.44.0 may have:
     - ABI incompatibilities with Python 3.11.14
     - Memory access issues in sandboxed environments (gVisor/runsc)
     - Dependencies on newer system libraries

3. **Environment Factors**
   - Platform: Linux 4.4.0 (gVisor sandbox)
   - Python: 3.11.14
   - Architecture: x86_64
   - Sandbox: gVisor may restrict certain syscalls needed by Docling's C extensions

#### Impact Assessment

**Currently Broken:**
- ✗ `test_rag_components.py` - Cannot run
- ✗ PDF processing functionality - May crash
- ✗ RAG retrieval with PDF sources - Unreliable

**Still Working:**
- ✓ Core agent functionality (no PDF processing)
- ✓ Presentation and validation agents
- ✓ Orchestration and parallel execution
- ✓ Metrics and source tracking

#### Recommended Solutions

**Option 1: Version Pinning (RECOMMENDED)**
```bash
# requirements-rag.txt
docling>=1.0.0,<2.0.0  # Pin to v1.x series
```
**Pros:**
- Quick fix
- Known working version
- Minimal code changes

**Cons:**
- Miss out on v2.x improvements
- Technical debt

**Option 2: Alternative PDF Library**
```bash
# Use pypdfium2 instead
pypdfium2>=4.0.0
pdfplumber>=0.10.0
```
**Pros:**
- More stable
- Better sandbox compatibility
- Lighter dependencies

**Cons:**
- Requires refactoring pdf_processor.py
- May lose some Docling-specific features

**Option 3: Make Docling Truly Optional**
- Enhance graceful degradation
- Add mock PDF processor for tests
- Document limitation clearly

**Pros:**
- Tests work without Docling
- System still functional
- Better modularity

**Cons:**
- Limited PDF functionality
- More complex testing setup

---

### 🔴 Issue #2: ChromaDB Not Installed

**Severity:** MEDIUM - Tests incomplete, feature disabled
**Affected Component:** Vector database / RAG storage
**Status:** ⚠️ MISSING DEPENDENCY

#### Root Cause Analysis

1. **Optional Dependency Not Installed**
   - Defined in `requirements-rag.txt`
   - Not installed by default
   - Users must manually install

2. **Test Assumptions**
   - Tests assume ChromaDB is available
   - No clear documentation about optional deps
   - Setup instructions incomplete

#### Impact Assessment

**Currently Broken:**
- ✗ Vector database storage - Not available
- ✗ Semantic search in PDFs - Disabled
- ✗ RAG retrieval - Mock mode only

**Still Working:**
- ✓ Tests use mocks and pass
- ✓ PDF processing logic (without storage)
- ✓ All non-RAG functionality

#### Recommended Solutions

**Option 1: Install ChromaDB (IMMEDIATE)**
```bash
pip install -r requirements-rag.txt
```

**Option 2: Add to Main Requirements**
```bash
# requirements.txt - if RAG is core feature
chromadb>=0.4.0
sentence-transformers>=2.2.0
```

**Option 3: Better Documentation**
```markdown
# README.md

## Optional Features

### RAG/PDF Processing
To enable PDF processing and semantic search:
```bash
pip install -r requirements-rag.txt
```

This installs:
- ChromaDB (vector database)
- sentence-transformers (embeddings)
- docling (PDF parsing)
```

---

## Recommended Action Plan

### Phase 1: Immediate Fixes (Today)

1. **Fix Docling Version Constraint**
   ```diff
   # requirements-rag.txt
   - docling>=1.0.0
   + docling>=1.0.0,<2.0.0
   ```

2. **Document RAG Setup Clearly**
   - Add setup section to README
   - Specify optional vs required deps
   - Provide installation commands

3. **Add Test Skip Logic**
   ```python
   # tests/test_rag_components.py
   import pytest

   @pytest.mark.skipif(not CHROMADB_AVAILABLE,
                      reason="ChromaDB not installed")
   def test_vector_storage():
       ...
   ```

### Phase 2: Short-term Improvements (This Week)

1. **Create Mock PDF Processor for Tests**
   - Allow tests to run without Docling
   - Mock ChromaDB interactions
   - Enable CI/CD without heavy deps

2. **Add Dependency Checker**
   ```python
   # scripts/check_dependencies.py
   def check_rag_dependencies():
       results = {
           'chromadb': check_import('chromadb'),
           'docling': check_import('docling'),
           'sentence_transformers': check_import('sentence_transformers')
       }
       print_status(results)
   ```

3. **Update Documentation**
   - System architecture diagram
   - Dependency tree
   - Feature availability matrix

### Phase 3: Long-term Solutions (Next Sprint)

1. **Evaluate Docling Alternatives**
   - Test pypdfium2
   - Test pdfplumber
   - Benchmark performance/compatibility

2. **Consider Containerization**
   - Docker image with all deps pre-installed
   - Avoid host system incompatibilities
   - Better reproducibility

3. **Add Integration Tests**
   - Test actual PDF processing (not mocked)
   - Test ChromaDB storage/retrieval
   - Test end-to-end RAG workflow

---

## Risk Assessment

| Issue | Severity | Likelihood | Impact | Priority |
|-------|----------|------------|--------|----------|
| Docling Segfault | HIGH | High | System crash | P0 |
| ChromaDB Missing | MEDIUM | Medium | Feature disabled | P1 |
| Test Coverage Gap | LOW | Low | Incomplete validation | P2 |

---

## Testing Strategy

### With RAG Dependencies
```bash
# Install full stack
pip install -r requirements.txt
pip install -r requirements-rag.txt

# Run all tests
python tests/run_all_tests.py
python examples/test_complete_workflow.py
```

### Without RAG Dependencies
```bash
# Install core only
pip install -r requirements.txt

# Run core tests
python tests/test_presentation_validation.py
python tests/test_metrics_sources.py
python examples/test_complete_workflow.py  # Should still work with warnings
```

### CI/CD Recommendation
```yaml
# .github/workflows/test.yml
jobs:
  test-core:
    # Test without RAG deps
    - pip install -r requirements.txt
    - python tests/test_presentation_validation.py

  test-rag:
    # Test with RAG deps (may fail until fixed)
    - pip install -r requirements.txt requirements-rag.txt
    - python tests/test_rag_components.py
```

---

## Decision Matrix

| Criterion | Pin Docling v1 | Switch Library | Make Optional |
|-----------|----------------|----------------|---------------|
| **Time to Fix** | 5 min | 2-4 hours | 1-2 hours |
| **Risk** | Low | Medium | Low |
| **Future Proof** | Poor | Good | Good |
| **User Impact** | None | None | Minimal |
| **Maintenance** | Low | Medium | Low |
| **Recommendation** | ✅ Do Now | Consider Later | ✅ Do Now |

---

## Conclusion

**Immediate Actions Required:**
1. ✅ Pin Docling to v1.x series
2. ✅ Document ChromaDB installation clearly
3. ✅ Add test skipping for missing deps

**Success Criteria:**
- All tests pass (with or without RAG deps)
- No segmentation faults
- Clear documentation
- User can choose to enable/disable RAG features

**Timeline:**
- Immediate fixes: 30 minutes
- Documentation: 1 hour
- Testing validation: 30 minutes
- **Total: 2 hours**
