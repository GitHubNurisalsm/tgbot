# rating.py
"""
Модуль для системы рейтингов, отзывов и репутации пользователей
"""
import json
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

class RatingSystem:
    """Система рейтингов и отзывов"""
    
    def __init__(self):
        self.ratings_file = "data/user_ratings.json"
        self.reviews_file = "data/user_reviews.json"
        self.stats_file = "data/user_stats.json"
        self._init_data_files()
    
    def _init_data_files(self):
        """Инициализирует файлы данных"""
        os.makedirs("data", exist_ok=True)
        
        for file_path in [self.ratings_file, self.reviews_file, self.stats_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False)
    
    def update_rating(self, user_id: int, rating_change: float, review_id: Optional[int] = None):
        """Обновляет рейтинг пользователя"""
        with open(self.ratings_file, 'r', encoding='utf-8') as f:
            ratings = json.load(f)
        
        user_str = str(user_id)
        
        if user_str not in ratings:
            ratings[user_str] = {
                'current_rating': 5.0,  # Начальный рейтинг
                'total_reviews': 0,
                'positive_reviews': 0,
                'negative_reviews': 0,
                'total_rating_sum': 0,
                'last_updated': datetime.now().isoformat(),
                'review_ids': []
            }
        
        user_data = ratings[user_str]
        
        # Обновляем рейтинг (сглаженное среднее)
        old_rating = user_data['current_rating']
        total_reviews = user_data['total_reviews']
        
        # Формула для обновления рейтинга с учетом количества отзывов
        if total_reviews == 0:
            new_rating = rating_change
        else:
            # Взвешенное обновление (новые отзывы имеют больший вес)
            weight = min(0.3, 1.0 / (total_reviews + 1))
            new_rating = old_rating * (1 - weight) + rating_change * weight
        
        # Ограничиваем рейтинг от 0 до 5
        new_rating = max(0.0, min(5.0, new_rating))
        
        # Обновляем статистику
        user_data['current_rating'] = round(new_rating, 2)
        user_data['total_reviews'] += 1
        user_data['total_rating_sum'] += rating_change
        
        if rating_change >= 3.0:
            user_data['positive_reviews'] += 1
        else:
            user_data['negative_reviews'] += 1
        
        user_data['last_updated'] = datetime.now().isoformat()
        
        if review_id:
            if 'review_ids' not in user_data:
                user_data['review_ids'] = []
            user_data['review_ids'].append(review_id)
        
        with open(self.ratings_file, 'w', encoding='utf-8') as f:
            json.dump(ratings, f, ensure_ascii=False, indent=2)
        
        # Обновляем статистику пользователя
        self._update_user_stats(user_id, rating_change >= 3.0)
        
        return new_rating
    
    def _update_user_stats(self, user_id: int, is_positive: bool):
        """Обновляет статистику пользователя"""
        with open(self.stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        user_str = str(user_id)
        today = datetime.now().strftime('%Y-%m-%d')
        
        if user_str not in stats:
            stats[user_str] = {
                'total_completed': 0,
                'monthly_completed': {},
                'positive_rate': 0,
                'response_time_avg': 0,
                'reliability_score': 100
            }
        
        user_stats = stats[user_str]
        user_stats['total_completed'] += 1
        
        # Обновляем месячную статистику
        if today not in user_stats['monthly_completed']:
            user_stats['monthly_completed'][today] = 0
        user_stats['monthly_completed'][today] += 1
        
        # Обновляем показатель положительных отзывов
        if is_positive:
            total = user_stats.get('positive_count', 0) + 1
            user_stats['positive_count'] = total
            user_stats['positive_rate'] = round((total / user_stats['total_completed']) * 100, 1)
        
        # Рассчитываем reliability score (коэффициент надежности)
        completed = user_stats['total_completed']
        positive_rate = user_stats.get('positive_rate', 100)
        
        # Формула: учитываем количество выполненных задач и положительные отзывы
        reliability = (completed * 0.3 + positive_rate * 0.7) / 100 * 100
        user_stats['reliability_score'] = round(min(100, reliability), 1)
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def add_review(self, reviewer_id: int, reviewed_id: int, rating: float, 
                  comment: str, request_id: Optional[int] = None) -> int:
        """Добавляет отзыв о пользователе"""
        with open(self.reviews_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        review_id = len(reviews) + 1
        
        review = {
            'id': review_id,
            'reviewer_id': reviewer_id,
            'reviewed_id': reviewed_id,
            'rating': rating,
            'comment': comment,
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'is_verified': True,
            'likes': 0,
            'dislikes': 0
        }
        
        reviews[str(review_id)] = review
        
        with open(self.reviews_file, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        
        # Обновляем рейтинг пользователя
        self.update_rating(reviewed_id, rating, review_id)
        
        return review_id
    
    def get_user_rating(self, user_id: int) -> Dict[str, Any]:
        """Получает рейтинг пользователя"""
        with open(self.ratings_file, 'r', encoding='utf-8') as f:
            ratings = json.load(f)
        
        user_str = str(user_id)
        
        if user_str not in ratings:
            return {
                'current_rating': 5.0,
                'total_reviews': 0,
                'positive_reviews': 0,
                'negative_reviews': 0,
                'rating_stars': '⭐⭐⭐⭐⭐',
                'has_rating': False
            }
        
        user_data = ratings[user_str]
        
        # Рассчитываем звездный рейтинг
        rating = user_data['current_rating']
        full_stars = int(rating)
        half_star = 1 if rating - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        stars = '⭐' * full_stars + '⭐' if half_star else '' + '☆' * empty_stars
        
        return {
            'current_rating': rating,
            'total_reviews': user_data['total_reviews'],
            'positive_reviews': user_data.get('positive_reviews', 0),
            'negative_reviews': user_data.get('negative_reviews', 0),
            'rating_stars': stars,
            'last_updated': user_data.get('last_updated'),
            'has_rating': user_data['total_reviews'] > 0
        }
    
    def get_user_reviews(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Получает отзывы о пользователе"""
        with open(self.reviews_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        user_reviews = []
        
        for review_id, review in reviews.items():
            if review['reviewed_id'] == user_id:
                user_reviews.append(review)
        
        # Сортируем по дате (сначала новые)
        user_reviews.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return user_reviews[:limit]
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику пользователя"""
        with open(self.stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        user_str = str(user_id)
        
        if user_str not in stats:
            return {
                'total_completed': 0,
                'monthly_completed': 0,
                'positive_rate': 100,
                'response_time_avg': 0,
                'reliability_score': 100,
                'level': 1,
                'experience': 0
            }
        
        user_stats = stats[user_str]
        
        # Рассчитываем месячное количество
        monthly_completed = sum(user_stats.get('monthly_completed', {}).values())
        
        # Рассчитываем уровень пользователя
        total_completed = user_stats.get('total_completed', 0)
        level = self._calculate_level(total_completed)
        experience = self._calculate_experience(total_completed)
        
        return {
            'total_completed': total_completed,
            'monthly_completed': monthly_completed,
            'positive_rate': user_stats.get('positive_rate', 100),
            'response_time_avg': user_stats.get('response_time_avg', 0),
            'reliability_score': user_stats.get('reliability_score', 100),
            'level': level,
            'experience': experience,
            'next_level_exp': self._exp_for_level(level + 1)
        }
    
    def _calculate_level(self, completed_tasks: int) -> int:
        """Рассчитывает уровень пользователя на основе выполненных задач"""
        # Формула: уровень = floor(log2(задач + 1)) + 1
        if completed_tasks == 0:
            return 1
        
        level = int(math.log2(completed_tasks + 1)) + 1
        return min(level, 50)  # Максимальный уровень 50
    
    def _calculate_experience(self, completed_tasks: int) -> int:
        """Рассчитывает текущий опыт пользователя"""
        current_level = self._calculate_level(completed_tasks)
        exp_for_current = self._exp_for_level(current_level)
        exp_for_next = self._exp_for_level(current_level + 1)
        
        # Процент заполнения до следующего уровня
        tasks_for_current = 2 ** (current_level - 1) - 1
        tasks_needed_for_next = 2 ** current_level - 1
        
        if tasks_needed_for_next == tasks_for_current:
            return 100
        
        progress = (completed_tasks - tasks_for_current) / (tasks_needed_for_next - tasks_for_current)
        return int(progress * 100)
    
    def _exp_for_level(self, level: int) -> int:
        """Опыт, необходимый для достижения уровня"""
        return 2 ** (level - 1) - 1
    
    def get_top_users(self, limit: int = 10, category: Optional[str] = None) -> List[Dict]:
        """Получает топ пользователей"""
        with open(self.ratings_file, 'r', encoding='utf-8') as f:
            ratings = json.load(f)
        
        top_users = []
        
        for user_id_str, user_data in ratings.items():
            if user_data.get('total_reviews', 0) >= 3:  # Только пользователи с минимум 3 отзывами
                user_id = int(user_id_str)
                stats = self.get_user_stats(user_id)
                
                # Рейтинговая формула: учитываем рейтинг, надежность и количество отзывов
                rating_score = user_data['current_rating']
                reliability_score = stats['reliability_score'] / 100
                review_count_bonus = min(user_data['total_reviews'] * 0.1, 2.0)  # Бонус за количество отзывов
                
                total_score = (rating_score * 0.4 + reliability_score * 4 * 0.4 + review_count_bonus * 0.2)
                
                top_users.append({
                    'user_id': user_id,
                    'rating': user_data['current_rating'],
                    'total_reviews': user_data['total_reviews'],
                    'total_score': total_score,
                    'reliability_score': stats['reliability_score'],
                    'level': stats['level']
                })
        
        # Сортируем по общему баллу
        top_users.sort(key=lambda x: x['total_score'], reverse=True)
        
        return top_users[:limit]
    
    def like_review(self, review_id: int):
        """Ставит лайк отзыву"""
        with open(self.reviews_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        review_str = str(review_id)
        if review_str in reviews:
            reviews[review_str]['likes'] = reviews[review_str].get('likes', 0) + 1
        
        with open(self.reviews_file, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
    
    def dislike_review(self, review_id: int):
        """Ставит дизлайк отзыву"""
        with open(self.reviews_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        review_str = str(review_id)
        if review_str in reviews:
            reviews[review_str]['dislikes'] = reviews[review_str].get('dislikes', 0) + 1
        
        with open(self.reviews_file, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)

# Создаем глобальный экземпляр системы рейтингов
rating_system = RatingSystem()

# Константы состояний для ConversationHandler
REVIEW_RATING, REVIEW_COMMENT = range(30, 32)

# Клавиатуры
def get_rating_main_keyboard():
    """Основная клавиатура раздела рейтингов"""
    keyboard = [
        [KeyboardButton("⭐ Рейтинг"), KeyboardButton("🏆 Топ пользователей")],
        [KeyboardButton("📝 Мои отзывы"), KeyboardButton("👥 Отзывы обо мне")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("🎖️ Уровни и достижения")],
        [KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_rating_stars_keyboard():
    """Клавиатура для выбора рейтинга (звезды)"""
    keyboard = [
        [
            InlineKeyboardButton("1 ⭐", callback_data="rate_star_1"),
            InlineKeyboardButton("2 ⭐⭐", callback_data="rate_star_2"),
            InlineKeyboardButton("3 ⭐⭐⭐", callback_data="rate_star_3")
        ],
        [
            InlineKeyboardButton("4 ⭐⭐⭐⭐", callback_data="rate_star_4"),
            InlineKeyboardButton("5 ⭐⭐⭐⭐⭐", callback_data="rate_star_5")
        ],
        [
            InlineKeyboardButton("🔙 Отмена", callback_data="rate_cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_review_actions_keyboard(review_id: int):
    """Клавиатура действий с отзывом"""
    keyboard = [
        [
            InlineKeyboardButton("👍", callback_data=f"like_review_{review_id}"),
            InlineKeyboardButton("👎", callback_data=f"dislike_review_{review_id}")
        ],
        [
            InlineKeyboardButton("📋 К профилю", callback_data=f"view_profile_review_{review_id}"),
            InlineKeyboardButton("⚠️ Пожаловаться", callback_data=f"report_review_{review_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_level_progress_bar(current_exp: int) -> str:
    """Создает прогресс-бар уровня"""
    bars = 10
    filled = int(current_exp / 10)
    empty = bars - filled
    
    return "▓" * filled + "░" * empty + f" {current_exp}%"

# Обработчики команд
async def show_rating_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню рейтингов"""
    await update.message.reply_text(
        "⭐ *Система рейтингов и отзывов*\n\n"
        "Здесь вы можете:\n"
        "• Просмотреть свой рейтинг и статистику\n"
        "• Ознакомиться с топом пользователей\n"
        "• Увидеть отзывы о себе и о других\n"
        "• Отслеживать свой прогресс и уровень\n\n"
        "Выберите действие:",
        reply_markup=get_rating_main_keyboard(),
        parse_mode='Markdown'
    )

async def show_my_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает рейтинг текущего пользователя"""
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Получаем данные рейтинга
    rating_data = rating_system.get_user_rating(user_id)
    stats_data = rating_system.get_user_stats(user_id)
    
    # Формируем сообщение
    message_text = f"⭐ *Рейтинг пользователя* @{user.username or user.first_name}\n\n"
    
    message_text += f"📊 *Общий рейтинг:* {rating_data['rating_stars']}\n"
    message_text += f"   {rating_data['current_rating']}/5.0\n\n"
    
    message_text += f"📈 *Статистика отзывов:*\n"
    message_text += f"   Всего отзывов: {rating_data['total_reviews']}\n"
    message_text += f"   👍 Положительных: {rating_data['positive_reviews']}\n"
    message_text += f"   👎 Отрицательных: {rating_data['negative_reviews']}\n\n"
    
    message_text += f"🎯 *Показатели надежности:*\n"
    message_text += f"   Надежность: {stats_data['reliability_score']}%\n"
    message_text += f"   Положительных: {stats_data['positive_rate']}%\n"
    message_text += f"   Выполнено задач: {stats_data['total_completed']}\n"
    message_text += f"   За месяц: {stats_data['monthly_completed']}\n\n"
    
    message_text += f"🎖️ *Уровень:* {stats_data['level']}\n"
    message_text += f"   Прогресс: {get_level_progress_bar(stats_data['experience'])}\n"
    message_text += f"   До след. уровня: {stats_data['next_level_exp'] - stats_data['total_completed']} задач\n"
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Оставить отзыв о себе", callback_data="review_self"),
            InlineKeyboardButton("🏆 Сравнить с топом", callback_data="compare_top")
        ]
    ]
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает топ пользователей"""
    top_users = rating_system.get_top_users(limit=10)
    
    if not top_users:
        await update.message.reply_text(
            "🏆 *Топ пользователей*\n\n"
            "Пока нет пользователей с достаточным количеством отзывов.\n"
            "Будьте первым!",
            parse_mode='Markdown',
            reply_markup=get_rating_main_keyboard()
        )
        return
    
    await update.message.reply_text(
        "🏆 *ТОП-10 пользователей*\n\n"
        "Рейтинг рассчитывается на основе:\n"
        "• Среднего рейтинга (40%)\n"
        "• Надежности (40%)\n"
        "• Количества отзывов (20%)\n",
        parse_mode='Markdown'
    )
    
    for i, user in enumerate(top_users, 1):
        # Здесь нужно получить username пользователя
        # Для примера используем ID
        user_info = f"👤 Пользователь #{user['user_id']}"
        
        user_text = (
            f"{i}. {user_info}\n"
            f"   ⭐ {user['rating']}/5.0 ({user['total_reviews']} отзывов)\n"
            f"   🛡️ Надежность: {user['reliability_score']}%\n"
            f"   🎖️ Уровень: {user['level']}\n"
            f"   📊 Балл: {user['total_score']:.2f}"
        )
        
        keyboard = [[
            InlineKeyboardButton("👤 Профиль", callback_data=f"view_top_profile_{user['user_id']}"),
            InlineKeyboardButton("📝 Отзывы", callback_data=f"view_top_reviews_{user['user_id']}")
        ]]
        
        await update.message.reply_text(
            user_text,
            reply_markup=InlineKeyboardMarkup(keyboard) if i <= 3 else None,
            parse_mode='Markdown'
        )
    
    await update.message.reply_text(
        "Продолжайте работать качественно, чтобы попасть в топ!",
        reply_markup=get_rating_main_keyboard()
    )

async def show_my_reviews_given(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает отзывы, которые оставил пользователь"""
    user_id = update.effective_user.id
    reviews = rating_system.get_user_reviews(user_id)
    
    # Фильтруем только те отзывы, где пользователь был рецензентом
    # Для этого нужно пересмотреть структуру данных или сделать отдельный метод
    
    await update.message.reply_text(
        "📝 *Мои отзывы*\n\n"
        "Отзывы, которые вы оставили другим пользователям, "
        "будут отображаться здесь.\n\n"
        "Функция в разработке...",
        parse_mode='Markdown',
        reply_markup=get_rating_main_keyboard()
    )

async def show_reviews_about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает отзывы о текущем пользователе"""
    user_id = update.effective_user.id
    reviews = rating_system.get_user_reviews(user_id)
    
    if not reviews:
        await update.message.reply_text(
            "👥 *Отзывы обо мне*\n\n"
            "Пока нет отзывов о вас.\n"
            "Отзывы появятся после завершения сотрудничества с другими пользователями.",
            parse_mode='Markdown',
            reply_markup=get_rating_main_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"👥 *Отзывы обо мне ({len(reviews)})*\n\n"
        "👇 Последние отзывы:",
        parse_mode='Markdown'
    )
    
    for review in reviews[:3]:  # Показываем последние 3 отзыва
        stars = "⭐" * int(review['rating']) + "☆" * (5 - int(review['rating']))
        time_ago = get_time_ago(review['timestamp'])
        
        review_text = (
            f"⭐ {stars} ({review['rating']}/5)\n"
            f"📝 {review['comment'][:150]}...\n"
            f"🕐 {time_ago}\n"
            f"👍 {review.get('likes', 0)} 👎 {review.get('dislikes', 0)}"
        )
        
        if review.get('request_id'):
            review_text += f"\n📋 К запросу: #{review['request_id']}"
        
        await update.message.reply_text(
            review_text,
            reply_markup=get_review_actions_keyboard(review['id']),
            parse_mode='Markdown'
        )
    
    if len(reviews) > 3:
        await update.message.reply_text(
            f"И еще {len(reviews) - 3} отзывов...",
            reply_markup=get_rating_main_keyboard()
        )

async def show_detailed_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает подробную статистику"""
    user_id = update.effective_user.id
    stats = rating_system.get_user_stats(user_id)
    rating = rating_system.get_user_rating(user_id)
    
    # Рассчитываем дополнительные метрики
    completion_rate = min(100, (stats['total_completed'] / (stats['total_completed'] + 5)) * 100)
    response_score = min(100, 100 - (stats.get('response_time_avg', 0) / 24) * 100)
    
    message_text = (
        "📊 *Подробная статистика*\n\n"
        
        "🎯 *Основные показатели:*\n"
        f"• Уровень: {stats['level']} ({stats['experience']}%)\n"
        f"• Выполнено задач: {stats['total_completed']}\n"
        f"• За месяц: {stats['monthly_completed']}\n"
        f"• Рейтинг: {rating['current_rating']}/5.0\n\n"
        
        "🛡️ *Надежность:*\n"
        f"• Общий score: {stats['reliability_score']}%\n"
        f"• Положительных отзывов: {stats['positive_rate']}%\n"
        f"• Rate выполнения: {completion_rate:.1f}%\n"
        f"• Скорость ответа: {response_score:.1f}%\n\n"
        
        "📈 *Аналитика:*\n"
    )
    
    if stats['total_completed'] > 0:
        avg_per_month = stats['monthly_completed'] / 30  # Примерно за месяц
        message_text += f"• Среднее в день: {avg_per_month:.1f}\n"
        
        if stats['level'] < 10:
            message_text += f"• До след. уровня: {stats['next_level_exp'] - stats['total_completed']} задач\n"
        
        # Рекомендации
        message_text += "\n💡 *Рекомендации:*\n"
        
        if rating['total_reviews'] < 3:
            message_text += "• Получите больше отзывов для повышения рейтинга\n"
        
        if stats['monthly_completed'] < 5:
            message_text += "• Выполняйте больше задач для роста уровня\n"
        
        if stats['positive_rate'] < 90:
            message_text += "• Улучшите качество работы для повышения положительных отзывов\n"
    
    await update.message.reply_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=get_rating_main_keyboard()
    )

async def show_levels_and_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает систему уровней и достижений"""
    user_id = update.effective_user.id
    stats = rating_system.get_user_stats(user_id)
    
    message_text = (
        "🎖️ *Система уровней и достижений*\n\n"
        
        "📊 *Ваш прогресс:*\n"
        f"• Текущий уровень: {stats['level']}\n"
        f"• Опыт: {stats['experience']}%\n"
        f"• Выполнено задач: {stats['total_completed']}\n"
        f"• До след. уровня: {max(0, stats['next_level_exp'] - stats['total_completed'])} задач\n\n"
        
        "📈 *Как растет уровень:*\n"
        "Уровень = log₂(выполненных задач + 1) + 1\n\n"
        
        "🏆 *Бонусы уровней:*\n"
        "• Уровень 5: Значок ⭐\n"
        "• Уровень 10: Значок 🌟\n"
        "• Уровень 20: Значок 🏆\n"
        "• Уровень 30: Значок 👑\n"
        "• Уровень 40: Значок 💎\n"
        "• Уровень 50: Легендарный статус\n\n"
        
        "🎯 *Текущие достижения:*\n"
    )
    
    # Проверяем достижения
    achievements = []
    
    if stats['total_completed'] >= 1:
        achievements.append("✅ Первая задача")
    if stats['total_completed'] >= 10:
        achievements.append("✅ 10 задач")
    if stats['total_completed'] >= 50:
        achievements.append("✅ 50 задач")
    if stats['total_completed'] >= 100:
        achievements.append("✅ 100 задач")
    
    if stats['positive_rate'] >= 90:
        achievements.append("✅ Высокое качество")
    if stats['monthly_completed'] >= 20:
        achievements.append("✅ Активный месяц")
    
    if achievements:
        for achievement in achievements:
            message_text += f"• {achievement}\n"
    else:
        message_text += "Пока нет достижений. Продолжайте работать!\n"
    
    # Следующие цели
    message_text += "\n🎯 *Ближайшие цели:*\n"
    
    if stats['level'] < 5:
        tasks_needed = stats['next_level_exp'] - stats['total_completed']
        message_text += f"• Уровень {stats['level'] + 1}: {tasks_needed} задач\n"
    
    if stats['total_completed'] < 10:
        message_text += f"• 10 задач: {10 - stats['total_completed']} осталось\n"
    
    await update.message.reply_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=get_rating_main_keyboard()
    )

def get_time_ago(timestamp_str: str) -> str:
    """Возвращает строку 'сколько времени назад'"""
    timestamp = datetime.fromisoformat(timestamp_str)
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} дн. назад"
    elif diff.seconds // 3600 > 0:
        return f"{diff.seconds // 3600} ч. назад"
    elif diff.seconds // 60 > 0:
        return f"{diff.seconds // 60} мин. назад"
    else:
        return "только что"

async def start_leave_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс оставления отзыва"""
    query = update.callback_query
    await query.answer()
    
    # Получаем данные из callback или контекста
    # Например: callback_data="review_user_123"
    
    await query.edit_message_text(
        "⭐ *Оставить отзыв*\n\n"
        "Выберите оценку (от 1 до 5 звезд):",
        reply_markup=get_rating_stars_keyboard()
    )
    return REVIEW_RATING

async def process_review_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор рейтинга для отзыва"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "rate_cancel":
        await query.edit_message_text(
            "Отмена оставления отзыва.",
            reply_markup=get_rating_main_keyboard()
        )
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    
    rating = int(query.data.replace("rate_star_", ""))
    context.user_data['review_rating'] = rating
    
    await query.edit_message_text(
        f"⭐ Выбрано: {rating} {'звезд' if rating > 1 else 'звезда'}\n\n"
        "Теперь напишите комментарий к отзыву:\n\n"
        "*Совет:* Опишите ваше впечатление от сотрудничества, "
        "что понравилось, что можно улучшить.\n\n"
        "Или напишите 'отмена' для отмены.",
        parse_mode='Markdown'
    )
    return REVIEW_COMMENT

async def save_user_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет отзыв о пользователе"""
    comment = update.message.text
    
    if comment.lower() in ['отмена', 'cancel', 'стоп']:
        await update.message.reply_text(
            "Отмена оставления отзыва.",
            reply_markup=get_rating_main_keyboard()
        )
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    
    rating = context.user_data.get('review_rating')
    user = update.effective_user
    
    # Здесь нужно получить ID пользователя, которому оставляем отзыв
    # Это может быть из context.user_data или другого источника
    reviewed_id = context.user_data.get('reviewed_user_id', user.id)  # По умолчанию себе
    
    # Сохраняем отзыв
    review_id = rating_system.add_review(
        reviewer_id=user.id,
        reviewed_id=reviewed_id,
        rating=float(rating),
        comment=comment,
        request_id=context.user_data.get('request_id')
    )
    
    # Очищаем временные данные
    context.user_data.clear()
    
    stars = "⭐" * rating + "☆" * (5 - rating)
    
    await update.message.reply_text(
        f"✅ *Отзыв сохранен!*\n\n"
        f"⭐ Оценка: {stars}\n"
        f"📝 Комментарий: {comment[:100]}...\n\n"
        f"Спасибо за ваш отзыв! Он помогает улучшать сообщество.",
        parse_mode='Markdown',
        reply_markup=get_rating_main_keyboard()
    )
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

async def cancel_rating_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущий процесс"""
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=get_rating_main_keyboard()
    )
    
    # Очищаем временные данные
    context.user_data.clear()
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

# Обработчик callback-запросов
async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия inline-кнопок в рейтингах"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("like_review_"):
        review_id = int(callback_data.replace("like_review_", ""))
        rating_system.like_review(review_id)
        
        await query.edit_message_text(
            "👍 Ваш лайк учтен!",
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("dislike_review_"):
        review_id = int(callback_data.replace("dislike_review_", ""))
        rating_system.dislike_review(review_id)
        
        await query.edit_message_text(
            "👎 Ваш дизлайк учтен!",
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("view_top_profile_"):
        user_id = int(callback_data.replace("view_top_profile_", ""))
        
        # Получаем информацию о пользователе
        rating_data = rating_system.get_user_rating(user_id)
        stats_data = rating_system.get_user_stats(user_id)
        
        profile_text = (
            f"👤 *Профиль пользователя #{user_id}*\n\n"
            f"⭐ Рейтинг: {rating_data['rating_stars']}\n"
            f"   {rating_data['current_rating']}/5.0 ({rating_data['total_reviews']} отзывов)\n\n"
            f"📊 Статистика:\n"
            f"• Уровень: {stats_data['level']}\n"
            f"• Надежность: {stats_data['reliability_score']}%\n"
            f"• Выполнено: {stats_data['total_completed']} задач\n"
            f"• Положительных: {stats_data['positive_rate']}%"
        )
        
        await query.edit_message_text(
            profile_text,
            parse_mode='Markdown'
        )
    
    elif callback_data == "review_self":
        # Начинаем процесс оставления отзыва о себе
        context.user_data['reviewed_user_id'] = query.from_user.id
        
        await query.edit_message_text(
            "⭐ *Оставить отзыв о себе*\n\n"
            "Вы можете оставить отзыв о своей работе. "
            "Это поможет другим пользователям лучше вас узнать.\n\n"
            "Выберите оценку:",
            reply_markup=get_rating_stars_keyboard()
        )
        return REVIEW_RATING
    
    elif callback_data == "compare_top":
        user_id = query.from_user.id
        user_stats = rating_system.get_user_stats(user_id)
        user_rating = rating_system.get_user_rating(user_id)
        top_users = rating_system.get_top_users(limit=1)
        
        if not top_users:
            await query.edit_message_text(
                "Пока нет топ пользователей для сравнения.",
                parse_mode='Markdown'
            )
            return
        
        top_user = top_users[0]
        
        comparison_text = (
            "🏆 *Сравнение с топом*\n\n"
            
            "📊 *Ваши показатели:*\n"
            f"• Рейтинг: {user_rating['current_rating']}/5.0\n"
            f"• Надежность: {user_stats['reliability_score']}%\n"
            f"• Уровень: {user_stats['level']}\n"
            f"• Задач: {user_stats['total_completed']}\n\n"
            
            "📈 *Топ-1 пользователь:*\n"
            f"• Рейтинг: {top_user['rating']}/5.0\n"
            f"• Надежность: {top_user['reliability_score']}%\n"
            f"• Уровень: {top_user['level']}\n"
            f"• Отзывов: {top_user['total_reviews']}\n\n"
            
            "🎯 *Что улучшить:*\n"
        )
        
        if user_rating['total_reviews'] < 3:
            comparison_text += "• Получите больше отзывов\n"
        if user_stats['total_completed'] < top_user.get('total_completed', 0) / 2:
            comparison_text += "• Выполняйте больше задач\n"
        if user_rating['current_rating'] < 4.5:
            comparison_text += "• Повышайте качество работы\n"
        
        comparison_text += "\nПродолжайте работать качественно!"
        
        await query.edit_message_text(
            comparison_text,
            parse_mode='Markdown'
        )