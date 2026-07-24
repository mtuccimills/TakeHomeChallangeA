from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Entidade de los modelos de datos a utilizar en el proyecto.
# Consumir fuente de información externa.


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)  # EmailStr validates that is not empty

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "username": "Mat",
                "email": "mat@gmail.com",
            }
        },
    )


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=20)
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "username": "Mat",
                "email": "mat@gmail.com",
                "password": "password123",
            }
        },
    )
    # Add password for authentication


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(
        default=None, max_length=120
    )  # EmailStr validates that is not empty

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={"example": {"username": "Matias"}},
    )


class Token(BaseModel):
    access_token: str
    token_type: str


class UserPublic(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "1",
                "username": "Mat",
            }
        },
    )


class UserPrivate(UserPublic):
    email: EmailStr
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "1",
                "username": "Mat",
                "email": "mat@gmail.copm",
            }
        },
    )


# token clasees for sending email, not implemanted yet
#
class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=120)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
