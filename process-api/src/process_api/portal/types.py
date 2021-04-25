"""Service types."""
from datetime import date
from enum import Enum
from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import Field


class VocabularyValue(BaseModel):
    """Portal vocabulary value."""

    title: str
    token: str


class User(BaseModel):
    """Portal user details."""

    jsonld_id: AnyHttpUrl = Field(alias="@id")

    id: str
    username: str
    fullname: str

    @property
    def first_name(self) -> str:
        """First name."""
        return (
            self.fullname.rsplit(", ", 1)[-1]
            if ", " in self.fullname
            else self.fullname.rsplit(" ", 1)[0]
        )

    @property
    def last_name(self) -> str:
        """Last name."""
        return (
            self.fullname.rsplit(", ", 1)[0]
            if ", " in self.fullname
            else self.fullname.rsplit(" ", 1)[-1]
        )


class Course(BaseModel):
    """Portal course type."""

    jsonld_id: AnyHttpUrl = Field(alias="@id")
    jsonld_type: str = Field(alias="@type")

    UID: str
    title: str
    description: str

    price: float

    product_code: VocabularyValue
    tax_code: VocabularyValue

    course_end_date: date
    course_id: str
    course_start_date: date
    credits: str

    registration_end_date: date
    registration_start_date: date

    vle_course_id: str


class VoucherState(str, Enum):
    """Portal voucher state."""

    disabled: str = "disabled"
    enabled: str = "enabled"


class Voucher(BaseModel):
    """Portal voucher."""

    jsonld_id: AnyHttpUrl = Field(alias="@id")
    jsonld_type: str = Field(alias="@type")

    UID: str
    title: str

    code: str
    review_state: VoucherState
