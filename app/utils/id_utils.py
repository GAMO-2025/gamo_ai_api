import random
import string

def generate_keyword_id():
    """랜덤 숫자+문자열 11자리 ID 생성"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=11))