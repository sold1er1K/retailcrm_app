from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class ClientBase(BaseModel):
    """Базовая модель клиента"""

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя клиента",
        example="Егор"
    )

    last_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Фамилия клиента",
        example="Солдатенков"
    )

    email: EmailStr = Field(
        ...,
        description="Email адрес клиента",
        example="egor.soldatenkov@gmail.com"
    )

    phone: Optional[str] = Field(
        None,
        pattern=r'^\+?[1-9]\d{1,14}$',
        description="Номер телефона в международном формате",
        example="+375333218678"
    )


class ClientCreate(ClientBase):
    """Модель для создания клиента"""

    @field_validator('first_name')
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        """Валидация имени клиента."""
        if not v.strip():
            raise ValueError("Имя не может быть пустым")
        return v.strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Валидация и нормализация номера телефона."""
        if v is None:
            return v

        # Удаляем все нецифровые символы кроме плюса в начале
        cleaned = ''.join(c for c in v if c.isdigit() or (c == '+' and v.index(c) == 0))

        if not cleaned:
            raise ValueError("Неверный формат телефона")

        return cleaned


class ClientResponse(ClientBase):
    """Модель ответа для клиента"""

    id: Optional[int] = Field(
        None,
        description="Внутренний ID клиента в RetailCRM",
        example=12345
    )

    external_id: Optional[str] = Field(
        None,
        description="Внешний ID клиента",
        example="EXT-12345"
    )

    created_at: Optional[str] = Field(
        None,
        description="Дата создания клиента",
        example="2025-12-15"
    )

    site: Optional[str] = Field(
        None,
        description="Магазин, с которого пришел клиент",
        example="default-store"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 12345,
                "first_name": "Егор",
                "last_name": "Солдатенков",
                "email": "egor.soldatenkov@gmail.com",
                "phone": "+375333218678",
                "created_at": "2025-12-15"
            }
        }


class ClientsListResponse(BaseModel):
    """Модель ответа для списка клиентов"""

    success: bool = Field(True, description="Успешность запроса клиентов")
    data: dict = Field(
        ...,
        description="Данные клиентов",
        example={
            "customers": [],
            "pagination": {
                "limit": 20,
                "totalCount": 0,
                "currentPage": 1,
                "totalPageCount": 0
            }
        }
    )

    meta: dict = Field(
        ...,
        description="Мета-информация",
        example={
            "total": 0,
            "page": 1,
            "limit": 20
        }
    )


class ClientCreateResponse(BaseModel):
    """Модель ответа при создании клиента"""

    success: bool = Field(True, description="Успешность создания клиента")
    data: dict = Field(
        ...,
        description="Данные созданного клиента",
        example={
            "customer_id": 12345,
            "message": "Клиент успешно создан"
        }
    )

    meta: dict = Field(
        ...,
        description="Мета-информация",
        example={
            "retailcrm_success": True,
            "customer_email": "egor.soldatenkov@gmail.com"
        }
    )