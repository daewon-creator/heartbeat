#!/usr/bin/env python3
"""
독립적인 API 모니터링 스크립트
FastAPI 서버와 별개로 실행되어 서버 상태를 체크하고 디스코드로 알림 전송
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import pytz
from config import settings
import requests

# 로깅 설정 (콘솔에만 출력)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class APIMonitor:
    def __init__(self):
        self.api_url = f"{settings.SERVER_URL}"
        self.discord_webhook = settings.DISCORD_HEART_URL
        self.check_interval = 60  # 1분마다 체크
        self.last_status = None
        
    async def check_api_health(self):
        """API 헬스체크"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/health", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': 'healthy',
                            'response_time': response.headers.get('X-Process-Time', 'unknown'),
                            'data': data
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'error': f'HTTP {response.status}',
                        }
        except aiohttp.ClientConnectorError:
            return {
                'status': 'down',
                'error': 'Connection refused - 서버가 실행되지 않음'
            }
        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Request timeout (10s)'
            }
        except Exception as e:
            return {
                'status': 'unhealthy', 
                'error': str(e)
            }
    
    def send_discord_notification(self, message):
        """디스코드 알림 전송 (동기 버전)"""
        try:
            payload = {
                "content": message,
                "username": "독립모니터봇"
            }
            
            response = requests.post(
                self.discord_webhook, 
                data=json.dumps(payload), 
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info("디스코드 알림 전송 성공")
            else:
                logger.error(f"디스코드 알림 전송 실패: {response.status_code}")
                
        except Exception as e:
            logger.error(f"디스코드 알림 전송 에러: {e}")
    
    async def run_single_check(self):
        """단일 헬스 체크 실행 (GitHub Actions용)"""
        logger.info("API 헬스 체크 실행...")
        logger.info(f"서버 URL: {self.api_url}")
        logger.info(f"디스코드 웹훅 전체 URL: {self.discord_webhook}")
        
        try:
            health_result = await self.check_api_health()
            current_status = health_result['status']
            
            # 한국 시간대로 변환
            kst = pytz.timezone('Asia/Seoul')
            now_kst = datetime.now(kst)
            timestamp = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')
            
            # 통신이 안될 때만 디스코드로 알림
            logger.info(f"Status: {current_status}")
            
            if current_status != 'healthy':
                if current_status == 'down':
                    message = (
                        f"🔴 **API 서버 다운** 🔴\n"
                        f"🕐 **시간**: {timestamp}\n"
                        f"💀 **상태**: 서버 응답 없음\n"
                        f"❌ **에러**: {health_result.get('error', 'Unknown error')}\n"
                        f"🌐 **서버**: {self.api_url}"
                    )
                else:  # unhealthy
                    message = (
                        f"⚠️ **API 문제 발생** ⚠️\n"
                        f"🕐 **시간**: {timestamp}\n"
                        f"🟡 **상태**: 서버 응답 불량\n"
                        f"❌ **에러**: {health_result.get('error', 'Unknown error')}\n"
                        f"🌐 **서버**: {self.api_url}"
                    )
                
                self.send_discord_notification(message)
            else:
                logger.info("서버 정상 - 디스코드 알림 생략")
            
        except Exception as e:
            logger.error(f"모니터링 에러: {e}")
            # 에러 발생시에도 디스코드로 알림
            kst = pytz.timezone('Asia/Seoul')
            now_kst = datetime.now(kst)
            timestamp = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')
            error_message = (
                f"💥 **모니터링 스크립트 에러** 💥\n"
                f"🕐 **시간**: {timestamp}\n"
                f"❌ **에러**: {str(e)}\n"
                f"🌐 **서버**: {self.api_url}"
            )
            self.send_discord_notification(error_message)

async def main():
    monitor = APIMonitor()
    await monitor.run_single_check()

if __name__ == "__main__":
    asyncio.run(main())