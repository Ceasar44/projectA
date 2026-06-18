import base64
import hashlib
import hmac
from urllib.parse import parse_qsl
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_auth_context, get_session
from app.api.v1.chat import ChatRequest, chat as chat_completion
from app.domain.auth.schemas import AuthContext
from app.domain.conversation.schemas import ConversationCreate
from app.domain.conversation.service import ConversationService
from app.domain.channels.schemas import ChannelActionRequest, ChannelConfigUpdate, ChannelRead
from app.domain.channels.service import ChannelService
from app.infrastructure.db.models.conversations import Conversation
from app.infrastructure.db.models.operations import CallLog, Settings
from app.infrastructure.db.repositories.channels import ChannelRepository
from app.infrastructure.db.repositories.conversations import ConversationRepository, MessageRepository
from app.infrastructure.db.repositories.customers import CustomerRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()
CHANNEL_TYPES = ["whatsapp", "email", "phone", "sms", "telegram"]


def build_service(session: AsyncSession) -> ChannelService:
    return ChannelService(ChannelRepository(session), SQLAlchemyUnitOfWork(session))


def build_conversation_service(session: AsyncSession) -> ConversationService:
    return ConversationService(
        conversation_repo=ConversationRepository(session),
        message_repo=MessageRepository(session),
        customer_repo=CustomerRepository(session),
        uow=SQLAlchemyUnitOfWork(session),
    )


def _validate_channel_type(channel_type: str) -> ORJSONResponse | None:
    if channel_type not in CHANNEL_TYPES:
        return ORJSONResponse({"error": "Invalid channel type"}, status_code=400)
    return None


async def _get_channel_config(session: AsyncSession, channel_type: str) -> dict:
    item = await build_service(session).get_channel(channel_type)
    return item.config or {}


def _validate_twilio_signature(auth_token: str, signature: str, url: str, params: dict[str, str]) -> bool:
    if not auth_token or not signature:
        return False
    data = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    computed = base64.b64encode(hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest())
    provided = signature.encode("utf-8")
    return len(computed) == len(provided) and hmac.compare_digest(computed, provided)


def _twiml_gather(message: str, callback_url: str) -> str:
    safe_message = escape(message)
    safe_callback = escape(callback_url)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="alice">{safe_message}</Say>'
        f'<Gather input="speech" action="{safe_callback}" method="POST" speechTimeout="auto" language="auto">'
        '<Say voice="alice">I&apos;m listening.</Say>'
        "</Gather>"
        '<Say voice="alice">I didn&apos;t hear anything. Goodbye.</Say>'
        "</Response>"
    )


def _twiml_say(message: str) -> str:
    safe_message = escape(message)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="alice">{safe_message}</Say>'
        '<Gather input="speech" action="/api/channels/phone/gather" method="POST" speechTimeout="auto" language="auto">'
        '<Say voice="alice">Is there anything else I can help with?</Say>'
        "</Gather>"
        '<Say voice="alice">Thank you for calling. Goodbye.</Say>'
        "</Response>"
    )


async def _read_form_values(request: Request) -> dict[str, str]:
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        raw_body = (await request.body()).decode("utf-8")
        return {key: value for key, value in parse_qsl(raw_body, keep_blank_values=True)}
    form = await request.form()
    return {key: str(value) for key, value in form.items()}


@router.get("", response_model=list[ChannelRead])
async def list_channels(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[ChannelRead]:
    return await build_service(session).list_channels()


@router.post("", response_model=ChannelRead)
async def save_channel(
    payload: ChannelConfigUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ChannelRead:
    if not payload.type or payload.type not in CHANNEL_TYPES:
        return ORJSONResponse(
            {"error": "Invalid channel type. Must be one of: " + ", ".join(CHANNEL_TYPES)},
            status_code=400,
        )
    return await build_service(session).save_channel(payload)


@router.get("/whatsapp")
async def whatsapp_status(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    item = await build_service(session).get_channel("whatsapp")
    status_value = item.status or "disconnected"
    return {
        "status": "qr_ready" if (item.config or {}).get("qr") else status_value,
        "qr": (item.config or {}).get("qr"),
        "message": (item.config or {}).get("message")
        or ("Scan the QR code with WhatsApp on your phone" if (item.config or {}).get("qr") else "Disconnected"),
    }


@router.post("/whatsapp")
async def whatsapp_connect(
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    action = payload.get("action")
    if action == "connect":
        config = await _get_channel_config(session, "whatsapp")
        if not config:
            return ORJSONResponse({"error": "Channel must be configured before connecting"}, status_code=400)
        result = await build_service(session).perform_action("whatsapp", "connect")
        return {
            "status": "qr_ready" if result.get("qr") else result.get("status", "connecting"),
            "qr": result.get("qr"),
            "message": "Scan the QR code with WhatsApp on your phone" if result.get("qr") else result.get("message", ""),
        }
    if action == "disconnect":
        await build_service(session).perform_action("whatsapp", "disconnect")
        return {"status": "disconnected"}
    return ORJSONResponse({"error": "Invalid action"}, status_code=400)


@router.get("/email")
async def email_status(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    item = await build_service(session).get_channel("email")
    return {
        "connected": item.status == "connected",
        "status": item.status or "disconnected",
    }


@router.post("/email")
async def email_action(
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    action = payload.get("action")
    if action == "connect":
        config = await _get_channel_config(session, "email")
        if not config:
            return ORJSONResponse({"error": "Channel must be configured before connecting"}, status_code=400)
        result = await build_service(session).perform_action("email", "connect")
        return {"connected": result.get("status") == "connected", "status": result.get("status")}
    if action == "disconnect":
        await build_service(session).perform_action("email", "disconnect")
        return {"status": "disconnected"}
    return ORJSONResponse({"error": "Invalid action"}, status_code=400)


@router.get("/{channel_type}", response_model=ChannelRead)
async def get_channel(
    channel_type: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ChannelRead:
    invalid = _validate_channel_type(channel_type)
    if invalid:
        return invalid
    return await build_service(session).get_channel(channel_type)


@router.put("/{channel_type}", response_model=ChannelRead)
async def update_channel(
    channel_type: str,
    payload: ChannelConfigUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ChannelRead:
    invalid = _validate_channel_type(channel_type)
    if invalid:
        return invalid
    return await build_service(session).update_channel(channel_type, payload)


@router.post("/{channel_type}/action")
async def channel_action(
    channel_type: str,
    payload: ChannelActionRequest,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    invalid = _validate_channel_type(channel_type)
    if invalid:
        return invalid
    if payload.action not in {"connect", "disconnect", "test"}:
        return ORJSONResponse(
            {"error": "Invalid action. Must be one of: connect, disconnect, test"},
            status_code=400,
        )
    config = await _get_channel_config(session, channel_type)
    if payload.action in {"connect", "test"} and not config:
        return ORJSONResponse(
            {"error": "Channel must be configured before " + ("connecting" if payload.action == "connect" else "testing")},
            status_code=400,
        )
    return await build_service(session).perform_action(channel_type, payload.action)


@router.post("/{channel_type}")
async def channel_action_compat(
    channel_type: str,
    payload: ChannelActionRequest,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    invalid = _validate_channel_type(channel_type)
    if invalid:
        return invalid
    if payload.action not in {"connect", "disconnect", "test"}:
        return ORJSONResponse(
            {"error": "Invalid action. Must be one of: connect, disconnect, test"},
            status_code=400,
        )
    config = await _get_channel_config(session, channel_type)
    if payload.action in {"connect", "test"} and not config:
        return ORJSONResponse(
            {"error": "Channel must be configured before " + ("connecting" if payload.action == "connect" else "testing")},
            status_code=400,
        )
    return await build_service(session).perform_action(channel_type, payload.action)


@router.post("/phone/incoming")
async def phone_incoming(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Response:
    params = await _read_form_values(request)
    settings = await session.scalar(select(Settings).where(Settings.id == "default"))
    auth_token = settings.twilio_token if settings and settings.twilio_token else ""
    if auth_token:
        signature = request.headers.get("x-twilio-signature", "")
        if not _validate_twilio_signature(auth_token, signature, str(request.url), params):
            return Response(content="Forbidden", status_code=403)

    from_number = params.get("From", "")
    call_sid = params.get("CallSid", "")
    if settings and call_sid:
        existing_log = await session.scalar(select(CallLog).where(CallLog.call_sid == call_sid))
        if not existing_log:
            session.add(
                CallLog(
                    call_sid=call_sid,
                    from_number=from_number,
                    to_number=settings.twilio_phone,
                    status="in-progress",
                )
            )
            await session.commit()

    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.channel == "phone",
            Conversation.status.in_(["active", "escalated"]),
            Conversation.customer_contact == from_number,
        )
    )
    if not conversation:
        conversation = await build_conversation_service(session).create_conversation(
            ConversationCreate(channel="phone", customerName="Phone Caller", customerContact=from_number)
        )
        conversation_id = conversation.id
    else:
        conversation_id = conversation.id

    welcome_message = settings.welcome_message if settings and settings.welcome_message else "Hello! How can I help you today?"
    callback_url = f"{request.base_url}api/channels/phone/gather?conversationId={conversation_id}&callSid={call_sid}"
    return Response(content=_twiml_gather(welcome_message, callback_url), media_type="text/xml")


@router.post("/phone/gather")
async def phone_gather(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Response:
    params = await _read_form_values(request)
    settings = await session.scalar(select(Settings).where(Settings.id == "default"))
    auth_token = settings.twilio_token if settings and settings.twilio_token else ""
    if auth_token:
        signature = request.headers.get("x-twilio-signature", "")
        if not _validate_twilio_signature(auth_token, signature, str(request.url), params):
            return Response(content="Forbidden", status_code=403)

    speech_result = params.get("SpeechResult", "")
    conversation_id = request.query_params.get("conversationId", "")
    call_sid = request.query_params.get("callSid", "") or params.get("CallSid", "")
    if not speech_result.strip():
        return Response(content=_twiml_say("I didn't catch that. Could you please repeat?"), media_type="text/xml")

    chat_response = await chat_completion(
        ChatRequest(conversationId=conversation_id, message=speech_result, channel="phone", customerContact=params.get("From")),
        session,
    )
    if call_sid:
        call_log = await session.scalar(select(CallLog).where(CallLog.call_sid == call_sid))
        if call_log:
            call_log.status = "in-progress"
            await session.commit()
    return Response(content=_twiml_say(str(chat_response.get("response", ""))), media_type="text/xml")


@router.post("/phone/status")
async def phone_status(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    params = await _read_form_values(request)
    settings = await session.scalar(select(Settings).where(Settings.id == "default"))
    auth_token = settings.twilio_token if settings and settings.twilio_token else ""
    if auth_token:
        signature = request.headers.get("x-twilio-signature", "")
        if not _validate_twilio_signature(auth_token, signature, str(request.url), params):
            return {"ok": True}

    call_sid = params.get("CallSid", "")
    call_duration = int(params.get("CallDuration", "0") or "0")
    call_status = params.get("CallStatus", "")
    if call_sid and call_status in {"completed", "failed", "no-answer"}:
        call_log = await session.scalar(select(CallLog).where(CallLog.call_sid == call_sid))
        if call_log:
            call_log.status = "completed" if call_status == "completed" else call_status
            call_log.duration = call_duration
            await session.commit()
    return {"ok": True}
