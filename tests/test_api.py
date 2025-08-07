import pytest
import json
import os
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestFiltersAPI:
    """Тесты для endpoint /api/filters"""
    
    def setup_method(self):
        """Подготовка перед каждым тестом"""
        # Удаляем тестовый файл если он существует
        config_path = Path("telemetr_parser/filters_config.py")
        if config_path.exists():
            # Сохраняем оригинальный файл
            with open(config_path, 'r', encoding='utf-8') as f:
                self.original_content = f.read()
        else:
            self.original_content = None
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        config_path = Path("telemetr_parser/filters_config.py")
        if self.original_content:
            # Восстанавливаем оригинальный файл
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(self.original_content)
        elif config_path.exists():
            # Удаляем тестовый файл
            config_path.unlink()
    
    def test_update_filters_success(self):
        """Тест успешного обновления фильтров"""
        # Корректные данные
        valid_filters = {
            "categories": ["IT", "Музыка"],
            "participants_from": 1000,
            "participants_to": 50000,
            "lang_code": "ru",
            "page": 1
        }
        
        response = client.put("/api/filters", json=valid_filters)
        
        # Проверяем статус ответа
        assert response.status_code == 204
        
        # Проверяем что файл создался
        config_path = Path("telemetr_parser/filters_config.py")
        assert config_path.exists()
        
        # Проверяем содержимое файла
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "IT" in content
            assert "Музыка" in content
            assert "1000" in content
            assert "FILTERS =" in content
    
    def test_update_filters_invalid_schema(self):
        """Тест валидации схемы - некорректные данные должны возвращать 422"""
        # Некорректные данные - отрицательные числа
        invalid_filters = {
            "participants_from": -1000,  # Отрицательное число
            "er_from": 150,  # ER больше 100%
            "categories": "not_a_list"  # Строка вместо списка
        }
        
        response = client.put("/api/filters", json=invalid_filters)
        
        # Проверяем что возвращается ошибка валидации
        assert response.status_code == 422
        
        # Проверяем что файл не создался/не изменился
        config_path = Path("telemetr_parser/filters_config.py")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "not_a_list" not in content
    
    def test_update_filters_empty_data(self):
        """Тест с пустыми данными"""
        empty_filters = {}
        
        response = client.put("/api/filters", json=empty_filters)
        
        # Пустые данные должны быть валидными (все поля optional)
        assert response.status_code == 204
        
        # Проверяем что файл создался с пустым объектом
        config_path = Path("telemetr_parser/filters_config.py")
        assert config_path.exists()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Пустой объект может содержать только page: 1 (дефолтное значение)
            assert "FILTERS =" in content
    
    def test_update_filters_cyrillic_characters(self):
        """Тест сохранения кириллических символов"""
        cyrillic_filters = {
            "categories": ["Музыка", "Юмор", "Кулинария"],
            "channel_name": "Тестовый канал",
            "description": "Описание на русском языке"
        }
        
        response = client.put("/api/filters", json=cyrillic_filters)
        
        assert response.status_code == 204
        
        # Проверяем что кириллица сохранилась корректно
        config_path = Path("telemetr_parser/filters_config.py")
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Музыка" in content
            assert "Тестовый канал" in content
            assert "русском языке" in content
            # Проверяем что не используется ASCII escape
            assert "\\u" not in content
    
    def test_update_filters_range_validation(self):
        """Тест валидации диапазонов"""
        # Корректные диапазоны
        valid_ranges = {
            "participants_from": 1000,
            "participants_to": 50000,
            "er_from": 5,
            "er_to": 25
        }
        
        response = client.put("/api/filters", json=valid_ranges)
        assert response.status_code == 204
        
        # Некорректные диапазоны - ER больше 100%
        invalid_ranges = {
            "er_from": 150,
            "er_to": 200
        }
        
        response = client.put("/api/filters", json=invalid_ranges)
        assert response.status_code == 422
    
    def test_update_filters_literal_values(self):
        """Тест валидации литеральных значений"""
        # Корректные литеральные значения
        valid_literals = {
            "channel_type": "opened",
            "verified": "yes",
            "has_stats": "es"
        }
        
        response = client.put("/api/filters", json=valid_literals)
        assert response.status_code == 204
        
        # Некорректные литеральные значения
        invalid_literals = {
            "channel_type": "invalid_type",
            "verified": "maybe"
        }
        
        response = client.put("/api/filters", json=invalid_literals)
        assert response.status_code == 422

class TestStatusAPI:
    """Тесты для endpoint /api/status"""
    
    def test_get_status_initial(self):
        """Тест получения начального статуса"""
        response = client.get("/api/status")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "error" in data
        assert isinstance(data["running"], bool)
        assert data["error"] is None or isinstance(data["error"], str)

class TestDownloadAPI:
    """Тесты для endpoint /api/download/{kind}"""
    
    def test_download_nonexistent_file(self):
        """Тест скачивания несуществующего файла"""
        # Убеждаемся что файлы не существуют
        excel_path = Path("data/telemetr_results.xlsx")
        json_path = Path("data/telemetr_results.json")
        
        if excel_path.exists():
            excel_path.unlink()
        if json_path.exists():
            json_path.unlink()
        
        # Пытаемся скачать несуществующие файлы
        response = client.get("/api/download/excel")
        assert response.status_code == 404
        
        response = client.get("/api/download/json")
        assert response.status_code == 404
    
    def test_download_invalid_kind(self):
        """Тест скачивания с некорректным типом файла"""
        response = client.get("/api/download/invalid")
        assert response.status_code == 422  # Pydantic validation error

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 