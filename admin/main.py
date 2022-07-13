from abc import abstractmethod
import re
from typing import Any, List, Optional, Type
from fastapi import Depends, Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from jinja2 import pass_context
from loguru import logger
from sqlmodel import Session

from common.admin.models import AdminModel, AdminModelManager
from starlette.templating import Jinja2Templates
from starlette.datastructures import FormData
from starlette.status import HTTP_200_OK
from common.admin.helpers import get_file_icon


class Admin:
    models: List[AdminModel] = []

    def __init__(self, title: str, admin_route_name: str = "admin") -> None:
        self.template = self._create_template(title, admin_route_name)

    def _create_template(self, title: str, admin_route_name: str):
        template = Jinja2Templates("common/templates")
        template.env.globals["admin_title"] = title
        template.env.globals["all_models"] = self.models
        template.env.filters["file_icon"] = get_file_icon
        template.env.filters[
            "to_model"
        ] = lambda identity: self._find_model_from_identity(identity)

        @pass_context
        def admin_url(context: dict) -> str:
            request = context["request"]
            return request.url_for(admin_route_name)

        @pass_context
        def admin_url_for(
            context: dict, model: AdminModel, action: str = "list"
        ) -> str:
            request = context["request"]
            return (
                request.url_for(admin_route_name)
                + f"?model={model.identity()}&action={action}"
            )

        template.env.globals["admin_url"] = admin_url
        template.env.globals["admin_url_for"] = admin_url_for
        return template

    def register(self, model: Type[AdminModel]) -> None:
        self.models.append(model())

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
        id = request.query_params.get("id")
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
        id = request.query_params.get("id")
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

    async def route(
        self, request: Request, model_manager: AdminModelManager
    ) -> Response:
        model = self._find_model_from_identity(request.query_params.get("model"))
        if model is None:
            return RedirectResponse(
                request.url.include_query_params(model=self.models[0].identity())
            )
        action = request.query_params.get("action")
        if action is None:
            return RedirectResponse(request.url.include_query_params(action="list"))
        elif action == "list":
            return await self._list(request, model)
        elif action == "show":
            return await self._show(request, model, model_manager)
        elif action == "create":
            return await self._create(request, model, model_manager)
        elif action == "edit":
            return await self._edit(request, model, model_manager)
        return await self._404(request)
