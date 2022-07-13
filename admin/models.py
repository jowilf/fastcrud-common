from abc import abstractmethod
import json
from typing import Any, Dict, List

from loguru import logger

from common.admin.helpers import slugify_class_name
from common.admin.fields import (
    DateTimeField,
    FileField,
    HasMany,
    ImageField,
    PhoneField,
    RelationField,
    StringField,
    BooleanField,
    TextField,
    EmailField,
    EnumField,
    DateField,
    TimeField,
    JSONField,
    NumberField,
)

from pydantic import BaseModel, EmailStr
from fastapi.datastructures import FormData


class AdminModel(BaseModel):
    def identity(self) -> str:
        return slugify_class_name(__class__.__name__)

    def get_name(self) -> str:
        return __class__.__name__

    @abstractmethod
    def datasource(self) -> str:
        pass

    def _export_columns(self) -> List[int]:
        return list(
            range(
                2,
                2+len(
                    list(
                        filter(
                            lambda f:not  getattr(self, f.name).exclude_from_list,
                            self.__fields__.values(),
                        )
                    )
                ),
            )
        )

    def search_columns(self) -> List[int]:
        columns, i = dict(), 0
        for field in self.__fields__.values():
            if (
                field.type_
                in [
                    DateTimeField,
                    PhoneField,
                    StringField,
                    BooleanField,
                    TextField,
                    EmailField,
                    EnumField,
                    DateField,
                    TimeField,
                    JSONField,
                    NumberField,
                ]
                and not getattr(self, field.name).is_array
            ):
                columns[i + 2] = field.name
            if not getattr(self, field.name).exclude_from_list:
                i += 1

        return columns

    def _extract_fields(self, form_data: FormData) -> Dict[str, Any]:
        data = dict()
        for field in self.__fields__.values():
            if not getattr(self, field.name).exclude_from_form:
                if (
                    field.type_ in [NumberField, EmailField, PhoneField]
                    and form_data.get(field.name) == ""
                ):
                    data[field.name] = None
                elif field.type_ == JSONField:
                    data[field.name] = json.loads(form_data.get(field.name))
                elif getattr(self, field.name).is_array:
                    data[field.name] = form_data.getlist(field.name)
                else:
                    data[field.name] = form_data.get(field.name)
                if field.type_ in [FileField, ImageField]:
                    data[f"_keep_old_{field.name}"] = form_data.get(
                        f"_keep_old_{field.name}"
                    )
        logger.info(data)
        return data


class AdminModelManager:
    @abstractmethod
    def find_by_id(self, model: AdminModel, id):
        pass

    @abstractmethod
    def create(self, model: AdminModel, form_data: FormData):
        pass

    @abstractmethod
    def edit(self, model: AdminModel, form_data: FormData, id):
        pass
