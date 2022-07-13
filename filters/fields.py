from pydantic import BaseModel, Field

from sqlalchemy.orm.attributes import InstrumentedAttribute
from datetime import date, datetime, time
from typing import List, Optional, Type


class FieldFilterBase(BaseModel):
    pass


class BooleanFilter(FieldFilterBase):
    is_: Optional[bool] = Field(None, alias="is")


class StringFilter(FieldFilterBase):
    eq: Optional[str]
    like: Optional[str]
    not_like: Optional[str]
    ilike: Optional[str]
    not_ilike: Optional[str]
    in_: Optional[List[str]] = Field(None, alias="in")
    not_in: Optional[List[str]]
    contains: Optional[str]
    startsWith: Optional[str]
    endsWith: Optional[str]
    neq: Optional[str]


class NumberFilter(FieldFilterBase):
    eq: Optional[float]
    ge: Optional[float]
    gt: Optional[float]
    le: Optional[float]
    lt: Optional[float]
    contains: Optional[str]
    between: Optional[List[float]] = Field(None, max_items=2, min_items=2)
    in_: Optional[List[float]] = Field(None, alias="in")
    not_in: Optional[List[float]]
    neq: Optional[float]
    is_: Optional[float] = Field(None, alias="is")


class DateTimeFilter(FieldFilterBase):
    eq: Optional[datetime]
    ge: Optional[datetime]
    gt: Optional[datetime]
    le: Optional[datetime]
    lt: Optional[datetime]
    between: Optional[List[datetime]] = Field(None, max_items=2, min_items=2)
    in_: Optional[List[datetime]] = Field(None, alias="in")
    not_in: Optional[List[datetime]]
    neq: Optional[datetime]
    is_: Optional[datetime] = Field(None, alias="is")


class TimeFilter(FieldFilterBase):
    eq: Optional[time]
    ge: Optional[time]
    gt: Optional[time]
    le: Optional[time]
    lt: Optional[time]
    between: Optional[List[time]] = Field(None, max_items=2, min_items=2)
    in_: Optional[List[time]] = Field(None, alias="in")
    not_in: Optional[List[time]]
    neq: Optional[time]
    is_: Optional[time] = Field(None, alias="is")


class DateFilter(FieldFilterBase):
    eq: Optional[date]
    ge: Optional[date]
    gt: Optional[date]
    le: Optional[date]
    lt: Optional[date]
    between: Optional[List[date]] = Field(None, max_items=2, min_items=2)
    in_: Optional[List[date]] = Field(None, alias="in")
    not_in: Optional[List[date]]
    neq: Optional[date]
    is_: Optional[date] = Field(None, alias="is")


class HasFilter(FieldFilterBase):
    pass


class AnyFilter(FieldFilterBase):
    pass
