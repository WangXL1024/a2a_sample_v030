# config/settings.py
REMOTE_AGENTS = {
    'coding_agent': {
        'host': 'localhost',
        'port': 10010,
        'description': 'An Agent for Coding'
    },
    'Automobile_Recommendation_Agent': {
        'host': 'localhost',
        'port': 10020,
        'description': 'Query relevant data from the database for automobile recommendation to user'
    },
    'Loan_Scheme_Suggestion_Agent': {
        'host': 'localhost',
        'port': 10030,
        'description': 'Give the loan scheme suggestion to user'
    },
    'Loan Pre-examination Agent': {
        'host': 'localhost',
        'port': 10040,
        'description': 'Based on the user basic information, conduct a loan pre-examination'
    },
    'chat_agent': {
        'host': 'localhost',
        'port': 10050,
        'description': 'An Agent for other chatting'
    },
}
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 9001,
    'timeout': 30
}