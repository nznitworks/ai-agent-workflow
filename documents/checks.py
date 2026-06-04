"""Schema models for network diagnostic endpoints."""

from pydantic import BaseModel, Field, HttpUrl


class HttpCheckRequest(BaseModel):
    """Input payload for HTTP checks."""

    url: HttpUrl
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=30.0)
    expected_status: int = Field(default=200, ge=100, le=599)


class HttpCheckResponse(BaseModel):
    """Response payload for HTTP checks."""

    ok: bool
    url: str
    status_code: int | None = None
    latency_ms: float | None = None
    detail: str


class EgressUrlResult(BaseModel):
    """Per-URL reachability result for outbound namespace checks."""

    url: str
    ok: bool
    status_code: int | None = None
    latency_ms: float | None = None
    detail: str


class EgressCheckRequest(BaseModel):
    """Input payload for checking outbound access to external URLs."""

    urls: list[HttpUrl] = Field(min_length=1, max_length=50)
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=30.0)
    expected_status: int = Field(default=200, ge=100, le=599)


class EgressCheckResponse(BaseModel):
    """Aggregate response for outbound namespace URL access checks."""

    ok: bool
    total: int
    success_count: int
    failure_count: int
    results: list[EgressUrlResult]
    detail: str


class DnsCheckRequest(BaseModel):
    """Input payload for DNS checks."""

    hostname: str = Field(min_length=1, max_length=253)
    record_type: str = Field(default="A", pattern="^(A|AAAA)$")


class DnsCheckResponse(BaseModel):
    """Response payload for DNS checks."""

    ok: bool
    hostname: str
    record_type: str
    addresses: list[str] = Field(default_factory=list)
    detail: str


class TcpCheckRequest(BaseModel):
    """Input payload for TCP checks."""

    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=30.0)


class TcpCheckResponse(BaseModel):
    """Response payload for TCP checks."""

    ok: bool
    host: str
    port: int
    latency_ms: float | None = None
    detail: str
