from pydantic import BaseModel, ConfigDict, Field


class BusinessHoursUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool | None = None
    timezone: str | None = None
    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None
    sunday: str | None = None
    offline_message: str | None = Field(default=None, alias="offlineMessage")


class BusinessHoursRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    enabled: bool
    timezone: str
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str
    sunday: str
    offline_message: str = Field(alias="offlineMessage")
