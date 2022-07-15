from abc import abstractmethod
import re
from typing import Any, List, Optional, Type
from fastapi import Depends, Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from jinja2 import pass_context
from loguru import logger
from pydantic import BaseModel
from sqlmodel import Session

from common.admin.models import AdminModel, AdminModelManager
from starlette.templating import Jinja2Templates
from starlette.datastructures import FormData
from starlette.status import HTTP_200_OK
from common.admin.helpers import get_file_icon


class ExportConfig(BaseModel):
    csv: bool = True
    excel: bool = True
    pdf: bool = True
    print: bool = True
    column_visibility: bool = True
    search_builder: bool = True


class Admin:
    models: List[AdminModel] = []

    def __init__(self, title: str, export_config: ExportConfig = ExportConfig()):
        self.export_config = export_config
        self.template = self._create_template(title)

    @abstractmethod
    def datasource(self, request: Request, model: AdminModel) -> str:
        pass

    @abstractmethod
    def file_url(self, request: Request, path: str) -> str:
        pass

    @abstractmethod
    def admin_url(self, request: Request) -> str:
        pass

    @abstractmethod
    def admin_url_for(
        self, request: Request, model: AdminModel, action: str, pk: str
    ) -> str:
        pass

    def _create_template(self, title: str):
        template = Jinja2Templates("common/templates")
        template.env.globals["admin_title"] = title
        template.env.globals["export_config"] = self.export_config
        template.env.globals["all_models"] = self.models
        template.env.filters["file_icon"] = get_file_icon
        template.env.filters[
            "to_model"
        ] = lambda identity: self._find_model_from_identity(identity)
        template.env.filters["field_title"] = lambda s: s.replace("_", " ").capitalize()

        @pass_context
        def ds(context: dict, model: AdminModel) -> str:
            return self.datasource(context["request"], model)

        @pass_context
        def file_url(context: dict, path: str) -> str:
            return self.file_url(context["request"], path)

        @pass_context
        def admin_url(context: dict) -> str:
            return self.admin_url(context["request"])

        @pass_context
        def admin_url_for(
            context: dict, model: AdminModel, action: str = "list", pk=None
        ) -> str:
            return self.admin_url_for(context["request"], model, action, pk)

        template.env.globals["file_url"] = file_url
        template.env.globals["admin_url"] = admin_url
        template.env.globals["admin_url_for"] = admin_url_for
        template.env.globals["ds"] = ds
        return template

    def register(self, model: AdminModel) -> None:
        self.models.append(model)

    def _find_model_from_identity(self, identity: str) -> Optional[AdminModel]:
        for model in self.models:
            if model.identity() == identity:
                return model

    async def _404(self, request: Request) -> Response:
        return self.template.TemplateResponse(
            "404.html",
            {"request": request},
        )

    async def _list(self, request: Request, model: AdminModel) -> Response:
        return self.template.TemplateResponse(
            "list.html",
            {"request": request, "model": model},
        )

    async def _show(
        self, request: Request, model: AdminModel, model_manager: AdminModelManager
    ) -> Response:
        id = request.query_params.get("pk")
        if id is None or model_manager.find_by_id(model, id) is None:
            return await self._404(request)
        return self.template.TemplateResponse(
            "show.html",
            {
                "request": request,
                "model": model,
                "value": model_manager.find_by_id(model, id),
            },
        )

    async def _create(
        self, request: Request, model: AdminModel, model_manager: AdminModelManager
    ) -> Response:
        if request.method == "GET":
            return self.template.TemplateResponse(
                "create.html",
                {
                    "request": request,
                    "model": model,
                },
            )
        elif request.method == "POST":
            form = await request.form()
            model_manager.create(model, form)
            return Response(status_code=HTTP_200_OK)

    async def _edit(
        self, request: Request, model: AdminModel, model_manager: AdminModelManager
    ) -> Response:
        id = request.query_params.get("pk")
        if id is None or model_manager.find_by_id(model, id) is None:
            return await self._404(request)
        if request.method == "GET":
            return self.template.TemplateResponse(
                "edit.html",
                {
                    "request": request,
                    "model": model,
                    "value": model_manager.find_by_id(model, id),
                },
            )
        elif request.method == "POST":
            form = await request.form()
            model_manager.edit(model, form, id)
            return Response(status_code=HTTP_200_OK)

    async def render_login(self, request: Request, error: Optional[str]= None) -> Response:
        return self.template.TemplateResponse(
            "login.html",
            {"request": request, "error": error},
        )

    async def render_dashboard(
        self,
        request: Request,
        model_identity: Optional[str],
        action: Optional[str],
        pk: Any,
        model_manager: AdminModelManager,
        login_required: bool = False,
    ) -> Response:
        if login_required and not self.is_authenticated(request):
            return await self._login(request)
        model = self._find_model_from_identity(model_identity)
        if model is not None:
            if action == "list":
                return await self._list(request, model)
            elif action == "show":
                return await self._show(request, model, model_manager)
            elif action == "create":
                return await self._create(request, model, model_manager)
            elif action == "edit":
                return await self._edit(request, model, model_manager)
        return await self._404(request)
