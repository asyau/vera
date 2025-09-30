"""
API Gateway implementation for microservices routing
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)
security = HTTPBearer()


class APIGateway:
    """
    API Gateway for routing requests to appropriate microservices
    Handles authentication, authorization, rate limiting, and load balancing
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_middleware()
        self.setup_error_handlers()

    def setup_middleware(self):
        """Setup middleware for CORS, authentication, etc."""

        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://localhost:8080",
                "https://localhost:8080",
                "http://127.0.0.1:8080",
                "https://127.0.0.1:8080",
                "http://localhost:8081",
                "https://localhost:8081",
                "http://127.0.0.1:8081",
                "https://127.0.0.1:8081",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.utcnow()

            # Log request
            logger.info(f"Request: {request.method} {request.url}")

            response = await call_next(request)

            # Log response
            process_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Response: {response.status_code} - {process_time:.3f}s")

            return response

    def setup_error_handlers(self):
        """Setup global error handlers"""

        @self.app.exception_handler(AuthenticationError)
        async def authentication_error_handler(
            request: Request, exc: AuthenticationError
        ):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": exc.message,
                    "error_code": exc.error_code,
                    "details": exc.details,
                },
            )

        @self.app.exception_handler(AuthorizationError)
        async def authorization_error_handler(
            request: Request, exc: AuthorizationError
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": exc.message,
                    "error_code": exc.error_code,
                    "details": exc.details,
                },
            )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail, "error_code": "HTTP_ERROR"},
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {str(exc)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                },
            )


class AuthenticationMiddleware:
    """Middleware for handling JWT authentication"""

    @staticmethod
    def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> Dict[str, Any]:
        """Verify JWT token and return user info"""

        try:
            token = credentials.credentials
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )

            # Check token expiration
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                raise AuthenticationError("Token expired", error_code="TOKEN_EXPIRED")

            return payload

        except jwt.InvalidTokenError as e:
            raise AuthenticationError("Invalid token", error_code="INVALID_TOKEN")
        except Exception as e:
            raise AuthenticationError("Authentication failed", error_code="AUTH_FAILED")

    @staticmethod
    def get_current_user_id(
        token_payload: Dict[str, Any] = Depends(verify_token)
    ) -> str:
        """Extract user ID from token payload"""
        user_id = token_payload.get("user_id")
        if not user_id:
            raise AuthenticationError(
                "Invalid token payload", error_code="INVALID_TOKEN_PAYLOAD"
            )
        return user_id

    @staticmethod
    def require_role(required_role: str):
        """Dependency factory for role-based authorization"""

        def role_checker(
            token_payload: Dict[str, Any] = Depends(
                AuthenticationMiddleware.verify_token
            )
        ) -> Dict[str, Any]:
            user_role = token_payload.get("role")
            if user_role != required_role:
                raise AuthorizationError(
                    f"Required role: {required_role}", error_code="INSUFFICIENT_ROLE"
                )
            return token_payload

        return role_checker

    @staticmethod
    def require_any_role(required_roles: list):
        """Dependency factory for multiple role authorization"""

        def role_checker(
            token_payload: Dict[str, Any] = Depends(
                AuthenticationMiddleware.verify_token
            )
        ) -> Dict[str, Any]:
            user_role = token_payload.get("role")
            if user_role not in required_roles:
                raise AuthorizationError(
                    f"Required roles: {required_roles}", error_code="INSUFFICIENT_ROLE"
                )
            return token_payload

        return role_checker


class ServiceRouter:
    """Router for directing requests to appropriate microservices"""

    def __init__(self):
        self.service_registry = {
            "user_management": {
                "host": "localhost",
                "port": 8001,
                "health_endpoint": "/health",
            },
            "task_management": {
                "host": "localhost",
                "port": 8002,
                "health_endpoint": "/health",
            },
            "communication": {
                "host": "localhost",
                "port": 8003,
                "health_endpoint": "/health",
            },
            "notification": {
                "host": "localhost",
                "port": 8004,
                "health_endpoint": "/health",
            },
            "file_management": {
                "host": "localhost",
                "port": 8005,
                "health_endpoint": "/health",
            },
            "ai_orchestration": {
                "host": "localhost",
                "port": 8006,
                "health_endpoint": "/health",
            },
        }

    def get_service_url(self, service_name: str) -> str:
        """Get the URL for a specific service"""
        service = self.service_registry.get(service_name)
        if not service:
            raise HTTPException(
                status_code=404, detail=f"Service {service_name} not found"
            )

        return f"http://{service['host']}:{service['port']}"

    def route_request(self, service_name: str, path: str, method: str = "GET") -> str:
        """Route request to appropriate service"""
        base_url = self.get_service_url(service_name)
        return f"{base_url}{path}"

    async def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            service = self.service_registry.get(service_name)
            if not service:
                return False

            # TODO: Implement actual health check HTTP request
            # For now, return True
            return True

        except Exception:
            return False

    async def get_healthy_services(self) -> Dict[str, bool]:
        """Get health status of all services"""
        health_status = {}

        for service_name in self.service_registry:
            health_status[service_name] = await self.check_service_health(service_name)

        return health_status


class LoadBalancer:
    """Simple load balancer for service instances"""

    def __init__(self):
        self.service_instances = {}
        self.current_instance = {}

    def add_service_instance(self, service_name: str, host: str, port: int):
        """Add a service instance"""
        if service_name not in self.service_instances:
            self.service_instances[service_name] = []
            self.current_instance[service_name] = 0

        self.service_instances[service_name].append(
            {"host": host, "port": port, "healthy": True}
        )

    def get_next_instance(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get next healthy instance using round-robin"""
        instances = self.service_instances.get(service_name, [])
        healthy_instances = [i for i in instances if i["healthy"]]

        if not healthy_instances:
            return None

        # Round-robin selection
        current_idx = self.current_instance.get(service_name, 0)
        instance = healthy_instances[current_idx % len(healthy_instances)]

        self.current_instance[service_name] = (current_idx + 1) % len(healthy_instances)

        return instance

    def mark_instance_unhealthy(self, service_name: str, host: str, port: int):
        """Mark a service instance as unhealthy"""
        instances = self.service_instances.get(service_name, [])
        for instance in instances:
            if instance["host"] == host and instance["port"] == port:
                instance["healthy"] = False
                break


# Global instances
service_router = ServiceRouter()
load_balancer = LoadBalancer()
