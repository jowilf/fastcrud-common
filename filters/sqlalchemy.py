from pydantic import BaseModel, Field

from sqlalchemy import and_, false, not_, or_, true
from sqlalchemy.orm.attributes import InstrumentedAttribute
from datetime import date, datetime, time
from typing import List, Optional, Type

from common.filters.base import BaseModelFilter
from common.filters.fields import AnyFilter, FieldFilterBase, HasFilter


class SQLAlchemyModelFilter(BaseModelFilter):
    __cls__ = None

    def _exp_from(self, field_filter: FieldFilterBase, p: InstrumentedAttribute):
        values = []
        for field in field_filter.__fields_set__:
            if field == "eq":
                values.append(p == getattr(field_filter, field))
            if field == "ge":
                values.append(p >= getattr(field_filter, field))
            if field == "gt":
                values.append(p > getattr(field_filter, field))
            if field == "between":
                values.append(p.between(*getattr(field_filter, field)))
            elif field == "le":
                values.append(p <= getattr(field_filter, field))
            elif field == "lt":
                values.append(p < getattr(field_filter, field))
            if field == "like":
                values.append(p.like(getattr(field_filter, field)))
            if field == "not_like":
                values.append(p.not_like(getattr(field_filter, field)))
            if field == "ilike":
                values.append(p.ilike(getattr(field_filter, field)))
            if field == "not_ilike":
                values.append(p.not_ilike(getattr(field_filter, field)))
            elif field == "in_":
                values.append(p.in_(getattr(field_filter, field)))
            elif field == "not_in":
                values.append(p.not_in(getattr(field_filter, field)))
            elif field == "contains":
                values.append(p.contains(getattr(field_filter, field)))
            elif field == "startsWith":
                values.append(p.startswith(getattr(field_filter, field)))
            elif field == "endsWith":
                values.append(p.endswith(getattr(field_filter, field)))
            elif field == "neq":
                values.append(p != getattr(field_filter, field))
            if field == "is_":
                values.append(p.is_(getattr(field_filter, field)))
        if len(values) == 1:
            return values[0]
        return and_(*values)

    def to_query(self):
        filters = []
        for field in self.__fields_set__:
            attr = getattr(self, field)
            if field == "or_":
                filters.append(or_(*[v.to_query() for v in attr]))
            elif field == "and_":
                filters.append(and_(*[v.to_query() for v in attr]))
            elif field == "not_":
                filters.append(not_(attr.to_query()))
            else:
                p: InstrumentedAttribute = getattr(self.__cls__, field)
                assert (
                    type(p) is InstrumentedAttribute
                ), f"{self.__cls__} is Invalid SQLAlchemy model"
                if isinstance(attr, FieldFilterBase):
                    filters.append(self._exp_from(attr, p))
                elif isinstance(attr, bool):
                    filters.append((p == true()) if attr else (p == false()))
                elif isinstance(attr, HasFilter):
                    filters.append(p.has(attr.to_query()))
                elif isinstance(attr, AnyFilter):
                    filters.append(p.any(attr.to_query()))
                else:
                    filters.append(p == attr)
        if len(filters) == 1:
            return filters[0]
        return and_(*filters)
