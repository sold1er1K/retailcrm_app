import json
import httpx

from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.dependencies import get_retailcrm_client
from app.api.v1.models import ClientCreate

router = APIRouter(prefix="/clients", tags=["clients"])

class RetailCRMClientError(Exception):
    """Кастомное исключение для ошибок RetailCRM API"""

    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class RetailCRMService:
    """Сервисный слой для работы с RetailCRM API"""

    @staticmethod
    async def create_customer(
            client_data: ClientCreate,
            retail_client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Создает нового клиента в RetailCRM.

        Args:
            client_data: Данные клиента для создания
            retail_client: HTTP клиент для RetailCRM

        Returns:
            Ответ от RetailCRM API
        """
        try:
            customer_data = {
                "firstName": client_data.first_name,
                "lastName": client_data.last_name,
                "email": client_data.email
            }

            if client_data.phone:
                customer_data["phones"] = [{"number": client_data.phone}]

            customer_json = json.dumps(customer_data, ensure_ascii=False)
            form_data = {"customer": customer_json}

            response = await retail_client.post(
                "/api/v5/customers/create",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0
            )

            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                error_msg = result.get("errorMsg", "Неизвестная ошибка создания")
                raise RetailCRMClientError(
                    message=error_msg,
                    status_code=response.status_code,
                    details={"errors": result.get("errors", [])}
                )

            return result

        except json.JSONDecodeError as e:
            raise RetailCRMClientError(
                message="Ошибка форматирования данных",
                status_code=500
            )
        except httpx.TimeoutException:
            raise RetailCRMClientError(
                message="Таймаут соединения с RetailCRM",
                status_code=504
            )

    @staticmethod
    async def fetch_customers(
            retail_client: httpx.AsyncClient,
            filters: Optional[Dict[str, Any]] = None,
            limit: int = 20,
            page: int = 1
    ) -> Dict[str, Any]:
        """
        Получает список клиентов из RetailCRM с фильтрацией.

        Args:
            retail_client: HTTP клиент для RetailCRM
            filters: Словарь фильтров
            limit: Лимит на страницу
            page: Номер страницы

        Returns:
            Ответ от RetailCRM API с клиентами
        """
        try:
            params = {"limit": limit, "page": page}

            if filters:
                for key, value in filters.items():
                    if value is not None:
                        params[f"filter[{key}]"] = value

            response = await retail_client.get(
                "/api/v5/customers",
                params=params,
                timeout=30.0
            )

            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                error_msg = result.get("errorMsg", "Неизвестная ошибка получения")
                raise RetailCRMClientError(
                    message=error_msg,
                    status_code=response.status_code
                )

            customers_count = len(result.get("customers", []))

            return result

        except httpx.TimeoutException:
            raise RetailCRMClientError(
                message="Таймаут соединения с RetailCRM",
                status_code=504
            )


def build_customer_filters(
        name: Optional[str] = None,
        email: Optional[str] = None,
        created_at: Optional[date] = None
) -> Dict[str, Any]:
    """
    Строит словарь фильтров для запроса клиентов.

    Args:
        name: Фильтр по имени
        email: Фильтр по email
        created_at: Фильтр по дате регистрации

    Returns:
        Словарь с примененными фильтрами
    """
    filters = {}

    if name:
        filters["name"] = name

    if email:
        filters["email"] = email

    if created_at:
        date_str = created_at.isoformat()
        filters["dateFrom"] = date_str
        filters["dateTo"] = date_str

    return filters


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Получить список клиентов",
    description="Возвращает список клиентов из RetailCRM с поддержкой фильтрации."
)
async def get_clients(
        name: Optional[str] = Query(
            None,
            description="Фильтр по имени или фамилии клиента",
            example="Егор"
        ),
        email: Optional[str] = Query(
            None,
            description="Фильтр по email адресу",
            example="egor.soldatenkov@gmail.com"
        ),
        created_at: Optional[date] = Query(
            None,
            description="Фильтр по дате регистрации (YYYY-MM-DD)",
            example="2025-12-15"
        ),
        limit: int = Query(
            20,
            ge=1,
            le=100,
            description="Количество клиентов на странице",
            example=20
        ),
        page: int = Query(
            1,
            ge=1,
            description="Номер страницы",
            example=1
        ),
        retail_client: httpx.AsyncClient = Depends(get_retailcrm_client)
) -> Dict[str, Any]:
    """
    Получение списка клиентов из RetailCRM с фильтрацией.

    Фильтрация по:
    - Имени/фамилии
    - Email адресу
    - Дате регистрации

    Returns:
        Пагинированный результат
    """
    try:
        filters = build_customer_filters(name, email, created_at)

        result = await RetailCRMService.fetch_customers(
            retail_client=retail_client,
            filters=filters,
            limit=limit,
            page=page
        )

        return {
            "success": True,
            "data": {
                "customers": result.get("customers", []),
                "pagination": result.get("pagination", {})
            },
            "meta": {
                "total": len(result.get("customers", [])),
                "page": page,
                "limit": limit
            }
        }

    except RetailCRMClientError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": "retailcrm_error",
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Внутренняя ошибка сервера"
            }
        )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
    summary="Создать нового клиента",
    description="Создает нового клиента в RetailCRM системе."
)
async def create_client(
        client_data: ClientCreate,
        retail_client: httpx.AsyncClient = Depends(get_retailcrm_client)
) -> Dict[str, Any]:
    """
    Создание нового клиента в RetailCRM.

    Требуемые поля:
    - first_name (имя)
    - email (почта)

    Опциональные поля:
    - last_name (фамилия)
    - phone (телефон)

    Returns:
        ID созданного клиента.
    """
    try:
        if not client_data.email or not client_data.first_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "validation_error",
                    "message": "Email и имя являются обязательными полями"
                }
            )

        result = await RetailCRMService.create_customer(client_data, retail_client)

        return {
            "success": True,
            "data": {
                "customer_id": result.get("id"),
                "message": "Клиент успешно создан"
            },
            "meta": {
                "retailcrm_success": True,
                "customer_email": client_data.email
            }
        }

    except HTTPException:
        raise
    except RetailCRMClientError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": "retailcrm_error",
                "message": f"Ошибка при создании клиента: {e.message}",
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Внутренняя ошибка при создании клиента"
            }
        )
