from pydantic import BaseModel

class CreateInvitationTokenSchema(BaseModel):
    token: str
    project_id: int
    user_id: int

