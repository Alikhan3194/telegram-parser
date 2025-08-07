from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class FiltersSchema(BaseModel):
    """Схема валидации фильтров для парсера"""
    
    # Основные фильтры
    categories: Optional[List[str]] = Field(None, description="Список категорий каналов")
    links: Optional[List[str]] = Field(None, description="Список ссылок на каналы")
    channel_name: Optional[str] = Field(None, description="Название канала")
    description: Optional[str] = Field(None, description="Описание канала")
    
    # Диапазоны подписчиков
    participants_from: Optional[int] = Field(None, ge=0, description="Минимальное количество подписчиков")
    participants_to: Optional[int] = Field(None, ge=0, description="Максимальное количество подписчиков")
    
    # Диапазоны просмотров
    views_post_from: Optional[int] = Field(None, ge=0, description="Минимальное количество просмотров на пост")
    views_post_to: Optional[int] = Field(None, ge=0, description="Максимальное количество просмотров на пост")
    
    # Диапазоны упоминаний
    mentions_week_from: Optional[int] = Field(None, ge=0, description="Минимальное количество упоминаний за неделю")
    mentions_week_to: Optional[int] = Field(None, ge=0, description="Максимальное количество упоминаний за неделю")
    
    # Диапазоны ER
    er_from: Optional[float] = Field(None, ge=0, le=100, description="Минимальный ER в процентах")
    er_to: Optional[float] = Field(None, ge=0, le=100, description="Максимальный ER в процентах")
    
    # Селекты
    channel_type: Optional[Literal["opened", "closed"]] = Field(None, description="Тип канала")
    verified: Optional[Literal["yes", "no"]] = Field(None, description="Верифицирован ли канал")
    lang_code: Optional[str] = Field(None, description="Код языка")
    has_stats: Optional[Literal["es"]] = Field(None, description="Наличие подробной статистики")
    
    # Пол аудитории
    male_from: Optional[int] = Field(None, ge=0, le=100, description="Минимальный процент мужчин в аудитории")
    female_from: Optional[int] = Field(None, ge=0, le=100, description="Минимальный процент женщин в аудитории")
    
    # Служебные
    page: Optional[int] = Field(1, ge=1, description="Номер страницы для парсинга")
    
    class Config:
        extra = "forbid"  # Запрещаем дополнительные поля 