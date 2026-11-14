"""Optional true Local/Cloud free-form AI dialogue on the single AETHERION Server.

No hidden cloud fallback, tool execution, clinical diagnosis, persistent chat
store or invented model output. Requires an authenticated Server user.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Literal
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler, Request

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from .admin_control import probe_local_ai, read_ai_settings, validate_local_url
from .cloud_ai_runtime import cloud_public_status, resolve_cloud_configuration


class ChatLine(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=3000)


class FreeChatRequest(BaseModel):
    messages: list[ChatLine] = Field(min_length=1, max_length=16)
    provider: Literal['local', 'cloud'] = 'local'
    cloud_consent: bool = False
    locale: Literal['vi', 'en'] = 'vi'

    @model_validator(mode='after')
    def valid_dialogue(self):
        if self.messages[-1].role != 'user':
            raise ValueError('Last message must be the user request')
        if sum(len(x.content) for x in self.messages) > 12000:
            raise ValueError('Conversation context exceeds 12000 characters')
        if self.provider == 'cloud' and not self.cloud_consent:
            raise ValueError('Explicit Cloud consent required before transmission')
        return self


def _cloud_ready() -> bool:
    # Either admin deliberately configured this process in memory, or an
    # explicitly opted-in environment provider exists. Neither is fake uptime.
    return resolve_cloud_configuration() is not None


def available_models(db: Path) -> dict:
    settings = read_ai_settings(db)
    is_local = settings.get('mode') == 'local_only' and bool(settings.get('local_model'))
    local = probe_local_ai(settings) if is_local else {'model_ready': False, 'selected_model': '', 'connection':'OFF'}
    cloud = cloud_public_status()
    return {
        'local_available': bool(local.get('model_ready')),
        'local_model': local.get('selected_model') if local.get('model_ready') else None,
        'cloud_available': cloud['enabled'],
        'cloud_model': cloud['model'],
        'cloud_provider': cloud['provider'],
        'cloud_source': cloud['source'],
        'cloud_tested': False,  # actual inference is not implied by configuration
        'cloud_requires_consent': True,
        'stored_by_server': False,
        'clinical_validation': False,
    }


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _invoke(url: str, payload: dict, headers: dict, *, timeout: int) -> dict:
    """No proxy, no redirect; bounded model answer; do not log secrets or health text."""
    req = Request(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                  method='POST', headers=headers)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError('Model returned non-200 status')
            data = response.read(48_001)
            if len(data) > 48_000:
                raise ValueError('Model response too large')
            body = json.loads(data)
            if not isinstance(body, dict):
                raise ValueError('Invalid model response')
            return body
    except (HTTPError, URLError, OSError, ValueError, TypeError) as exc:
        raise HTTPException(503, detail='Configured model unavailable; no answer was generated') from exc


SYSTEM_VI = (
    'Bạn là trợ lý khoa học sức khỏe AETHERION. Trả lời hội thoại tự nhiên bằng tiếng Việt. '
    'Bạn không phải bác sĩ đang khám bệnh; không khẳng định chẩn đoán, không tự tạo thông số y khoa, '
    'không quyết định cấp cứu hoặc kê toa/đưa liều thuốc cá nhân hóa. '
    'Thông tin không chắc phải nói rõ. Không bịa trích dẫn NASA. '
    'Nếu người dùng mô tả tình huống khẩn cấp, khuyên tìm hỗ trợ y tế trực tiếp ngay. '
    'Không yêu cầu người dùng tiết lộ dữ liệu định danh.'
)
SYSTEM_EN = (
    'You are the AETHERION health-science conversational assistant. Respond in English. '
    'You are not conducting a medical examination. Do not assert a diagnosis, fabricate recorded measurements, '
    'make emergency-service decisions, or prescribe personalized medication/doses. '
    'Communicate uncertainty, do not invent NASA citations, advise human emergency care when symptoms may be urgent, '
    'and do not request identifying health information.'
)


def ask_model(db: Path, request: FreeChatRequest) -> dict:
    prompt = {'role':'system', 'content':SYSTEM_VI if request.locale == 'vi' else SYSTEM_EN}
    messages = [prompt] + [x.model_dump() for x in request.messages]
    if request.provider == 'local':
        settings = read_ai_settings(db)
        if settings.get('mode') != 'local_only' or not settings.get('local_model'):
            raise HTTPException(503, detail='Local AI not activated by Server Admin')
        available = probe_local_ai(settings)
        if not available.get('model_ready'):
            raise HTTPException(503, detail='Selected local AI model not installed or offline')
        base = validate_local_url(str(settings['local_url']))
        model = str(settings['local_model'])
        payload = {'model': model, 'stream': False, 'messages': messages,
                   'options': {'temperature':0.25, 'num_predict':750}}
        body = _invoke(base+'/api/chat',payload,{'Content-Type':'application/json'},
                       timeout=min(30, int(settings['timeout_seconds'])))
        reply = (body.get('message') or {}).get('content')
        provider, cloud_used = 'local', False
    else:
        if not request.cloud_consent:
            raise HTTPException(403, detail='Cloud consent required')
        config = resolve_cloud_configuration()
        if config is None:
            raise HTTPException(503, detail='Cloud AI not configured by Server administrator')
        # OnePad's provider dispatch, ported to this ONE server. Fixed upstream
        # hosts, no user-selected URL, no secret exposed in request/response.
        model = config.model
        if config.provider == 'gemini':
            payload = {
                'systemInstruction': {'parts': [{'text':prompt['content']}]},
                'contents': [
                    {'role': 'model' if row['role'] == 'assistant' else 'user',
                     'parts': [{'text':row['content']}]}
                    for row in messages[1:]
                ],
                'generationConfig': {'temperature':0.25,'maxOutputTokens':750},
            }
            body = _invoke(
                'https://generativelanguage.googleapis.com/v1beta/models/'
                + model + ':generateContent',
                payload,
                {'Content-Type':'application/json', 'x-goog-api-key':config.api_key},
                timeout=25,
            )
            try:
                parts = body['candidates'][0]['content']['parts']
                reply = ''.join(p['text'] for p in parts
                                if isinstance(p, dict) and isinstance(p.get('text'), str))
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise HTTPException(503, detail='Gemini provider returned no text') from exc
        else:
            # Newer OpenAI chat models reject deprecated max_tokens and can
            # reject custom temperature. Keep the broadly compatible fields.
            payload = {'model':model,'messages':messages,
                       'max_completion_tokens':750,'store':False}
            body = _invoke(
                'https://api.openai.com/v1/chat/completions',payload,
                {'Content-Type':'application/json',
                 'Authorization':'Bearer '+config.api_key},timeout=25,
            )
            try:
                reply = body['choices'][0]['message']['content']
            except (KeyError, IndexError, TypeError) as exc:
                raise HTTPException(503, detail='OpenAI provider returned no text') from exc
        provider, cloud_used = 'cloud', True
    if not isinstance(reply, str) or not reply.strip() or len(reply) > 12000:
        raise HTTPException(503, detail='Configured model returned an invalid answer')
    return {
        'reply':reply.strip(), 'model':model, 'provider':provider,
        'cloud_used':cloud_used,
        'cloud_provider':config.provider if cloud_used else None,
        'stored_by_server':False,
        'clinical_validation':False, 'medical_decision':'NOT_PERFORMED',
        'sources':[], 'notice':'AI-generated conversation; not verified NASA or clinical guidance.'
    }



def test_cloud_connection(db: Path) -> dict:
    """Real no-patient-data inference; administrative action only.

    Never claims READY from a configured key alone, never discloses model text,
    provider secrets, or any user's medical context in a test.
    """
    import time
    config = resolve_cloud_configuration()
    if config is None:
        raise HTTPException(503, detail='Cloud provider and API key not configured')
    start = time.monotonic()
    result = ask_model(db, FreeChatRequest(
        messages=[ChatLine(role='user',content='Reply only: connection_ok')],
        provider='cloud', cloud_consent=True, locale='en',
    ))
    if not isinstance(result.get('reply'), str) or not result['reply'].strip():
        raise HTTPException(503, detail='Cloud model did not generate a reply')
    return {
        'status':'READY','provider':config.provider,'model':config.model,
        'latency_ms':round((time.monotonic()-start)*1000),
        'actual_inference':True,
    }


def build_assistant_router(db_path: Callable[[], Path], require_session: Callable) -> APIRouter:
    router=APIRouter(prefix='/api/v1/assistant',tags=['Optional real AI conversation'])

    @router.get('/status')
    def status(identity: tuple[dict, str] = Depends(require_session)):
        return available_models(db_path())

    @router.post('/chat')
    def chat(req: FreeChatRequest, identity: tuple[dict, str] = Depends(require_session)):
        return ask_model(db_path(),req)

    return router
