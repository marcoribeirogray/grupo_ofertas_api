from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class IntegrationBase(BaseModel):
    label: str
    data: dict[str, Any] = Field(default_factory=dict)


class IntegrationCreate(IntegrationBase):
    provider: str


class IntegrationUpdate(IntegrationBase):
    pass


class IntegrationRead(IntegrationBase):
    id: int
    provider: str

    class Config:
        from_attributes = True


class TemplateBase(BaseModel):
    name: str
    slug: str
    body: str
    description: Optional[str] = None
    is_default: bool = False


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    body: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None


class TemplateRead(TemplateBase):
    id: int

    class Config:
        from_attributes = True


class RuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: dict[str, Any] = Field(default_factory=dict)
    actions: dict[str, Any] = Field(default_factory=dict)


class RuleUpdate(BaseModel):
    description: Optional[str] = None
    conditions: Optional[dict[str, Any]] = None
    actions: Optional[dict[str, Any]] = None


class RuleRead(RuleBase):
    id: int

    class Config:
        from_attributes = True


class OfferPreviewRequest(BaseModel):
    url: str
    store: Optional[str] = None
    coupon: Optional[str] = None
    template_slug: Optional[str] = None
    overrides: dict[str, Any] = Field(default_factory=dict)


class OfferPreviewResponse(BaseModel):
    title: str
    store: str
    affiliate_url: str
    short_url: str
    price: Optional[str]
    price_original: Optional[str]
    benefits: list[str] = Field(default_factory=list)
    image: Optional[str]
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
