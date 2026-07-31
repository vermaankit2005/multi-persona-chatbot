from pydantic import BaseModel


class PersonaOut(BaseModel):
    """A persona as shown in the picker.

    `system_prompt` is deliberately absent — it is internal and must never
    reach the client.
    """
    key: str
    name: str
