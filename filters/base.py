from abc import abstractmethod

from pydantic import BaseModel


class BaseModelFilter(BaseModel):
    @abstractmethod
    def to_query(self):
        pass
