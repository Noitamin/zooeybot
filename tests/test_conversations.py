import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
from test_websearch import chatbot, Context, Typing


class Channel:
    def __init__(self, channel_id=10):
        self.id = channel_id
        self.messages = []
        self.history_error = False
        self.fetch_message = AsyncMock()
        self.history_options = None

    def typing(self):
        return Typing()

    async def history(self, **kwargs):
        self.history_options = kwargs
        if self.history_error:
            raise discord.Forbidden(SimpleNamespace(status=403, reason='Forbidden'), 'No history')
        for message in self.messages[:kwargs['limit']]:
            yield message


def message(channel, message_id, text, author=1, bot=False, reference=None):
    return SimpleNamespace(
        id=message_id, channel=channel, content=text, clean_content=text,
        author=SimpleNamespace(id=author, display_name=f'User{author}', bot=bot),
        guild=SimpleNamespace(id=1), reference=reference, attachments=[], webhook_id=None,
        to_reference=lambda **kwargs: discord.MessageReference(message_id=message_id, channel_id=channel.id, **kwargs),
    )


class ConversationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.channel = Channel()
        self.ctx = Context()
        self.ctx.prefix = None
        self.ctx.channel = self.channel
        self.bot = SimpleNamespace(user=SimpleNamespace(id=99), get_context=AsyncMock(return_value=self.ctx))
        self.cog = chatbot.ChatBot(self.bot)

    async def test_mention_context_order_and_temporary_memory(self):
        self.channel.messages = [message(self.channel, 2, 'second'), message(self.channel, 1, 'first')]
        incoming = message(self.channel, 3, '<@99> thoughts?')
        with patch.object(chatbot, 'completion_ds', return_value='An answer') as complete:
            self.assertTrue(await self.cog.handle_conversation(incoming))
        request = complete.call_args.args[0]
        data = json.loads(request[-2]['content'].split('\n', 1)[1])
        self.assertEqual([item['text'] for item in data], ['first', 'second'])
        self.assertIn('thoughts?', request[-1]['content'])
        self.assertEqual(self.channel.history_options['limit'], 10)
        self.assertIs(self.channel.history_options['before'], incoming)
        memory = self.cog.messages[('guild', 1)]
        self.assertEqual(len(memory), 3)
        self.assertNotIn('Temporary channel background', str(memory))
        self.assertEqual(self.ctx.sent[0][1]['reference'].message_id, 3)

    async def test_reply_without_ping_includes_older_target(self):
        target = message(self.channel, 1, 'Which characters do you own?', author=99, bot=True)
        self.channel.fetch_message.return_value = target
        incoming = message(self.channel, 20, 'These three', reference=SimpleNamespace(channel_id=10, message_id=1, resolved=None))
        with patch.object(chatbot, 'completion_ds', return_value='An answer') as complete:
            self.assertTrue(await self.cog.handle_conversation(incoming))
        data = json.loads(complete.call_args.args[0][-2]['content'].split('\n', 1)[1])
        self.assertEqual(data[0]['text'], target.content)
        self.assertTrue(data[0]['reply_target'])

    async def test_ordinary_messages_bots_webhooks_and_commands_do_not_trigger(self):
        cases = [message(self.channel, 1, 'hello'), message(self.channel, 2, '<@99>', bot=True), message(self.channel, 3, '<@99>')]
        cases[-1].webhook_id = 100
        with patch.object(chatbot, 'completion_ds') as complete:
            for incoming in cases:
                self.assertFalse(await self.cog.handle_conversation(incoming))
            self.ctx.prefix = '&'
            self.assertFalse(await self.cog.handle_conversation(message(self.channel, 4, '&chat hi <@99>')))
            complete.assert_not_called()

    async def test_reply_to_someone_else_does_not_trigger(self):
        self.channel.fetch_message.return_value = message(self.channel, 1, 'hello', author=2)
        incoming = message(self.channel, 2, 'hi', reference=SimpleNamespace(channel_id=10, message_id=1, resolved=None))
        self.assertFalse(await self.cog.handle_conversation(incoming))

    async def test_missing_history_and_deleted_reference_fall_back_to_mention(self):
        self.channel.history_error = True
        self.channel.fetch_message.side_effect = discord.NotFound(SimpleNamespace(status=404, reason='Not Found'), 'Deleted')
        incoming = message(self.channel, 2, '<@!99> hello', reference=SimpleNamespace(channel_id=10, message_id=1, resolved=None))
        with patch.object(chatbot, 'completion_ds', return_value='Hello'):
            self.assertTrue(await self.cog.handle_conversation(incoming))
        self.assertEqual(self.ctx.sent[0][0], 'Hello')

    async def test_context_bounds_attachments_dedup_and_same_channel(self):
        target = message(self.channel, 1, 'attached', author=99, bot=True)
        target.attachments = [object()]
        self.channel.messages = [message(self.channel, i, 'x' * 3000) for i in range(14, 5, -1)] + [target]
        records = await self.cog.channel_context(message(self.channel, 20, '<@99>'), target)
        self.assertLessEqual(len(json.dumps(records, ensure_ascii=False)), chatbot.CHANNEL_CONTEXT_CHARS)
        self.assertEqual(sum(item['id'] == '1' for item in records), 1)
        self.assertIn('have not been viewed', records[0]['text'])
        self.assertTrue(all(len(item['text']) <= 1000 for item in records))
        self.channel.messages = [message(Channel(11), 30, 'private elsewhere')]
        self.assertEqual(await self.cog.channel_context(message(self.channel, 40, '<@99>'), None), [])

    async def test_cross_channel_reference_is_not_fetched(self):
        incoming = message(self.channel, 2, 'hi', reference=SimpleNamespace(channel_id=11, message_id=1, resolved=None))
        self.assertFalse(await self.cog.handle_conversation(incoming))
        self.channel.fetch_message.assert_not_called()

    async def test_clear_mention_is_conversation_not_memory_reset(self):
        self.cog.messages[('guild', 1)] = [{'role': 'system', 'content': 'persona'}, {'role': 'user', 'content': 'old'}]
        with patch.object(chatbot, 'completion_ds', return_value='answer'):
            await self.cog.respond(self.ctx, 'CLEAR', background=[])
        self.assertEqual(len(self.cog.messages[('guild', 1)]), 4)

    async def test_background_overlap_not_duplicated_in_model_request(self):
        self.cog.messages[('guild', 1)] = [{'role': 'system', 'content': 'persona'}, {'role': 'assistant', 'content': 'previous answer'}]
        background = [{'id': '1', 'author': 'Zooey', 'text': 'previous answer'}]
        with patch.object(chatbot, 'completion_ds', return_value='new answer') as complete:
            await self.cog.respond(self.ctx, 'question', background=background)
        self.assertEqual(str(complete.call_args.args[0]).count('previous answer'), 1)


if __name__ == '__main__':
    unittest.main()
