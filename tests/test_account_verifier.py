import pytest
from unittest.mock import AsyncMock, patch
from app.account_verifier import AccountVerifier
from app.models import VerificationStatus

@pytest.mark.asyncio
async def test_unverifiable_when_username_not_configured():
    """Test that verification immediately fails with UNVERIFIABLE if EXPECTED_LEETCODE_USERNAME is empty."""
    verifier = AccountVerifier()
    verifier.expected_username = ""
    status, username, msg = await verifier.verify_identity(headless=True)
    assert status == VerificationStatus.UNVERIFIABLE
    assert username is None
    assert "not configured" in msg

@pytest.mark.asyncio
@patch.object(AccountVerifier, "get_active_username", new_callable=AsyncMock)
@patch("playwright.async_api.async_playwright")
async def test_account_username_matching(mock_playwright, mock_get_username):
    """Test successful verification when authenticated username matches configured username."""
    # Setup mocks
    mock_get_username.return_value = (True, "srinjoysinha32820")
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page
    mock_p_instance = AsyncMock()
    mock_p_instance.chromium.launch_persistent_context.return_value = mock_context
    mock_playwright.return_value.__aenter__.return_value = mock_p_instance

    verifier = AccountVerifier()
    verifier.expected_username = "srinjoysinha32820"

    status, username, msg = await verifier.verify_identity(headless=True)
    assert status == VerificationStatus.VERIFIED
    assert username == "srinjoysinha32820"
    assert "verified successfully" in msg

@pytest.mark.asyncio
@patch.object(AccountVerifier, "get_active_username", new_callable=AsyncMock)
@patch("playwright.async_api.async_playwright")
async def test_account_username_mismatch(mock_playwright, mock_get_username):
    """Test that mismatched username disables submissions with MISMATCH status."""
    mock_get_username.return_value = (True, "different_user")
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page
    mock_p_instance = AsyncMock()
    mock_p_instance.chromium.launch_persistent_context.return_value = mock_context
    mock_playwright.return_value.__aenter__.return_value = mock_p_instance

    verifier = AccountVerifier()
    verifier.expected_username = "srinjoysinha32820"

    status, username, msg = await verifier.verify_identity(headless=True)
    assert status == VerificationStatus.MISMATCH
    assert username == "different_user"
    assert "Account mismatch" in msg

@pytest.mark.asyncio
@patch.object(AccountVerifier, "get_active_username", new_callable=AsyncMock)
@patch("playwright.async_api.async_playwright")
async def test_logged_out_session(mock_playwright, mock_get_username):
    """Test that an unauthenticated session returns NOT_LOGGED_IN."""
    mock_get_username.return_value = (False, None)
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page
    mock_p_instance = AsyncMock()
    mock_p_instance.chromium.launch_persistent_context.return_value = mock_context
    mock_playwright.return_value.__aenter__.return_value = mock_p_instance

    verifier = AccountVerifier()
    verifier.expected_username = "srinjoysinha32820"

    status, username, msg = await verifier.verify_identity(headless=True)
    assert status == VerificationStatus.NOT_LOGGED_IN
    assert username is None
    assert "No authenticated LeetCode session found" in msg
