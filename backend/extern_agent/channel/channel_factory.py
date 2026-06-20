"""
channel factory
"""
from extern_agent.common import const
from .channel import Channel


def create_channel(channel_type) -> Channel:
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    ch = Channel()
    if channel_type == "terminal":
        from extern_agent.channel.terminal.terminal_channel import TerminalChannel
        ch = TerminalChannel()
    elif channel_type == 'web':
        from extern_agent.channel.web.web_channel import WebChannel
        ch = WebChannel()
    elif channel_type == "wechatmp":
        from extern_agent.channel.wechatmp.wechatmp_channel import WechatMPChannel
        ch = WechatMPChannel(passive_reply=True)
    elif channel_type == "wechatmp_service":
        from extern_agent.channel.wechatmp.wechatmp_channel import WechatMPChannel
        ch = WechatMPChannel(passive_reply=False)
    elif channel_type == "wechatcom_app":
        from extern_agent.channel.wechatcom.wechatcomapp_channel import WechatComAppChannel
        ch = WechatComAppChannel()
    elif channel_type == const.WECHAT_KF:
        from extern_agent.channel.wechat_kf.wechat_kf_channel import WechatKfChannel
        ch = WechatKfChannel()
    elif channel_type == const.FEISHU:
        from extern_agent.channel.feishu.feishu_channel import FeiShuChanel
        ch = FeiShuChanel()
    elif channel_type == const.DINGTALK:
        from extern_agent.channel.dingtalk.dingtalk_channel import DingTalkChanel
        ch = DingTalkChanel()
    elif channel_type == const.WECOM_BOT:
        from extern_agent.channel.wecom_bot.wecom_bot_channel import WecomBotChannel
        ch = WecomBotChannel()
    elif channel_type == const.QQ:
        from extern_agent.channel.qq.qq_channel import QQChannel
        ch = QQChannel()
    elif channel_type == const.TELEGRAM:
        from extern_agent.channel.telegram.telegram_channel import TelegramChannel
        ch = TelegramChannel()
    elif channel_type == const.SLACK:
        from extern_agent.channel.slack.slack_channel import SlackChannel
        ch = SlackChannel()
    elif channel_type == const.DISCORD:
        from extern_agent.channel.discord.discord_channel import DiscordChannel
        ch = DiscordChannel()
    elif channel_type in (const.WEIXIN, "wx"):
        from extern_agent.channel.weixin.weixin_channel import WeixinChannel
        ch = WeixinChannel()
        channel_type = const.WEIXIN
    else:
        raise RuntimeError
    ch.channel_type = channel_type
    return ch
