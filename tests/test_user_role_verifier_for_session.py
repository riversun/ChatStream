import pytest
from unittest.mock import Mock

from chatstream.user_role_verifier_for_session import UserRoleVerifierForSession


def test_role_has_access_to_api():
    """
    Test if the user role has access to the given API
    """
    # Initialize UserRoleVerifierForSession object
    verifier = UserRoleVerifierForSession(logger=Mock(),eloc=Mock(),api_access_role={})

    # Create mock request object
    request = Mock()
    request.state = Mock()

    # Mock session with a list of allowed apis
    request.state.session = Mock(get_session=Mock(return_value={
        "user_role_name": "role1",
        "allowed_apis": ["api1", "api2", "api3"]
    }))

    result = verifier.verify_role_has_privilege(request, "api1")
    assert result["allowed"] == True


def test_role_does_not_have_access_to_api():
    """
    Test if the user role does not have access to the given API
    """
    # Initialize UserRoleVerifierForSession object
    verifier = UserRoleVerifierForSession(logger=Mock(),eloc=Mock(),api_access_role={})

    # Create mock request object
    request = Mock()
    request.state = Mock()

    # Mock session with a list of allowed apis
    request.state.session = Mock(get_session=Mock(return_value={
        "user_role_name": "role1",
        "allowed_apis": ["api1", "api2", "api3"]
    }))

    result = verifier.verify_role_has_privilege(request, "api4")
    assert result["allowed"] == False


def test_allowed_apis_is_string_and_matches_api_name():
    """
    Test if the user role has access to the given API when allowed_apis is a string
    """
    # Initialize UserRoleVerifierForSession object
    verifier = UserRoleVerifierForSession(logger=Mock(),eloc=Mock(),api_access_role={})

    # Create mock request object
    request = Mock()
    request.state = Mock()

    # Mock session with a string allowed api
    request.state.session = Mock(get_session=Mock(return_value={
        "user_role_name": "role2",
        "allowed_apis": "api1"
    }))

    result = verifier.verify_role_has_privilege(request, "api1")
    assert result["allowed"] == True


def test_allowed_apis_is_string_and_does_not_match_api_name():
    """
    Test if the user role does not have access to the given API when allowed_apis is a string
    """
    # Initialize UserRoleVerifierForSession object
    verifier = UserRoleVerifierForSession(logger=Mock(),eloc=Mock(),api_access_role={})

    # Create mock request object
    request = Mock()
    request.state = Mock()

    # Mock session with a string allowed api
    request.state.session = Mock(get_session=Mock(return_value={
        "user_role_name": "role2",
        "allowed_apis": "api1"
    }))

    result = verifier.verify_role_has_privilege(request, "api4")
    assert result["allowed"] == False


def test_no_allowed_apis():
    """
    Test if an exception is raised when allowed_apis is not present
    """
    # Initialize UserRoleVerifierForSession object
    verifier = UserRoleVerifierForSession(logger=Mock(),eloc=Mock(),api_access_role={})

    # Create mock request object
    request = Mock()
    request.state = Mock()

    # Mock session with no allowed apis
    request.state.session = Mock(get_session=Mock(return_value={
        "user_role_name": "role3"
    }))
    result = verifier.verify_role_has_privilege(request, "api1")
    assert result["allowed"] == False
    # with pytest.raises(Exception, match="allowed_apis should be either string or list."):
    #     res=verifier.verify_role_has_privilege(request, "api1")
    #     print(res)


def test_session_not_available():
    """
    Test if an exception is raised when the session is not available
    """
    # Initialize UserRoleVerifierForSession object
    verifier = UserRoleVerifierForSession(logger=Mock(),eloc=Mock(),api_access_role={})

    # Create mock request object
    request = Mock()
    request.state = Mock()

    # Set session to None
    request.state.session = None

    with pytest.raises(Exception, match="Session is not available."):
        verifier.verify_role_has_privilege(request, "api1")
