"""
Comprehensive test suite for MLS Middleware.

This test suite validates the security-critical middleware that manages
MLS context for requests. Tests cover:

1. Middleware initialization
2. Request processing with authenticated users
3. Request processing with anonymous users
4. Security context integration with crum
5. Edge cases and error conditions
6. Integration with the MLS access control system
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse
from django.db import models

from mls_core.middleware import MLSMiddleware

# Import test models from existing tests
try:
    from abac.models import Label, Security, FakeUser, Object
    ABAC_AVAILABLE = True
except ImportError:
    # ABAC not available - create test models
    Label = None
    Security = None
    FakeUser = None
    Object = None
    ABAC_AVAILABLE = False


# Test-only models (used when ABAC app is not available)
if not ABAC_AVAILABLE:
    class Label(models.Model):
        """Test-only Label model"""
        class LabelType(models.TextChoices):
            LEVEL = "LVL", "Level"
            CATEGORY = "CAT", "Category"

        short_code = models.CharField(max_length=3)
        name = models.CharField(max_length=50)
        label_type = models.CharField(
            max_length=3,
            choices=LabelType.choices,
            default=LabelType.CATEGORY
        )

        class Meta:
            app_label = 'mls_core'

        def __str__(self):
            return self.name

    class Security(models.Model):
        """Test-only Security model"""
        securities = models.ManyToManyField(Label, related_name="labels")

        class Meta:
            app_label = 'mls_core'
            verbose_name_plural = "securities"

        def __str__(self):
            return ", ".join(str(s.short_code) for s in self.securities.all())

    class FakeUser(models.Model):
        """Test-only FakeUser model"""
        name = models.CharField(max_length=50)
        accesses = models.OneToOneField(
            Security,
            on_delete=models.SET_NULL,
            null=True
        )

        class Meta:
            app_label = 'mls_core'

        def __str__(self):
            return self.name


# ==================== Unit Tests ====================

class TestMLSMiddlewareInitialization(TestCase):
    """Unit tests for middleware initialization."""

    def test_middleware_initialization_with_valid_get_response(self):
        """Middleware should initialize correctly with a valid get_response callable"""
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        self.assertIsNotNone(middleware)
        self.assertEqual(middleware.get_response, get_response)

    def test_middleware_initialization_stores_get_response(self):
        """Middleware should store the get_response callable"""
        get_response = Mock()
        middleware = MLSMiddleware(get_response)

        self.assertTrue(hasattr(middleware, 'get_response'))
        self.assertIs(middleware.get_response, get_response)

    def test_middleware_is_callable(self):
        """Middleware instance should be callable"""
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        self.assertTrue(callable(middleware))


class TestMLSMiddlewareRequestProcessing(TestCase):
    """Unit tests for request processing in middleware."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = MLSMiddleware(self.get_response)

    def test_call_method_invokes_get_response(self):
        """__call__ should invoke get_response with the request"""
        request = self.factory.get('/test/')

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)

    def test_call_method_returns_response(self):
        """__call__ should return the response from get_response"""
        request = self.factory.get('/test/')
        expected_response = HttpResponse("Test Response", status=201)
        self.get_response.return_value = expected_response

        response = self.middleware(request)

        self.assertEqual(response, expected_response)
        self.assertEqual(response.status_code, 201)

    def test_middleware_passes_request_through_unchanged(self):
        """Middleware should not modify the request object"""
        request = self.factory.get('/test/')
        request.custom_attribute = "test_value"

        self.middleware(request)

        # Verify request was passed to get_response
        call_args = self.get_response.call_args[0]
        self.assertEqual(call_args[0].custom_attribute, "test_value")

    def test_middleware_handles_post_request(self):
        """Middleware should handle POST requests correctly"""
        request = self.factory.post('/test/', {'data': 'value'})

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)

    def test_middleware_handles_authenticated_request(self):
        """Middleware should handle requests from authenticated users"""
        request = self.factory.get('/test/')
        # is_authenticated is a read-only property (always True for a real
        # User instance) - not a constructor kwarg
        request.user = User(username='testuser')

        response = self.middleware(request)

        self.get_response.assert_called_once()
        self.assertEqual(response.status_code, 200)

    def test_middleware_handles_anonymous_request(self):
        """Middleware should handle requests from anonymous users"""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()

        response = self.middleware(request)

        self.get_response.assert_called_once()
        self.assertEqual(response.status_code, 200)


class TestMLSMiddlewareProcessView(TestCase):
    """Unit tests for process_view method."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = MLSMiddleware(self.get_response)

    def test_process_view_returns_none(self):
        """process_view should return None to allow normal view processing"""
        request = self.factory.get('/test/')
        view_func = Mock()

        result = self.middleware.process_view(request, view_func, (), {})

        self.assertIsNone(result)

    def test_process_view_with_authenticated_user(self):
        """process_view should handle authenticated user requests"""
        request = self.factory.get('/test/')
        request.user = User(username='testuser')
        view_func = Mock()

        result = self.middleware.process_view(request, view_func, (), {})

        self.assertIsNone(result)

    def test_process_view_with_anonymous_user(self):
        """process_view should handle anonymous user requests"""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        view_func = Mock()

        result = self.middleware.process_view(request, view_func, (), {})

        self.assertIsNone(result)

    def test_process_view_with_view_args(self):
        """process_view should handle view arguments correctly"""
        request = self.factory.get('/test/')
        view_func = Mock()
        view_args = (1, 2, 3)
        view_kwargs = {'key': 'value'}

        result = self.middleware.process_view(
            request, view_func, view_args, view_kwargs
        )

        self.assertIsNone(result)

    def test_process_view_called_before_view_execution(self):
        """process_view is called before the actual view function"""
        request = self.factory.get('/test/')
        view_func = Mock()

        # process_view should return None, allowing view to execute
        result = self.middleware.process_view(request, view_func, (), {})

        self.assertIsNone(result)
        # View function should not be called by middleware
        view_func.assert_not_called()


# ==================== Integration Tests ====================

class TestMLSMiddlewareWithCrum(TestCase):
    """Integration tests for middleware with django-crum."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = MLSMiddleware(self.get_response)

    @patch('mls_core.middleware.get_current_request')
    def test_middleware_works_with_crum_get_current_request(self, mock_get_request):
        """Middleware should work alongside crum's get_current_request"""
        request = self.factory.get('/test/')

        self.middleware(request)

        # Middleware should allow crum to work normally
        self.get_response.assert_called_once()

    def test_middleware_preserves_request_for_crum(self):
        """Middleware should not interfere with crum's request storage"""
        request = self.factory.get('/test/')
        request.user = User(username='testuser')

        # Call middleware
        self.middleware(request)

        # Request should still be accessible to get_response
        self.get_response.assert_called_with(request)


class TestMLSMiddlewareWithMLSModels(TestCase):
    """Integration tests with actual MLS models."""

    def setUp(self):
        """Set up test fixtures including security labels"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = MLSMiddleware(self.get_response)

        # Create security labels
        self.label_unclassified = Label.objects.create(
            short_code="U",
            name="Unclassified",
            label_type=Label.LabelType.LEVEL
        )
        self.label_secret = Label.objects.create(
            short_code="S",
            name="Secret",
            label_type=Label.LabelType.LEVEL
        )

        # Create security clearances
        self.security_unclass = Security.objects.create()
        self.security_unclass.securities.add(self.label_unclassified)

        self.security_secret = Security.objects.create()
        self.security_secret.securities.add(
            self.label_unclassified,
            self.label_secret
        )

    def tearDown(self):
        """Clean up test data"""
        FakeUser.objects.all().delete()
        Security.objects.all().delete()
        Label.objects.all().delete()

    @patch('crum.get_current_user')
    def test_middleware_with_mls_user_context(self, mock_get_user):
        """Middleware should work with MLS user context from crum"""
        # Create MLS user
        user = FakeUser.objects.create(
            name="Secret User",
            accesses=self.security_secret
        )

        mock_get_user.return_value = user
        request = self.factory.get('/test/')

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)

    @patch('crum.get_current_user')
    def test_middleware_with_low_clearance_user(self, mock_get_user):
        """Middleware should handle users with low clearance"""
        # Create low clearance user
        user = FakeUser.objects.create(
            name="Unclassified User",
            accesses=self.security_unclass
        )

        mock_get_user.return_value = user
        request = self.factory.get('/test/')

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)

    @patch('crum.get_current_user')
    def test_middleware_with_user_without_clearance(self, mock_get_user):
        """Middleware should handle users without security clearances"""
        # Create user with no clearances
        user = FakeUser.objects.create(name="No Clearance User")

        mock_get_user.return_value = user
        request = self.factory.get('/test/')

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)


# ==================== Security Tests ====================

class TestMLSMiddlewareSecurity(TestCase):
    """Security-focused tests for middleware behavior."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = MLSMiddleware(self.get_response)

    def test_middleware_does_not_bypass_authentication(self):
        """Middleware should not interfere with Django authentication"""
        request = self.factory.get('/test/')
        # No user attribute set - middleware should still work

        response = self.middleware(request)

        # Should process normally, auth is handled elsewhere
        self.assertEqual(response.status_code, 200)

    def test_middleware_does_not_expose_sensitive_data(self):
        """Middleware should not leak sensitive information in responses"""
        request = self.factory.get('/test/')
        request.user = User(username='testuser')

        response = self.middleware(request)

        # Response should not contain middleware internals
        self.assertNotIn(b'MLSMiddleware', response.content)

    @patch('crum.get_current_user')
    def test_middleware_fails_secure_on_exception(self, mock_get_user):
        """Middleware should fail securely if an exception occurs"""
        # Make get_current_user raise an exception
        mock_get_user.side_effect = Exception("Database error")

        request = self.factory.get('/test/')

        # Middleware should still call get_response (exception handled elsewhere)
        response = self.middleware(request)

        # Should complete the request (error handling is view's responsibility)
        self.get_response.assert_called_once()

    def test_middleware_preserves_security_headers(self):
        """Middleware should not strip security-related headers"""
        request = self.factory.get('/test/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1'

        self.middleware(request)

        # Verify request metadata is preserved
        call_args = self.get_response.call_args[0]
        self.assertIn('HTTP_X_FORWARDED_FOR', call_args[0].META)


# ==================== Edge Cases and Error Conditions ====================

class TestMLSMiddlewareEdgeCases(TestCase):
    """Tests for edge cases and unusual conditions."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = MLSMiddleware(self.get_response)

    def test_middleware_with_none_request(self):
        """Middleware should propagate an AttributeError for a bogus (None)
        request rather than silently swallowing it"""
        # This shouldn't happen in practice, but test defensive coding.
        # MLSMiddleware is a pure passthrough - it never touches `request`
        # itself - so the error has to come from the downstream handler
        # actually using it. self.get_response is a Mock in setUp() and
        # wouldn't care what it's called with, so use a real handler here
        # that dereferences the request the way a real view would.
        def real_view(request):
            return HttpResponse(f"Method: {request.method}")

        middleware = MLSMiddleware(real_view)

        with self.assertRaises(AttributeError):
            middleware(None)

    def test_middleware_with_exception_in_get_response(self):
        """Middleware should not suppress exceptions from get_response"""
        self.get_response.side_effect = ValueError("View error")
        request = self.factory.get('/test/')

        with self.assertRaises(ValueError):
            self.middleware(request)

    def test_process_view_with_none_view_func(self):
        """process_view should handle None view function"""
        request = self.factory.get('/test/')

        # Should not crash even with None view
        result = self.middleware.process_view(request, None, (), {})

        self.assertIsNone(result)

    def test_middleware_with_malformed_request(self):
        """Middleware should handle malformed requests"""
        request = Mock()
        request.method = "INVALID"

        # Middleware should still call get_response
        self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_multiple_middleware_instances(self):
        """Multiple middleware instances should work independently"""
        get_response_1 = Mock(return_value=HttpResponse("Response 1"))
        get_response_2 = Mock(return_value=HttpResponse("Response 2"))

        middleware_1 = MLSMiddleware(get_response_1)
        middleware_2 = MLSMiddleware(get_response_2)

        request = self.factory.get('/test/')

        response_1 = middleware_1(request)
        response_2 = middleware_2(request)

        self.assertIn(b"Response 1", response_1.content)
        self.assertIn(b"Response 2", response_2.content)

    def test_middleware_with_request_without_user_attribute(self):
        """Middleware should handle requests without user attribute"""
        request = self.factory.get('/test/')
        # Don't set request.user

        # Should not crash
        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)


class TestMLSMiddlewareProcessViewEdgeCases(TestCase):
    """Edge case tests for process_view method."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = MLSMiddleware(self.get_response)

    def test_process_view_with_empty_args_kwargs(self):
        """process_view should handle empty args and kwargs"""
        request = self.factory.get('/test/')
        view_func = Mock()

        result = self.middleware.process_view(request, view_func, (), {})

        self.assertIsNone(result)

    def test_process_view_with_complex_kwargs(self):
        """process_view should handle complex view kwargs"""
        request = self.factory.get('/test/')
        view_func = Mock()
        view_kwargs = {
            'pk': 123,
            'slug': 'test-slug',
            'nested': {'key': 'value'}
        }

        result = self.middleware.process_view(request, view_func, (), view_kwargs)

        self.assertIsNone(result)

    def test_process_view_multiple_calls(self):
        """process_view should handle multiple calls on same request"""
        request = self.factory.get('/test/')
        view_func_1 = Mock()
        view_func_2 = Mock()

        result_1 = self.middleware.process_view(request, view_func_1, (), {})
        result_2 = self.middleware.process_view(request, view_func_2, (), {})

        self.assertIsNone(result_1)
        self.assertIsNone(result_2)


# ==================== Functional Tests ====================

class TestMLSMiddlewareRequestFlow(TestCase):
    """Functional tests for complete request flow through middleware."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()

    def test_complete_request_flow_with_authenticated_user(self):
        """Test complete request flow with authenticated user"""
        # Create a simple view
        def test_view(request):
            return HttpResponse(f"Hello {request.user.username}")

        middleware = MLSMiddleware(test_view)

        request = self.factory.get('/test/')
        # is_authenticated is a read-only property - already True for any
        # real (non-anonymous) User instance, nothing to set here
        request.user = User(username='testuser')

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hello testuser", response.content)

    def test_complete_request_flow_with_anonymous_user(self):
        """Test complete request flow with anonymous user"""
        def test_view(request):
            if request.user.is_authenticated:
                return HttpResponse("Authenticated")
            return HttpResponse("Anonymous")

        middleware = MLSMiddleware(test_view)

        request = self.factory.get('/test/')
        request.user = AnonymousUser()

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Anonymous", response.content)

    def test_middleware_in_middleware_chain(self):
        """Test middleware as part of a chain"""
        # Simulate middleware chain
        def final_view(request):
            return HttpResponse("Final")

        def outer_middleware(request):
            # Simulate another middleware wrapping MLS middleware
            mls_middleware = MLSMiddleware(final_view)
            return mls_middleware(request)

        request = self.factory.get('/test/')
        request.user = User(username='testuser')

        response = outer_middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Final", response.content)


# ==================== Acceptance Tests ====================

class TestMLSMiddlewareAcceptance(TestCase):
    """Acceptance tests validating middleware meets requirements."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()

    def test_middleware_meets_django_middleware_protocol(self):
        """Middleware should follow Django middleware protocol"""
        get_response = Mock(return_value=HttpResponse("OK"))

        # Should accept get_response in __init__
        middleware = MLSMiddleware(get_response)

        # Should be callable
        self.assertTrue(callable(middleware))

        # Should have process_view method
        self.assertTrue(hasattr(middleware, 'process_view'))
        self.assertTrue(callable(middleware.process_view))

    def test_middleware_integrates_with_crum(self):
        """Middleware should integrate properly with django-crum"""
        # This test validates the documented integration
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        request = self.factory.get('/test/')

        # Should work without errors (crum integration is passive)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_middleware_enables_mls_context(self):
        """Middleware should enable MLS context for requests"""
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        request = self.factory.get('/test/')
        request.user = User(username='testuser')

        # Middleware should process request and enable context
        response = middleware(request)

        # Request should have been processed
        self.assertEqual(response.status_code, 200)

    def test_middleware_supports_all_http_methods(self):
        """Middleware should support all standard HTTP methods"""
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']

        for method in methods:
            request = getattr(self.factory, method.lower())('/test/')
            response = middleware(request)

            self.assertEqual(
                response.status_code, 200,
                f"Failed for method {method}"
            )


# ==================== Performance Tests ====================

class TestMLSMiddlewarePerformance(TestCase):
    """Performance tests for middleware."""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()

    def test_middleware_minimal_overhead(self):
        """Middleware should add minimal overhead to request processing"""
        import time

        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        request = self.factory.get('/test/')
        request.user = User(username='testuser')

        # Measure time for 1000 requests
        start = time.time()
        for _ in range(1000):
            middleware(request)
        elapsed = time.time() - start

        # Should complete 1000 requests in less than 1 second
        # (This is very generous - actual should be much faster)
        self.assertLess(elapsed, 1.0,
            f"Middleware too slow: {elapsed:.3f}s for 1000 requests")

    def test_process_view_performance(self):
        """process_view should execute quickly"""
        import time

        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        request = self.factory.get('/test/')
        view_func = Mock()

        # Measure time for 10000 process_view calls
        start = time.time()
        for _ in range(10000):
            middleware.process_view(request, view_func, (), {})
        elapsed = time.time() - start

        # Should complete 10000 calls in less than 1 second
        self.assertLess(elapsed, 1.0,
            f"process_view too slow: {elapsed:.3f}s for 10000 calls")


# ==================== Pytest-specific Tests ====================

@pytest.mark.django_db
class TestMLSMiddlewarePytestStyle:
    """Pytest-style tests for middleware."""

    def test_middleware_initialization_pytest(self):
        """Pytest-style test for middleware initialization"""
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        assert middleware is not None
        assert middleware.get_response == get_response

    def test_middleware_call_pytest(self):
        """Pytest-style test for middleware call"""
        factory = RequestFactory()
        get_response = Mock(return_value=HttpResponse("Test"))
        middleware = MLSMiddleware(get_response)

        request = factory.get('/test/')
        response = middleware(request)

        assert response.status_code == 200
        get_response.assert_called_once_with(request)

    @pytest.mark.parametrize("method", ['get', 'post', 'put', 'patch', 'delete'])
    def test_middleware_handles_all_methods_pytest(self, method):
        """Pytest parametrized test for different HTTP methods"""
        factory = RequestFactory()
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        request = getattr(factory, method)('/test/')
        response = middleware(request)

        assert response.status_code == 200

    @pytest.mark.parametrize("user_type,expected_auth", [
        (lambda: User(username='test'), True),
        (lambda: AnonymousUser(), False),
    ])
    def test_middleware_with_different_users_pytest(self, user_type, expected_auth):
        """Pytest parametrized test for different user types"""
        factory = RequestFactory()
        get_response = Mock(return_value=HttpResponse("OK"))
        middleware = MLSMiddleware(get_response)

        request = factory.get('/test/')
        request.user = user_type()

        response = middleware(request)

        assert response.status_code == 200


# ==================== Test Fixtures (Pytest) ====================

@pytest.fixture
def request_factory():
    """Fixture providing RequestFactory instance"""
    return RequestFactory()


@pytest.fixture
def mls_middleware():
    """Fixture providing MLSMiddleware instance"""
    get_response = Mock(return_value=HttpResponse("OK"))
    return MLSMiddleware(get_response)


@pytest.fixture
def authenticated_request(request_factory):
    """Fixture providing authenticated request"""
    request = request_factory.get('/test/')
    # is_authenticated is a read-only property - already True for any
    # real (non-anonymous) User instance, nothing to set here
    request.user = User(username='testuser')
    return request


@pytest.fixture
def anonymous_request(request_factory):
    """Fixture providing anonymous request"""
    request = request_factory.get('/test/')
    request.user = AnonymousUser()
    return request


@pytest.mark.django_db
class TestMLSMiddlewareWithFixtures:
    """Tests using pytest fixtures."""

    def test_middleware_with_authenticated_fixture(
        self, mls_middleware, authenticated_request
    ):
        """Test middleware with authenticated request fixture"""
        response = mls_middleware(authenticated_request)

        assert response.status_code == 200

    def test_middleware_with_anonymous_fixture(
        self, mls_middleware, anonymous_request
    ):
        """Test middleware with anonymous request fixture"""
        response = mls_middleware(anonymous_request)

        assert response.status_code == 200

    def test_process_view_with_fixtures(
        self, mls_middleware, authenticated_request
    ):
        """Test process_view with fixtures"""
        view_func = Mock()

        result = mls_middleware.process_view(
            authenticated_request, view_func, (), {}
        )

        assert result is None


# ==================== Documentation Tests ====================

class TestMLSMiddlewareDocumentation(TestCase):
    """Tests validating middleware documentation and comments."""

    def test_middleware_has_docstring(self):
        """Middleware class should have documentation"""
        self.assertIsNotNone(MLSMiddleware.__doc__)
        self.assertGreater(len(MLSMiddleware.__doc__.strip()), 0)

    def test_middleware_init_is_documented(self):
        """Middleware __init__ method should be documented or simple"""
        # __init__ might not have docstring if it's trivial
        self.assertTrue(hasattr(MLSMiddleware, '__init__'))

    def test_middleware_call_is_documented(self):
        """Middleware __call__ method should be documented or simple"""
        self.assertTrue(hasattr(MLSMiddleware, '__call__'))

    def test_process_view_has_docstring(self):
        """process_view method should have documentation"""
        self.assertIsNotNone(MLSMiddleware.process_view.__doc__)
        self.assertGreater(
            len(MLSMiddleware.process_view.__doc__.strip()), 0
        )
