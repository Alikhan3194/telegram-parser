import React, { useState, useEffect } from 'react'
import { Formik, Form, Field } from 'formik'
import { toast } from 'react-toastify'
import { putFilters, startParse, getStatus, download, ParseStatus } from '../lib/api'

interface FormValues {
  categories: string[]
  links: string
  channel_name: string
  description: string
  participants_from: string
  participants_to: string
  views_post_from: string
  views_post_to: string
  mentions_week_from: string
  mentions_week_to: string
  er_from: string
  er_to: string
  channel_type: string
  verified: string
  lang_code: string
  male_from: string
  female_from: string
  has_stats: string
}

const ParserForm: React.FC = () => {
  const [status, setStatus] = useState<ParseStatus>({ running: false, error: null })
  const [polling, setPolling] = useState(false)
  const [completed, setCompleted] = useState(false)

  // Список всех категорий
  const allCategories = [
    'GIF и video', 'IT', 'SMM', 'Авто и мото', 'Авторский блог', 'Азербайджанские каналы',
    'Активный отдых', 'Анекдоты', 'Аниме', 'Армянские каналы', 'Афиша', 'Белорусские каналы',
    'Бизнес и финансы', 'Блогеры', 'Вакансии', 'Военное', 'Все подряд', 'Гороскоп',
    'Грузинские каналы', 'Даркнет', 'Дизайн', 'Для мужчин', 'Для родителей', 'ЕГЭ и экзамены',
    'Женские', 'Животные', 'Здоровье', 'Знакомства', 'Игры', 'Искусство', 'Казахстанские каналы',
    'Карьера', 'Каталог', 'Киргизские каналы', 'Коронавирус', 'Красота и мода', 'Криптовалюты',
    'Кулинария', 'Лайфхаки', 'Лингвистика', 'Литература', 'Магазин', 'Маркетплейсы', 'Мобайл',
    'Молдавские каналы', 'Музыка', 'Наука и технологии', 'Недвижимость', 'Новости', 'Образование',
    'Объявления', 'Однострочные', 'Подкасты', 'Подслушано', 'Познавательные', 'Политика',
    'Пошлое', 'Прогнозы и ставки', 'Прокси', 'Психология', 'Путешествия', 'Региональные',
    'Религия', 'Рукоделие', 'Сад и огород', 'Сервисы', 'Сливы', 'Спорт', 'Стикеры',
    'Строительство и ремонт', 'Таджикские каналы', 'Технические каналы', 'Узбекские каналы',
    'Украинские каналы', 'Фан-каналы', 'Фильмы и сериалы', 'Фото', 'Халява и скидки',
    'Цитаты', 'Эзотерика', 'Экология', 'Юмор', 'Юриспруденция'
  ]

  // Языки
  const languages = [
    { code: '', name: 'Любой' },
    { code: 'ru', name: 'Русский' },
    { code: 'ua', name: 'Украинский' },
    { code: 'en', name: 'Английский' },
    { code: 'tr', name: 'Турецкий' },
    { code: 'sk', name: 'Словакский' },
    { code: 'hr', name: 'Хорватский' },
    { code: 'sq', name: 'Албанский' },
    { code: 'by', name: 'Белорусский' },
    { code: 'bg', name: 'Болгарский' },
    { code: 'hu', name: 'Венгерский' },
    { code: 'vi', name: 'Вьетнамский' },
    { code: 'nl', name: 'Голландский' },
    { code: 'ge', name: 'Грузинский' },
    { code: 'gr', name: 'Греческий' },
    { code: 'dk', name: 'Датский' },
    { code: 'il', name: 'Иврит' },
    { code: 'id', name: 'Индонезийский' },
    { code: 'es', name: 'Испанский' },
    { code: 'it', name: 'Итальянский' },
    { code: 'kz', name: 'Казахский' },
    { code: 'kg', name: 'Киргизский' },
    { code: 'cn', name: 'Китайский' },
    { code: 'lv', name: 'Латышский' },
    { code: 'lt', name: 'Литовский' },
    { code: 'mk', name: 'Македонский' },
    { code: 'md', name: 'Молдавский' },
    { code: 'de', name: 'Немецкий' },
    { code: 'no', name: 'Норвежский' },
    { code: 'pl', name: 'Польский' },
    { code: 'pt', name: 'Португальский' },
    { code: 'ro', name: 'Румынский' },
    { code: 'rs', name: 'Сербский' },
    { code: 'tj', name: 'Таджикский' },
    { code: 'uz', name: 'Узбекский' },
    { code: 'fi', name: 'Финский' },
    { code: 'fr', name: 'Французский' },
    { code: 'cz', name: 'Чешский' },
    { code: 'sv', name: 'Шведский' },
    { code: 'et', name: 'Эстонский' },
    { code: 'af', name: 'Афганский' },
    { code: 'n/a', name: 'Не определён' }
  ]

  const initialValues: FormValues = {
    categories: [],
    links: '',
    channel_name: '',
    description: '',
    participants_from: '',
    participants_to: '',
    views_post_from: '',
    views_post_to: '',
    mentions_week_from: '',
    mentions_week_to: '',
    er_from: '',
    er_to: '',
    channel_type: '',
    verified: '',
    lang_code: '',
    male_from: '',
    female_from: '',
    has_stats: ''
  }

  // Polling для статуса
  useEffect(() => {
    let interval: number
    if (polling) {
      interval = setInterval(async () => {
        try {
          const currentStatus = await getStatus()
          setStatus(currentStatus)
          if (!currentStatus.running) {
            setPolling(false)
            
            // Если парсинг завершен успешно - показываем сообщение
            if (!currentStatus.error) {
              setCompleted(true)
            }
          }
        } catch (error) {
          console.error('Ошибка получения статуса:', error)
          setPolling(false)
        }
      }, 3000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [polling])

  const handleSubmit = async (values: FormValues, { resetForm }: any) => {
    try {
      setCompleted(false) // Сбрасываем статус завершения
      
      // Подготавливаем данные
      const filters: any = {}
      
      if (values.categories.length > 0) filters.categories = values.categories
      if (values.links && values.links.trim()) filters.links = values.links.trim().split('\n').filter(link => link.trim())
      if (values.channel_name && values.channel_name.trim()) filters.channel_name = values.channel_name.trim()
      if (values.description && values.description.trim()) filters.description = values.description.trim()
      
      // Числовые поля - проверяем что значение существует и не пустое
      if (values.participants_from && String(values.participants_from).trim()) {
        filters.participants_from = parseInt(String(values.participants_from))
      }
      if (values.participants_to && String(values.participants_to).trim()) {
        filters.participants_to = parseInt(String(values.participants_to))
      }
      if (values.views_post_from && String(values.views_post_from).trim()) {
        filters.views_post_from = parseInt(String(values.views_post_from))
      }
      if (values.views_post_to && String(values.views_post_to).trim()) {
        filters.views_post_to = parseInt(String(values.views_post_to))
      }
      if (values.mentions_week_from && String(values.mentions_week_from).trim()) {
        filters.mentions_week_from = parseInt(String(values.mentions_week_from))
      }
      if (values.mentions_week_to && String(values.mentions_week_to).trim()) {
        filters.mentions_week_to = parseInt(String(values.mentions_week_to))
      }
      if (values.er_from && String(values.er_from).trim()) {
        filters.er_from = parseFloat(String(values.er_from))
      }
      if (values.er_to && String(values.er_to).trim()) {
        filters.er_to = parseFloat(String(values.er_to))
      }
      if (values.male_from && String(values.male_from).trim()) {
        filters.male_from = parseInt(String(values.male_from))
      }
      if (values.female_from && String(values.female_from).trim()) {
        filters.female_from = parseInt(String(values.female_from))
      }
      
      // Селекты
      if (values.channel_type && values.channel_type !== '') filters.channel_type = values.channel_type
      if (values.verified && values.verified !== '') filters.verified = values.verified
      if (values.lang_code && values.lang_code !== '') filters.lang_code = values.lang_code
      if (values.has_stats && values.has_stats !== '') filters.has_stats = values.has_stats

      // Отправка фильтров
      await putFilters(filters)
      
      // Запуск парсера
      await startParse()
      
      toast.success('Парсер запущен')
      setStatus({ running: true, error: null })
      setPolling(true)
      
    } catch (error: any) {
      console.error('Ошибка запуска парсера:', error)
      toast.error(error.message || 'Ошибка запуска парсера')
      
      // Показываем детальную информацию об ошибке
      if (error.message.includes('Failed to fetch')) {
        toast.error('Backend недоступен. Убедитесь, что сервер запущен на порту 8000')
      }
    }
  }

  const handleDownload = async (type: 'excel' | 'json') => {
    try {
      await download(type)
      toast.success(`Файл ${type.toUpperCase()} скачан`)
    } catch (error: any) {
      toast.error(error.message || `Ошибка скачивания ${type}`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-8 py-6">
            <h1 className="text-3xl font-bold text-white">Телеметр Парсер</h1>
            <p className="text-blue-100 mt-2">Настройте фильтры и запустите парсинг Telegram каналов</p>
          </div>

          {/* Status Messages */}
          {status.running && (
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mx-8 mt-6 rounded-r-lg">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                <p className="text-blue-800 font-medium">Парсинг выполняется... Ожидайте завершения</p>
              </div>
            </div>
          )}

          {status.error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 mx-8 mt-6 rounded-r-lg">
              <p className="text-red-800 font-medium">Ошибка: {status.error}</p>
            </div>
          )}

          {completed && !status.running && !status.error && (
            <div className="bg-green-50 border-l-4 border-green-400 p-4 mx-8 mt-6 rounded-r-lg">
              <div className="flex items-center">
                <div className="text-green-600 mr-3">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-green-800 font-semibold">Парсинг завершен успешно!</p>
                  <p className="text-green-700 text-sm">Файлы готовы к скачиванию. Нажмите кнопки ниже для скачивания Excel или JSON.</p>
                </div>
              </div>
            </div>
          )}

          <Formik initialValues={initialValues} onSubmit={handleSubmit}>
            {({ values, setFieldValue, resetForm }) => (
              <Form className="p-8 space-y-8">
                
                {/* Categories Section */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                    Категории каналов
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50">
                    {allCategories.map(category => (
                      <label key={category} className="flex items-center space-x-2 text-sm hover:bg-white p-2 rounded cursor-pointer transition-colors">
                        <Field
                          type="checkbox"
                          name="categories"
                          value={category}
                          className="w-4 h-4 text-blue-600 bg-white border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                        />
                        <span className="text-gray-700">{category}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Text Filters */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                    Поиск по содержимому
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Ссылки (по одной на строку)
                      </label>
                      <Field
                        as="textarea"
                        name="links"
                        rows={3}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                        placeholder="https://t.me/channel1&#10;https://t.me/channel2"
                      />
                    </div>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                          Название канала
                        </label>
                        <Field
                          type="text"
                          name="channel_name"
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="Поиск в названии"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                          Описание канала
                        </label>
                        <Field
                          type="text"
                          name="description"
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="Поиск в описании"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Numeric Filters */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                    Числовые показатели
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    
                    {/* Participants */}
                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Количество подписчиков
                      </label>
                      <div className="flex gap-2">
                        <Field
                          type="number"
                          name="participants_from"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="От"
                        />
                        <Field
                          type="number"
                          name="participants_to"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="До"
                        />
                      </div>
                    </div>

                    {/* Views */}
                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Просмотров на пост
                      </label>
                      <div className="flex gap-2">
                        <Field
                          type="number"
                          name="views_post_from"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="От"
                        />
                        <Field
                          type="number"
                          name="views_post_to"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="До"
                        />
                      </div>
                    </div>

                    {/* Mentions */}
                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Упоминаний за неделю
                      </label>
                      <div className="flex gap-2">
                        <Field
                          type="number"
                          name="mentions_week_from"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="От"
                        />
                        <Field
                          type="number"
                          name="mentions_week_to"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="До"
                        />
                      </div>
                    </div>

                    {/* ER */}
                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        ER (Engagement Rate), %
                      </label>
                      <div className="flex gap-2">
                        <Field
                          type="number"
                          step="0.1"
                          name="er_from"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="От"
                        />
                        <Field
                          type="number"
                          step="0.1"
                          name="er_to"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="До"
                        />
                      </div>
                    </div>

                    {/* Gender */}
                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Пол аудитории, %
                      </label>
                      <div className="flex gap-2">
                        <Field
                          type="number"
                          name="male_from"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="Мужчины от"
                        />
                        <Field
                          type="number"
                          name="female_from"
                          className="w-1/2 px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none"
                          placeholder="Женщины от"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Select Filters */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                    Дополнительные параметры
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    
                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Тип канала
                      </label>
                      <Field
                        as="select"
                        name="channel_type"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      >
                        <option value="">Не важно</option>
                        <option value="opened">Открытый</option>
                        <option value="closed">Закрытый</option>
                      </Field>
                    </div>

                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Верификация
                      </label>
                      <Field
                        as="select"
                        name="verified"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      >
                        <option value="">Не важно</option>
                        <option value="yes">Да</option>
                        <option value="no">Нет</option>
                      </Field>
                    </div>

                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Язык
                      </label>
                      <Field
                        as="select"
                        name="lang_code"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      >
                        {languages.map(lang => (
                          <option key={lang.code} value={lang.code}>{lang.name}</option>
                        ))}
                      </Field>
                    </div>

                    <div>
                      <label className="block text-xs text-gray-500 uppercase font-semibold mb-2">
                        Подробная статистика
                      </label>
                      <Field
                        as="select"
                        name="has_stats"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      >
                        <option value="">Не важно</option>
                        <option value="es">Подключено</option>
                      </Field>
                    </div>
                  </div>
                </div>

                {/* Main Action Button */}
                <div className="flex justify-center pt-6 border-t border-gray-200">
                  <button
                    type="submit"
                    disabled={status.running}
                    className="px-8 py-4 bg-blue-600 text-white rounded-lg shadow-lg hover:shadow-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold text-lg flex items-center gap-3"
                  >
                    {status.running && (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    )}
                    Запустить парсер
                  </button>
                </div>

                {/* Reset Button */}
                <div className="flex justify-center pt-4">
                  <button
                    type="button"
                    onClick={() => resetForm()}
                    className="px-5 py-2 bg-gray-500 text-white rounded-lg shadow-md hover:shadow-lg hover:bg-gray-600 transition-all duration-200 font-medium text-sm"
                  >
                    Сбросить форму
                  </button>
                </div>

                {/* Download Buttons */}
                {completed && !status.running && !status.error && (
                  <div className="flex justify-center gap-4 pt-6">
                    <button
                      type="button"
                      onClick={() => handleDownload('excel')}
                      className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md hover:shadow-lg hover:bg-green-700 transition-all duration-200 font-medium flex items-center gap-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Скачать Excel
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDownload('json')}
                      className="px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md hover:shadow-lg hover:bg-purple-700 transition-all duration-200 font-medium flex items-center gap-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Скачать JSON
                    </button>
                  </div>
                )}
              </Form>
            )}
          </Formik>
        </div>
      </div>
    </div>
  )
}

export default ParserForm