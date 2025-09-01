#!/usr/bin/env python3
"""
환경설정 관리 모듈
GitHub Actions Secrets에서 환경변수를 불러와 설정 관리
"""
import os
from typing import Optional

class Settings:
    """설정 관리 클래스"""
    
    def __init__(self):
        # 서버 URL 설정 (기본값: 로컬 개발 서버)
        self.SERVER_URL = os.getenv(
            'SERVER_URL', 
            'http://localhost:8000'
        )
        
        # 디스코드 웹훅 URL
        self.DISCORD_HEART_URL = os.getenv('DISCORD_HEART_URL')
        
        # 검증
        self._validate_settings()
    
    def _validate_settings(self):
        """설정값 검증"""
        if not self.DISCORD_HEART_URL:
            raise ValueError(
                "DISCORD_HEART_URL 환경변수가 설정되지 않았습니다. "
                "GitHub Secrets에 DISCORD_HEART_URL을 설정해주세요."
            )
        
        if not self.SERVER_URL:
            raise ValueError("SERVER_URL이 설정되지 않았습니다.")
    
    def __repr__(self):
        return f"Settings(SERVER_URL={self.SERVER_URL}, DISCORD_HEART_URL={'*' * 10 if self.DISCORD_HEART_URL else None})"

# 전역 설정 인스턴스
settings = Settings()