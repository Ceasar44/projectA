from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SettingsUpdate(BaseModel):
    business_name: str | None = Field(default=None, alias="businessName", max_length=500)
    business_desc: str | None = Field(default=None, alias="businessDesc", max_length=5000)
    welcome_message: str | None = Field(default=None, alias="welcomeMessage", max_length=2000)
    tone: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=20)
    ai_provider: str | None = Field(default=None, alias="aiProvider", max_length=50)
    ai_model: str | None = Field(default=None, alias="aiModel", max_length=100)
    ai_api_key: str | None = Field(default=None, alias="aiApiKey", max_length=500)
    max_tokens: int | None = Field(default=None, alias="maxTokens", ge=100, le=128000)
    temperature: float | None = Field(default=None, ge=0, le=2)
    smtp_host: str | None = Field(default=None, alias="smtpHost", max_length=500)
    smtp_port: int | None = Field(default=None, alias="smtpPort", ge=1, le=65535)
    smtp_user: str | None = Field(default=None, alias="smtpUser", max_length=300)
    smtp_pass: str | None = Field(default=None, alias="smtpPass", max_length=500)
    smtp_from: str | None = Field(default=None, alias="smtpFrom", max_length=300)
    imap_host: str | None = Field(default=None, alias="imapHost", max_length=500)
    imap_port: int | None = Field(default=None, alias="imapPort", ge=1, le=65535)
    imap_user: str | None = Field(default=None, alias="imapUser", max_length=300)
    imap_pass: str | None = Field(default=None, alias="imapPass", max_length=500)
    twilio_sid: str | None = Field(default=None, alias="twilioSid", max_length=200)
    twilio_token: str | None = Field(default=None, alias="twilioToken", max_length=200)
    twilio_phone: str | None = Field(default=None, alias="twilioPhone", max_length=50)
    eleven_labs_key: str | None = Field(default=None, alias="elevenLabsKey", max_length=200)
    eleven_labs_voice: str | None = Field(default=None, alias="elevenLabsVoice", max_length=200)
    whatsapp_mode: str | None = Field(default=None, alias="whatsappMode", max_length=50)
    whatsapp_api_key: str | None = Field(default=None, alias="whatsappApiKey", max_length=500)
    whatsapp_phone: str | None = Field(default=None, alias="whatsappPhone", max_length=50)
    telegram_bot_token: str | None = Field(default=None, alias="telegramBotToken", max_length=500)


class SettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    business_name: str = Field(alias="businessName")
    business_desc: str = Field(alias="businessDesc")
    welcome_message: str = Field(alias="welcomeMessage")
    tone: str
    language: str
    ai_provider: str = Field(alias="aiProvider")
    ai_model: str = Field(alias="aiModel")
    ai_api_key: str = Field(alias="aiApiKey")
    max_tokens: int = Field(alias="maxTokens")
    temperature: float
    smtp_host: str = Field(alias="smtpHost")
    smtp_port: int = Field(alias="smtpPort")
    smtp_user: str = Field(alias="smtpUser")
    smtp_pass: str = Field(alias="smtpPass")
    smtp_from: str = Field(alias="smtpFrom")
    imap_host: str = Field(alias="imapHost")
    imap_port: int = Field(alias="imapPort")
    imap_user: str = Field(alias="imapUser")
    imap_pass: str = Field(alias="imapPass")
    twilio_sid: str = Field(alias="twilioSid")
    twilio_token: str = Field(alias="twilioToken")
    twilio_phone: str = Field(alias="twilioPhone")
    eleven_labs_key: str = Field(alias="elevenLabsKey")
    eleven_labs_voice: str = Field(alias="elevenLabsVoice")
    whatsapp_mode: str = Field(alias="whatsappMode")
    whatsapp_api_key: str = Field(alias="whatsappApiKey")
    whatsapp_phone: str = Field(alias="whatsappPhone")
    telegram_bot_token: str = Field(alias="telegramBotToken")
    created_at: datetime
    updated_at: datetime
