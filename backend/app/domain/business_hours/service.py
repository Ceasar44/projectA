import re

from app.domain.business_hours.schemas import BusinessHoursRead, BusinessHoursUpdate
from app.infrastructure.db.models.operations import BusinessHours


class BusinessHoursService:
    def __init__(self, uow):
        self.uow = uow

    async def get_config(self) -> BusinessHoursRead:
        config = await self.uow.session.get(BusinessHours, "default")
        if not config:
            config = BusinessHours(id="default")
            self.uow.session.add(config)
            await self.uow.commit()
            await self.uow.session.refresh(config)
        return BusinessHoursRead.model_validate(config)

    async def update_config(self, payload: BusinessHoursUpdate) -> BusinessHoursRead:
        time_pattern = re.compile(r"^\d{2}:\d{2}-\d{2}:\d{2}$")

        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        for day in days:
            value = getattr(payload, day, None)
            if value is not None and value != "" and not time_pattern.match(value):
                raise ValueError(
                    f"Invalid time format for {day}. Use HH:mm-HH:mm or leave empty."
                )

        config = await self.uow.session.get(BusinessHours, "default")
        if not config:
            config = BusinessHours(
                id="default",
                enabled=payload.enabled or False,
                timezone=payload.timezone or "UTC",
                monday=payload.monday or "09:00-18:00",
                tuesday=payload.tuesday or "09:00-18:00",
                wednesday=payload.wednesday or "09:00-18:00",
                thursday=payload.thursday or "09:00-18:00",
                friday=payload.friday or "09:00-18:00",
                saturday=payload.saturday or "",
                sunday=payload.sunday or "",
                offline_message=payload.offline_message
                or "We are currently offline. We will get back to you during business hours.",
            )
            self.uow.session.add(config)
        else:
            update_data = payload.model_dump(exclude_unset=True, by_alias=False)
            for key, value in update_data.items():
                setattr(config, key, value)

        await self.uow.commit()
        await self.uow.session.refresh(config)
        return BusinessHoursRead.model_validate(config)

    async def is_within_hours(self) -> bool:
        config = await self.get_config()
        if not config.enabled:
            return True

        import datetime

        now = datetime.datetime.now(datetime.timezone.utc)
        day_name = now.strftime("%A").lower()
        hours = getattr(config, day_name, "")

        if not hours:
            return False

        try:
            start_str, end_str = hours.split("-")
            start_hour, start_min = map(int, start_str.split(":"))
            end_hour, end_min = map(int, end_str.split(":"))

            current_minutes = now.hour * 60 + now.minute
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            return start_minutes <= current_minutes <= end_minutes
        except (ValueError, AttributeError):
            return False
