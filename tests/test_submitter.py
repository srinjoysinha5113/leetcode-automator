import pytest
from unittest.mock import AsyncMock, patch
from app.config import settings
from app.models import Verdict, VerificationStatus
from app.submitter import LeetCodeSubmitter

@pytest.mark.asyncio
async def test_auto_submit_false_blocks_submission():
    """Test that AUTO_SUBMIT=false completely halts submission without opening browser."""
    with patch.object(settings, "AUTO_SUBMIT", False):
        submitter = LeetCodeSubmitter()
        res = await submitter.submit_solution(
            problem_slug="two-sum",
            solution_code="class Solution: pass",
        )
        assert res.verdict == Verdict.UNKNOWN
        assert "AUTO_SUBMIT is disabled" in res.error

@pytest.mark.asyncio
async def test_unverified_account_blocks_submission():
    """Test that unverified account halts submission."""
    with patch.object(settings, "AUTO_SUBMIT", True):
        submitter = LeetCodeSubmitter()
        submitter.verifier.verify_identity = AsyncMock(
            return_value=(VerificationStatus.MISMATCH, "wrong_user", "Mismatch")
        )
        res = await submitter.submit_solution(
            problem_slug="two-sum",
            solution_code="class Solution: pass",
        )
        assert res.verdict == Verdict.UNKNOWN
        assert "Account verification failed" in res.error
