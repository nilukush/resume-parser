"""
Test spaCy and Python 3.12 compatibility.

This test verifies that spaCy can be imported and initialized
without ForwardRef._evaluate errors on Python 3.12+.

Related: Bug Fix #19 - Python 3.12 Deployment Error
"""
import sys
import pytest
from unittest.mock import patch, MagicMock


class TestSpacyPython312Compatibility:
    """Test spaCy compatibility with Python 3.12"""

    def test_spacy_imports_without_forwardref_error(self):
        """
        Test that spaCy can be imported without ForwardRef._evaluate errors.

        This test will fail if spaCy version is incompatible with Python 3.12.
        The error manifests as: TypeError: ForwardRef._evaluate() missing
        1 required keyword-only argument: 'recursive_guard'

        Expected behavior:
        - Python 3.12+ requires spaCy 3.8+
        - spaCy 3.7.2 will fail on import
        """
        # This import will fail with ForwardRef error if incompatible
        try:
            import spacy
            from spacy.language import Language
            from spacy.tokens import Doc, Span, Token

            # If we reach here, import succeeded
            assert True, "spaCy imported successfully"

            # Verify we can check the version
            assert hasattr(spacy, '__version__'), "spaCy has __version__ attribute"

            # Parse version to ensure it's 3.8+ for Python 3.12+
            major, minor, *_ = map(int, spacy.__version__.split('.'))
            if sys.version_info >= (3, 12):
                assert (major, minor) >= (3, 8), (
                    f"spaCy 3.8+ required for Python 3.12+, got {spacy.__version__}"
                )

        except TypeError as e:
            if "ForwardRef._evaluate" in str(e):
                pytest.fail(
                    f"spaCy version incompatible with Python {sys.version_info.major}.{sys.version_info.minor}: {e}"
                )
            else:
                raise

    def test_spacy_language_class_exists(self):
        """Test that spacy.Language class can be accessed (tests pydantic integration)"""
        import spacy
        from spacy.language import Language

        # Verify Language class exists and is callable
        assert callable(Language), "Language class should be callable"

    def test_pydantic_compatibility_with_spacy(self):
        """
        Test that Pydantic can validate spaCy's internal models.

        This specifically tests the TokenPatternString model that was
        failing in the original error.
        """
        import spacy

        # Import spacy.schemas which contains TokenPatternString
        # This is where the original error occurred
        try:
            from spacy import schemas

            # If we can import schemas without error, pydantic compatibility works
            assert hasattr(schemas, 'TokenPatternString'), (
                "TokenPatternString should exist in spacy.schemas"
            )

        except TypeError as e:
            if "ForwardRef" in str(e) or "recursive_guard" in str(e):
                pytest.fail(f"Pydantic/spaCy version incompatibility: {e}")
            else:
                raise

    @pytest.mark.skipif(
        sys.version_info < (3, 12),
        reason="Test only applicable to Python 3.12+"
    )
    def test_python_312_specific_requirements(self):
        """Test Python 3.12 specific requirements"""
        import sys

        # Verify we're on Python 3.12+
        assert sys.version_info >= (3, 12), "This test requires Python 3.12+"

        # Import spacy and verify version
        import spacy

        major, minor, *_ = map(int, spacy.__version__.split('.'))
        assert (major, minor) >= (3, 8), (
            f"Python 3.12+ requires spaCy 3.8+, got {spacy.__version__}"
        )


class TestSpacyMinimalFunctionality:
    """Test basic spaCy functionality after successful import"""

    @pytest.mark.skipif(
        sys.version_info < (3, 12),
        reason="Test only applicable to Python 3.12+"
    )
    def test_spacy_blank_model_can_be_created(self):
        """Test that a blank spaCy model can be created (no download required)"""
        import spacy

        # Create a blank model (doesn't require downloading models)
        try:
            nlp = spacy.blank("en")
            assert nlp is not None, "Blank model should be created"

            # Test basic processing
            doc = nlp("Hello world")
            assert len(doc) == 2, "Should process 2 tokens"

        except TypeError as e:
            if "ForwardRef" in str(e):
                pytest.fail(f"ForwardRef error during model creation: {e}")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
