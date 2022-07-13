from typing import Optional

from depot.manager import DepotManager, get_depot
from fastapi import UploadFile
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import event, inspect, orm, types
from sqlalchemy.orm import ColumnProperty
from sqlmodel import Session


class FileInfo(BaseModel):
    path: Optional[str]
    filename: Optional[str]
    content_type: Optional[str]
    content: Optional[UploadFile]

    class Config:
        fields = {"content": {"exclude": True}}

    def save_to_storage(self, upload_storage: Optional[str] = None):
        if self.content is not None:
            content = self.content
            if upload_storage is None:
                upload_storage = DepotManager.get_default()
            depot = DepotManager.get(upload_storage)
            fileid = depot.create(
                content.file,
                filename=content.filename,
                content_type=content.content_type,
            )
            self.path = "%s/%s" % (upload_storage, fileid)
            self.filename = content.filename
            self.content_type = content.content_type
            logger.info("__save_content %s" % self.dict())
        else:
            self.path = None

    def to_db(self):
        if self.path is None:
            return None
        return self.dict()


class FileField(types.TypeDecorator):
    impl = types.JSON

    def __init__(self, upload_storage=None, is_array=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.upload_storage = upload_storage
        self.is_array = is_array

    def process_bind_param(self, value, dialect):
        if not value:
            return [] if self.is_array else None
        if not self.is_array and not isinstance(value, FileInfo):
            raise ValueError(f"Expected FileInfo, received: {type(value)}")
        if self.is_array and not (
            type(value) is list and all([isinstance(v, FileInfo) for v in value])
        ):
            raise ValueError(f"Expected list of FileInfo, received: {type(value)}")
        return [v.to_db() for v in value] if self.is_array else value.to_db()

    def process_result_value(self, value, dialect):
        if not value:
            return None
        if type(value) is dict:
            return [FileInfo(**value)] if self.is_array else FileInfo(**value)
        return [FileInfo(**v) for v in value]


class FileFieldSessionTracker(object):
    mapped_entities = dict()

    @classmethod
    def _field_set(cls, target, value, oldvalue, initiator):
        logger.info("field_set old: %s" % oldvalue)
        logger.info("field_set new: %s" % value)

        inspection = inspect(target)
        set_property = inspection.mapper.get_property(initiator.key)
        column_type = set_property.columns[0].type
        assert isinstance(column_type, FileField)
        session = inspection.session
        if session is not None:
            if isinstance(oldvalue, FileInfo):
                oldvalue = [oldvalue]
            if oldvalue is not None and (
                type(oldvalue) is list
                and all([isinstance(v, FileInfo) for v in oldvalue])
            ):
                session._depot_old = getattr(session, "_depot_old", set())
                session._depot_old.update([v.path for v in oldvalue])

        if value is None:
            return value
        if isinstance(value, FileInfo):
            value = [value]
        assert type(value) is list and all([isinstance(v, FileInfo) for v in value])
        for v in value:
            v.save_to_storage(column_type.upload_storage)

    @classmethod
    def _before_commit(cls, session):
        logger.info("before_commit new: %s" % session.new)
        logger.info("before_commit dirty: %s" % session.dirty)
        logger.info("before_commit delete: %s" % session.deleted)
        cls.add_to_session(session.new, session)
        # cls.add_to_session(session.dirty, session)
        cls.add_to_session(session.deleted, session, True)

    @classmethod
    def add_to_session(cls, _list, session, old=False):
        for obj in _list:
            class_ = obj.__class__
            tracked_columns = cls.mapped_entities.get(class_, tuple())
            for col in tracked_columns:
                value = getattr(obj, col)
                if isinstance(value, FileInfo):
                    value = [value]
                if value is not None and (
                    type(value) is list
                    and all([isinstance(v, FileInfo) for v in value])
                ):
                    if old:
                        session._depot_old = getattr(session, "_depot_old", set())
                        session._depot_old.update([v.path for v in value])
                    else:
                        session._depot_new = getattr(session, "_depot_new", set())
                        session._depot_new.update([v.path for v in value])

    @classmethod
    def _after_commit(cls, session):
        if hasattr(session, "_depot_old"):
            logger.info("_after_commit old: %s" % session._depot_old)
        if hasattr(session, "_depot_new"):
            logger.info("_after_commit new: %s" % session._depot_new)
        cls.delete_files(getattr(session, "_depot_old", set()), "after_commit")
        cls.clear_session(session)

    @classmethod
    def _after_flush(cls, session, flush_context):
        cls.add_to_session(
            [s.obj() for s in flush_context.states.keys() if s.deleted], session, True
        )

    @classmethod
    def _after_soft_rollback(cls, session, previous_transaction):
        cls.delete_files(getattr(session, "_depot_new", set()), "rollback")
        cls.clear_session(session)

    @classmethod
    def delete_files(cls, paths, msg):
        for path in paths:
            depot, fileid = path.split("/")
            get_depot(depot).delete(fileid)
            logger.debug("deleted %s due to %s" % (path, msg))

    @classmethod
    def clear_session(cls, session):
        if hasattr(session, "_depot_old"):
            del session._depot_old
        if hasattr(session, "_depot_new"):
            del session._depot_new

    @classmethod
    def _mapper_configured(cls, mapper, class_):
        for mapper_property in mapper.iterate_properties:
            if isinstance(mapper_property, ColumnProperty):
                for idx, col in enumerate(mapper_property.columns):
                    if isinstance(col.type, FileField):
                        if idx > 0:
                            # Not clear when this might happen, but ColumnProperty can have
                            # multiple columns assigned. We should probably take the first one
                            # as is done by ColumnProperty.expression but there is no guarantee
                            # that it would be the right thing to do.
                            raise TypeError(
                                "FileField currently supports a single column"
                            )
                        cls.mapped_entities.setdefault(class_, []).append(
                            mapper_property.key
                        )
                        event.listen(
                            mapper_property,
                            "set",
                            cls._field_set,
                            retval=True,
                            propagate=True,
                        )

    @classmethod
    def setup(cls):
        event.listen(orm.mapper, "mapper_configured", cls._mapper_configured)
        event.listen(Session, "before_commit", cls._before_commit)
        event.listen(Session, "after_commit", cls._after_commit)
        event.listen(Session, "after_flush_postexec", cls._after_flush)
        event.listen(Session, "after_soft_rollback", cls._after_soft_rollback)


FileFieldSessionTracker.setup()
