from pydantic import BaseModel, ConfigDict


class PersonaOut(BaseModel):
    """A persona as shown in the picker.

    `system_prompt` is deliberately absent — it is internal and must never
    reach the client.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {"key": "grumpy_pirate", "name": "Grumpy Pirate"}
        },
    )

    key: str
    name: str
